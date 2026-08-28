import pandas as pd
import streamlit as st
import io
import os
import glob
import pdfkit 
import re # Tambahan pustaka untuk memproses teks plat nomor

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="Dashboard SIGAP Instansi", layout="wide")
st.title("Dashboard Data SIGAP Instansi")

# ==========================================
# 0. MEMUAT DATA OTOMATIS (ANTI-ERROR)
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
    st.error("⚠️ File CSV tidak ditemukan! Pastikan file data Anda sudah di-upload ke GitHub.")
    st.stop()

# ==========================================
# 1. DETEKSI KOLOM PINTAR
# ==========================================
# Menyeragamkan semua nama kolom agar mudah dicari
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
col_plat = cari_kolom(['plat', 'nopol', 'polisi', 'no_pol']) # Mencari kolom plat nomor

if not all([col_jp, col_np, col_sk, col_kunj, col_gol]):
    st.warning("⚠️ Beberapa kolom data tidak terdeteksi otomatis, harap periksa struktur file CSV Anda.")

# ==========================================
# 2. MENGOLAH DATA WILAYAH DARI PLAT NOMOR
# ==========================================
def tentukan_wilayah(plat):
    if pd.isna(plat):
        return 'Tidak Diketahui'
    
    plat_str = str(plat).upper().strip()
    
    # Logika Regex: Mencari angka berapapun jumlahnya (\d+), 
    # lalu mengabaikan spasi jika ada (\s*), 
    # dan menangkap SATU huruf pertama setelah angka tersebut ([A-Z]).
    match = re.search(r'\d+\s*([A-Z])', plat_str)
    
    if match:
        seri = match.group(1) # Mengambil huruf awalan seri
        if seri == 'N': return 'Lhokseumawe'
        elif seri == 'Z': return 'Bireuen'
        elif seri == 'Y': return 'Bener Meriah'
        elif seri in ['K', 'Q']: return 'Aceh Utara'
        elif seri == 'G': return 'Aceh Tengah'
        else: return 'Wilayah Lain (Seri ' + seri + ')'
    
    return 'Format Plat Tidak Dikenali'

# Terapkan fungsi ke dataframe untuk membuat kolom baru "Wilayah"
if col_plat:
    df['wilayah_kendaraan'] = df[col_plat].apply(tentukan_wilayah)
else:
    df['wilayah_kendaraan'] = 'Kolom Plat Tidak Ditemukan'
    st.warning("⚠️ Kolom Plat Nomor tidak ditemukan di data, filter wilayah tidak dapat diproses.")

# ==========================================
# 3. KONFIGURASI SIDEBAR & FILTER
# ==========================================
st.sidebar.header("Filter Dashboard")

# Tambahan Filter Wilayah di paling atas
filter_wilayah = st.sidebar.multiselect("📍 Wilayah (Dari Plat)", df['wilayah_kendaraan'].dropna().unique())

# Filter lainnya
jenis_pemilik = st.sidebar.multiselect("Jenis Pemilik", df[col_jp].dropna().unique())
nama_pemilik = st.sidebar.multiselect("Nama Pemilik", df[col_np].dropna().unique())
status_kend = st.sidebar.multiselect("Status Kendaraan", df[col_sk].dropna().unique())
status_kunjungan = st.sidebar.multiselect("Status Kunjungan", df[col_kunj].dropna().unique())

# Eksekusi Logika Filter
df_filtered = df.copy()
if filter_wilayah:
    df_filtered = df_filtered[df_filtered['wilayah_kendaraan'].isin(filter_wilayah)]
if jenis_pemilik:
    df_filtered = df_filtered[df_filtered[col_jp].isin(jenis_pemilik)]
if nama_pemilik:
    df_filtered = df_filtered[df_filtered[col_np].isin(nama_pemilik)]
if status_kend:
    df_filtered = df_filtered[df_filtered[col_sk].isin(status_kend)]
if status_kunjungan:
    df_filtered = df_filtered[df_filtered[col_kunj].isin(status_kunjungan)]

# ==========================================
# 4. MENAMPILKAN MATRIKS DATA
# ==========================================
st.subheader("Matriks Ringkasan")
total_kendaraan = df_filtered.shape[0]
st.metric(label="Total Kendaraan (Terfilter)", value=total_kendaraan)

st.subheader("Matriks Golongan vs Jenis Pemilik")
if not df_filtered.empty:
    try:
        matriks = pd.crosstab(df_filtered[col_gol], df_filtered[col_jp])
        st.dataframe(matriks, use_container_width=True)
    except Exception as e:
        st.error(f"Tabel matriks tidak dapat dimuat: {e}")
    
    st.markdown("---")
    st.subheader("Data Hasil Filter")
    # Menampilkan 100 data teratas agar browser tidak berat
    st.dataframe(df_filtered.head(1000), use_container_width=True) 

    # ==========================================
    # 5. FUNGSI DOWNLOAD EXCEL & PDF
    # ==========================================
    st.write("### Unduh Data (Full)")
    
    col1, col2 = st.columns(2)
    
    # --- EXCEL DOWNLOAD ---
    def convert_df_to_excel(dataframe):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            dataframe.to_excel(writer, index=False, sheet_name='Data_Filter')
        return output.getvalue()
    
    with col1:
        st.download_button(
            label="📥 Download Excel",
            data=convert_df_to_excel(df_filtered),
            file_name="Data_SIGAP_Instansi_Terfilter.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    # --- PDF DOWNLOAD ---
    def convert_df_to_pdf(dataframe):
        html = dataframe.to_html(index=False)
        pdf = pdfkit.from_string(html, False)
        return pdf
    
    with col2:
        try:
            pdf_data = convert_df_to_pdf(df_filtered)
            st.download_button(
                label="📄 Download PDF",
                data=pdf_data,
                file_name="Data_SIGAP_Instansi_Terfilter.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.info("⚠️ Fitur PDF di Cloud memerlukan pengaturan server khusus ('wkhtmltopdf'). Silakan gunakan unduh Excel.")

else:
    st.warning("Tidak ada data kendaraan yang sesuai dengan kombinasi filter tersebut.")
