import pandas as pd
import streamlit as st
import io
import os
import glob
import pdfkit 
import re 
import plotly.express as px

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="Dashboard SIGAP Instansi", page_icon="📊", layout="wide")
st.title("📊 Dashboard Data SIGAP Instansi")
st.markdown("---")

# ==========================================
# 0. MEMUAT DATA OTOMATIS
# ==========================================
@st.cache_data
def load_data():
    target_file = 'detil_data_sigap_instansi_2026-08-27T09_03_07.260452959Z.csv'
    if os.path.exists(target_file):
        return pd.read_csv(target_file)
    csv_files = glob.glob('*.csv')
    if csv_files:
        return pd.read_csv(csv_files[0])
    return None

df = load_data()

if df is None:
    st.error("⚠️ File CSV tidak ditemukan! Pastikan file data Anda sudah di-upload.")
    st.stop()

# ==========================================
# 1. PERSIAPAN NAMA KOLOM
# ==========================================
df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')

def cari_kolom(kata_kunci_list):
    for col in df.columns:
        if any(kata in col for kata in kata_kunci_list):
            return col
    return None

col_jp = cari_kolom(['jenis_pemilik', 'pemilik_kendaraan'])
col_np = cari_kolom(['nama_pemilik', 'nama_instansi', 'pemilik'])
col_sk = cari_kolom(['status_kendaraan', 'status_kend', 'status', 'lunas'])
col_kunj = cari_kolom(['status_kunjungan', 'status_kunjung', 'kunjungan'])
col_gol = cari_kolom(['jenis_golongan', 'golongan', 'jenis'])

# Pencarian nama kolom plat nomor diperluas agar pasti terdeteksi
col_plat = cari_kolom(['plat', 'nopol', 'no_pol', 'polisi', 'tnkb', 'kendaraan'])

# ==========================================
# 2. FILTER 5 WILAYAH UTAMA (DI BELAKANG LAYAR)
# ==========================================
def tentukan_wilayah(plat):
    if pd.isna(plat):
        return None # Data kosong diabaikan
    
    plat_str = str(plat).upper().strip()
    match = re.search(r'\d+[-.\s]*([A-Z])', plat_str)
    
    if match:
        seri = match.group(1) 
        if seri == 'N': return 'Lhokseumawe'
        elif seri == 'Z': return 'Bireuen'
        elif seri in ['K', 'Q']: return 'Aceh Utara'
        elif seri == 'Y': return 'Bener Meriah'
        elif seri == 'G': return 'Aceh Tengah'
            
    return None # Jika selain 5 wilayah ini, abaikan

if col_plat:
    df['wilayah_kendaraan'] = df[col_plat].apply(tentukan_wilayah)
    # Filter dataset: Hanya simpan data yang termasuk 5 wilayah di atas
    df = df[df['wilayah_kendaraan'].notna()]
else:
    st.error("⚠️ Kolom Plat Nomor tidak dapat ditemukan di dalam file. Pastikan ada kata 'plat' atau 'nopol' di baris judul file Anda.")
    st.stop()

# ==========================================
# 3. KONFIGURASI SIDEBAR & FILTER
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/8636/8636208.png", width=100)
st.sidebar.header("🔍 Filter Data")

# Filter wilayah murni hanya menampilkan 5 wilayah yang Anda inginkan
filter_wilayah = st.sidebar.multiselect("📍 Wilayah (Sesuai Plat)", df['wilayah_kendaraan'].unique())
jenis_pemilik = st.sidebar.multiselect("🏢 Jenis Pemilik", df[col_jp].dropna().unique() if col_jp else [])
nama_pemilik = st.sidebar.multiselect("👤 Nama Pemilik", df[col_np].dropna().unique() if col_np else [])
status_kend = st.sidebar.multiselect("💰 Status Kendaraan", df[col_sk].dropna().unique() if col_sk else [])
status_kunjungan = st.sidebar.multiselect("🤝 Status Kunjungan", df[col_kunj].dropna().unique() if col_kunj else [])

df_filtered = df.copy()
if filter_wilayah: df_filtered = df_filtered[df_filtered['wilayah_kendaraan'].isin(filter_wilayah)]
if jenis_pemilik: df_filtered = df_filtered[df_filtered[col_jp].isin(jenis_pemilik)]
if nama_pemilik: df_filtered = df_filtered[df_filtered[col_np].isin(nama_pemilik)]
if status_kend: df_filtered = df_filtered[df_filtered[col_sk].isin(status_kend)]
if status_kunjungan: df_filtered = df_filtered[df_filtered[col_kunj].isin(status_kunjungan)]

# ==========================================
# 4. DASHBOARD UTAMA
# ==========================================
if df_filtered.empty:
    st.warning("📭 Tidak ada data yang sesuai.")
else:
    st.subheader("📈 Ringkasan Informasi Eksekutif")
    col1, col2, col3, col4 = st.columns(4)
    
    total_kendaraan = df_filtered.shape[0]
    total_lunas = df_filtered[df_filtered[col_sk].astype(str).str.contains('Lunas', case=False, na=False) & ~df_filtered[col_sk].astype(str).str.contains('Belum', case=False, na=False)].shape[0] if col_sk else 0
    total_belum_lunas = total_kendaraan - total_lunas
    total_wilayah_aktif = df_filtered['wilayah_kendaraan'].nunique()
    
    with col1: st.metric(label="Total Kendaraan", value=f"{total_kendaraan:,}".replace(',', '.'))
    with col2: st.metric(label="✅ Status Lunas", value=f"{total_lunas:,}".replace(',', '.'))
    with col3: st.metric(label="🚨 Belum Lunas", value=f"{total_belum_lunas:,}".replace(',', '.'))
    with col4: st.metric(label="📍 Jumlah Wilayah", value=total_wilayah_aktif)
        
    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("📊 Visualisasi Data")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        if col_sk:
            status_counts = df_filtered[col_sk].value_counts().reset_index()
            status_counts.columns = ['Status', 'Jumlah']
            fig_status = px.pie(status_counts, names='Status', values='Jumlah', hole=0.4, 
                                title='Persentase Status Kendaraan', color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_status, use_container_width=True)

    with chart_col2:
        wilayah_counts = df_filtered['wilayah_kendaraan'].value_counts().reset_index()
        wilayah_counts.columns = ['Wilayah', 'Jumlah']
        fig_wilayah = px.bar(wilayah_counts, x='Wilayah', y='Jumlah', 
                             title='Sebaran Kendaraan per Wilayah', text_auto=True, color='Wilayah',
                             color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_wilayah, use_container_width=True)

    st.markdown("---")
    st.subheader("📑 Matriks Golongan vs Jenis Pemilik")
    if col_gol and col_jp:
        try:
            matriks = pd.crosstab(df_filtered[col_gol], df_filtered[col_jp])
            st.dataframe(matriks.style.background_gradient(cmap='Blues'), use_container_width=True)
        except Exception as e:
            st.dataframe(pd.crosstab(df_filtered[col_gol], df_filtered[col_jp]), use_container_width=True)
    
    st.markdown("---")
    with st.expander("Klik di sini untuk melihat Tabel Data Selengkapnya"):
        st.dataframe(df_filtered.head(1000), use_container_width=True) 

    # ==========================================
    # 5. FUNGSI DOWNLOAD EXCEL & PDF
    # ==========================================
    st.write("### ⬇️ Unduh Laporan")
    dl_col1, dl_col2 = st.columns(2)
    
    def convert_df_to_excel(dataframe):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            dataframe.to_excel(writer, index=False, sheet_name='Data_Filter')
        return output.getvalue()
    
    with dl_col1:
        st.download_button(
            label="📥 Download Laporan Excel", data=convert_df_to_excel(df_filtered),
            file_name="Laporan_SIGAP_Instansi.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    def convert_df_to_pdf(dataframe):
        html = dataframe.to_html(index=False)
        return pdfkit.from_string(html, False)
    
    with dl_col2:
        try:
            pdf_data = convert_df_to_pdf(df_filtered.head(500))
            st.download_button(label="📄 Download Laporan PDF", data=pdf_data, file_name="Laporan_SIGAP_Instansi.pdf", mime="application/pdf")
        except:
            st.info("⚠️ Fitur PDF memerlukan server khusus ('wkhtmltopdf'). Silakan unduh format Excel.")
