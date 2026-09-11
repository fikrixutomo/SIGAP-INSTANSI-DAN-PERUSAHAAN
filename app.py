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
st.set_page_config(page_title="Dashboard SIGAP Instansi & Perorangan", page_icon="📊", layout="wide")
st.title("📊 Dashboard Data SIGAP Multi-Kategori")
st.markdown("---")

# ==========================================
# 0. MEMUAT DATA OTOMATIS
# ==========================================
@st.cache_data
def load_data():
    csv_files = glob.glob('*.csv')
    if not csv_files:
        return None
    
    # Prioritaskan membaca file 'detil_data' dan ambil yang terbaru
    csv_files.sort(key=os.path.getmtime, reverse=True)
    target_file = None
    for f in csv_files:
        if 'detil_data' in f.lower():
            target_file = f
            break
            
    if not target_file:
        target_file = csv_files[0]
        
    return pd.read_csv(target_file, low_memory=False)

df = load_data()

if df is None:
    st.error("⚠️ File CSV tidak ditemukan! Pastikan file data Anda berada di folder yang sama dengan script.")
    st.stop()

# ==========================================
# 1. PERSIAPAN NAMA KOLOM
# ==========================================
# Simpan nama kolom asli untuk keperluan debug nanti
kolom_asli = df.columns.tolist()

df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')

def cari_kolom(kata_kunci_list):
    for col in df.columns:
        if any(kata in col for kata in kata_kunci_list):
            return col
    return None

col_np = cari_kolom(['nama_pemilik', 'nama_instansi', 'pemilik', 'nama', 'nm_pemilik'])
col_jp = cari_kolom(['jenis_pemilik', 'pemilik_kendaraan', 'kategori_pemilik', 'jenis_pemilikan', 'kepemilikan'])
col_sk = cari_kolom(['status_kendaraan', 'status_kend', 'status', 'lunas'])
col_kunj = cari_kolom(['status_kunjungan', 'status_kunjung', 'kunjungan'])
col_gol = cari_kolom(['jenis_golongan', 'golongan', 'jenis'])
col_plat = cari_kolom(['plat', 'nopol', 'no_pol', 'polisi', 'tnkb', 'kendaraan'])

# ==========================================
# 2. PENGELOMPOKAN WILAYAH & KATEGORI PEMILIK
# ==========================================
def tentukan_wilayah(plat):
    if pd.isna(plat): return None
    plat_str = str(plat).upper().strip()
    match = re.search(r'\d+[-.\s]*([A-Z])', plat_str)
    
    if match:
        seri = match.group(1) 
        if seri == 'N': return 'Lhokseumawe'
        elif seri == 'Z': return 'Bireuen'
        elif seri in ['K', 'Q']: return 'Aceh Utara'
        elif seri == 'Y': return 'Bener Meriah'
        elif seri == 'G': return 'Aceh Tengah'
    return None

if col_plat:
    df['wilayah_kendaraan'] = df[col_plat].apply(tentukan_wilayah)
    df = df[df['wilayah_kendaraan'].notna()]

def klasifikasi_entitas(row):
    teks = ""
    # Pindai dari nama pemilik
    if col_np and pd.notna(row.get(col_np)):
        teks += str(row[col_np]).upper() + " "
    # Pindai dari jenis pemilik juga
    if col_jp and pd.notna(row.get(col_jp)):
        teks += str(row[col_jp]).upper() + " "
        
    if not teks.strip():
        return 'Perorangan'
        
    # KATA KUNCI INSTANSI (Sangat Lengkap)
    kw_instansi = [
        'DINAS ', 'PEMERINTAH', 'KABUPATEN', 'PROVINSI', 'KOTA ', 'PEMKAB', 'PEMKOT', 'PEMPROV',
        'GAMPONG', 'DESA ', 'KECAMATAN', 'KEMENTERIAN', 'BAPPEDA', 'INSPEKTORAT', 'SEKRETARIAT',
        'BADAN', 'KANTOR', 'POLRI', 'POLRES', 'POLDA', 'TNI', 'KODIM', 'KORAMIL', 'PUSKESMAS',
        'RSUD', 'RSU', 'BUMN', 'BUMD', 'NEGARA', 'BKKBN', 'KEJAKSAAN', 'PENGADILAN'
    ]
    
    # KATA KUNCI PERUSAHAAN (Sangat Lengkap)
    kw_perusahaan = [
        'PT ', 'PT.', ' PT', 'CV ', 'CV.', ' CV', 'YAYASAN', 'KOPERASI', 'BANK ', 'BPR ', 
        'FIRMA', 'SWASTA', 'CORP', 'PDAM', 'LKM', 'LEMBAGA', 'UD ', 'UD.', ' UD'
    ]
    
    if "BADAN USAHA" in teks: return 'Perusahaan'
        
    for k in kw_instansi:
        if k in teks: return 'Instansi'
            
    for k in kw_perusahaan:
        if k in teks: return 'Perusahaan'
            
    return 'Perorangan'

# Terapkan Klasifikasi Baru
df['kategori_entitas'] = df.apply(klasifikasi_entitas, axis=1)

# ==========================================
# 3. KONFIGURASI SIDEBAR & FILTER
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/8636/8636208.png", width=100)
st.sidebar.header("🔍 Filter Data")

opsi_kategori = ['Instansi', 'Perusahaan', 'Perorangan']
kategori_terpilih = st.sidebar.multiselect("🏷️ Kategori Pemilik", opsi_kategori, default=opsi_kategori)

filter_wilayah = st.sidebar.multiselect("📍 Wilayah (Sesuai Plat)", df['wilayah_kendaraan'].dropna().unique())
jenis_pemilik = st.sidebar.multiselect("🏢 Detail Jenis Pemilik", df[col_jp].dropna().unique() if col_jp else [])
nama_pemilik = st.sidebar.multiselect("👤 Nama Pemilik", df[col_np].dropna().unique() if col_np else [])
status_kend = st.sidebar.multiselect("💰 Status Kendaraan", df[col_sk].dropna().unique() if col_sk else [])
status_kunjungan = st.sidebar.multiselect("🤝 Status Kunjungan", df[col_kunj].dropna().unique() if col_kunj else [])

df_filtered = df.copy()

if kategori_terpilih: df_filtered = df_filtered[df_filtered['kategori_entitas'].isin(kategori_terpilih)]
if filter_wilayah: df_filtered = df_filtered[df_filtered['wilayah_kendaraan'].isin(filter_wilayah)]
if jenis_pemilik and col_jp: df_filtered = df_filtered[df_filtered[col_jp].isin(jenis_pemilik)]
if nama_pemilik and col_np: df_filtered = df_filtered[df_filtered[col_np].isin(nama_pemilik)]
if status_kend and col_sk: df_filtered = df_filtered[df_filtered[col_sk].isin(status_kend)]
if status_kunjungan and col_kunj: df_filtered = df_filtered[df_filtered[col_kunj].isin(status_kunjungan)]

# ==========================================
# 4. DASHBOARD UTAMA
# ==========================================
if df_filtered.empty:
    st.warning("📭 Tidak ada data yang sesuai dengan filter saat ini.")
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
    with st.expander("Klik di sini untuk melihat Tabel Data Selengkapnya"):
        st.dataframe(df_filtered.head(1000), use_container_width=True) 

    st.write("### ⬇️ Unduh Laporan")
    dl_col1, dl_col2 = st.columns(2)
    def convert_df_to_excel(dataframe):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            dataframe.to_excel(writer, index=False, sheet_name='Data_Filter')
        return output.getvalue()
    
    with dl_col1:
        st.download_button(label="📥 Download Laporan Excel", data=convert_df_to_excel(df_filtered), file_name="Laporan_SIGAP.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ==========================================
# 5. MODE DEBUG (PEMERIKSAAN DATA)
# ==========================================
st.markdown("---")
with st.expander("🛠️ Mode Debug (Buka Jika Data Masih Kosong)"):
    st.write("Bagian ini membantu menganalisis mengapa data Instansi/Perusahaan tidak terbaca.")
    st.write(f"- **Kolom Nama Pemilik Terdeteksi:** `{col_np}`")
    st.write(f"- **Kolom Jenis Pemilik Terdeteksi:** `{col_jp}`")
    
    # Menampilkan ringkasan klasifikasi
    st.write("**Hasil Pembagian Kategori Saat Ini:**")
    st.dataframe(df['kategori_entitas'].value_counts().reset_index())
    
    # Menampilkan sampel data mentah untuk nama pemilik
    st.write("**Sampel 50 Nama Pemilik Asli di File Anda:**")
    if col_np:
        st.dataframe(df[[col_np, 'kategori_entitas']].drop_duplicates().head(50))
