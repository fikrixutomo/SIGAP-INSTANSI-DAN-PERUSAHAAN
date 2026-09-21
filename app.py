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
st.set_page_config(page_title="Dashboard SIGAP Multi-Kategori", page_icon="📊", layout="wide")
st.title("📊 Dashboard Data SIGAP (Pemerintahan, Perusahaan, Perorangan)")
st.markdown("---")

# ==========================================
# 0. FUNGSI PEMROSESAN UTAMA (TER-CACHE UTUT MENCEGAH SLOWDOWN)
# ==========================================
@st.cache_data(show_spinner="Memproses data, mohon tunggu sebentar... ⏳")
def load_and_preprocess_data():
    csv_files = glob.glob('*.csv')
    if not csv_files:
        return None, [], None, None, None, None

    # Identifikasi file
    file_instansi = [f for f in csv_files if 'detil_data_sigap_instansi' in f.lower()]
    file_potensi = [f for f in csv_files if 'detil_potensi_sigap_prioritas' in f.lower()]
    
    file_instansi.sort(key=os.path.getmtime, reverse=True)
    file_potensi.sort(key=os.path.getmtime, reverse=True)
    
    df_list = []
    loaded_files = []
    
    # Load File Instansi & Perusahaan
    if file_instansi:
        df_i = pd.read_csv(file_instansi[0], low_memory=False)
        df_i['sumber_file'] = 'instansi'
        df_list.append(df_i)
        loaded_files.append(file_instansi[0])
        
    # Load File Kendaraan Pribadi
    if file_potensi:
        df_p = pd.read_csv(file_potensi[0], low_memory=False)
        df_p['sumber_file'] = 'potensi_prioritas'
        df_list.append(df_p)
        loaded_files.append(file_potensi[0])
        
    if not df_list:
        csv_files.sort(key=os.path.getmtime, reverse=True)
        df_any = pd.read_csv(csv_files[0], low_memory=False)
        df_any['sumber_file'] = 'unknown'
        df_list.append(df_any)
        loaded_files.append(csv_files[0])
        
    df = pd.concat(df_list, ignore_index=True)
    
    # PERSIAPAN KOLOM
    df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
    
    # ------------------------------------------
    # KONVERSI AUTOMATIS FORMAT TANGGAL KE DD-MM-YYYY
    # ------------------------------------------
    for col in df.columns:
        if any(k in col for k in ['tgl', 'tanggal', 'date', 'tempo', 'lahir']):
            try:
                parsed_dates = pd.to_datetime(df[col], errors='coerce')
                if parsed_dates.notna().sum() > 0:
                    df[col] = parsed_dates.dt.strftime('%d-%m-%Y')
            except Exception:
                pass

    # PERBAIKAN BUG: return None jika tidak ditemukan
    def cari_kolom(kata_kunci_list):
        for col in df.columns:
            if any(kata in col for kata in kata_kunci_list):
                return col
        return None

    col_np = cari_kolom(['nama_pemilik', 'nama_instansi', 'pemilik', 'nama', 'nm_pemilik'])
    col_jp = cari_kolom(['jenis_pemilik', 'pemilik_kendaraan', 'kategori_pemilik', 'jenis_pemilikan', 'kepemilikan'])
    col_sk = cari_kolom(['status_kendaraan', 'status_kend', 'status', 'lunas'])
    col_kunj = cari_kolom(['status_kunjungan', 'status_kunjung', 'kunjungan'])
    col_plat = cari_kolom(['plat', 'nopol', 'no_pol', 'polisi', 'tnkb', 'kendaraan'])

    # TENTUKAN WILAYAH
    def tentukan_wilayah(plat):
        if pd.isna(plat): return None
        match = re.search(r'\d+[-.\s]*([A-Z])', str(plat).upper().strip())
        if match:
            seri = match.group(1) 
            if seri == 'N': return 'Lhokseumawe'
            if seri == 'Z': return 'Bireuen'
            if seri in ['K', 'Q']: return 'Aceh Utara'
            if seri == 'Y': return 'Bener Meriah'
            if seri == 'G': return 'Aceh Tengah'
        return None

    if col_plat:
        df['wilayah_kendaraan'] = df[col_plat].apply(tentukan_wilayah)
        df = df[df['wilayah_kendaraan'].notna()]
        
    # KLASIFIKASI ENTITAS (Aturan Mutlak)
    def klasifikasi_entitas(row):
        sumber = str(row.get('sumber_file', ''))
        if sumber == 'potensi_prioritas':
            return 'Perorangan'
            
        if sumber == 'instansi':
            jp_val = str(row.get(col_jp, '')).upper() if col_jp else ""
            if any(k in jp_val for k in ['PERUSAHAAN', 'SWASTA', 'BADAN', 'YAYASAN', 'KOPERASI', 'PT', 'CV']):
                return 'Perusahaan'
            elif any(k in jp_val for k in ['PEMERINTAH', 'INSTANSI', 'BUMN', 'BUMD', 'NEGARA']):
                return 'Pemerintahan'
            else:
                np_val = str(row.get(col_np, '')).upper() if col_np else ""
                if any(k in np_val for k in ['PT', 'CV', 'YAYASAN', 'KOPERASI', 'SWASTA', 'BADAN USAHA']):
                    return 'Perusahaan'
                return 'Pemerintahan'
                
        return 'Perorangan'

    df['kategori_entitas'] = df.apply(klasifikasi_entitas, axis=1)
    
    return df, loaded_files, col_np, col_jp, col_sk, col_kunj

# Menjalankan pemrosesan
df, file_names, col_np, col_jp, col_sk, col_kunj = load_and_preprocess_data()

if df is None:
    st.error("⚠️ File CSV tidak ditemukan! Pastikan file data Anda berada di folder yang sama dengan script.")
    st.stop()

# ==========================================
# 1. KONFIGURASI SIDEBAR & FILTER
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/8636/8636208.png", width=100)
st.sidebar.header("🔍 Filter Data")

opsi_kategori = ['Pemerintahan', 'Perusahaan', 'Perorangan']
kategori_terpilih = st.sidebar.multiselect("🏷️ Kategori Pemilik", opsi_kategori, default=opsi_kategori)

filter_wilayah = st.sidebar.multiselect("📍 Wilayah (Sesuai Plat)", df['wilayah_kendaraan'].dropna().unique())
nama_pemilik = st.sidebar.multiselect("👤 Nama Pemilik", df[col_np].dropna().unique() if col_np else [])
status_kend = st.sidebar.multiselect("💰 Status Kendaraan", df[col_sk].dropna().unique() if col_sk else [])
status_kunjungan = st.sidebar.multiselect("🤝 Status Kunjungan", df[col_kunj].dropna().unique() if col_kunj else [])

df_filtered = df.copy()

if kategori_terpilih: df_filtered = df_filtered[df_filtered['kategori_entitas'].isin(kategori_terpilih)]
if filter_wilayah: df_filtered = df_filtered[df_filtered['wilayah_kendaraan'].isin(filter_wilayah)]
if nama_pemilik and col_np: df_filtered = df_filtered[df_filtered[col_np].isin(nama_pemilik)]
if status_kend and col_sk: df_filtered = df_filtered[df_filtered[col_sk].isin(status_kend)]
if status_kunjungan and col_kunj: df_filtered = df_filtered[df_filtered[col_kunj].isin(status_kunjungan)]

# ==========================================
# 2. DASHBOARD UTAMA
# ==========================================
st.info(f"📁 **Data berhasil dimuat dan digabung dari file berikut:**\n" + "\n".join([f"- `{f}`" for f in file_names]))

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
    with st.expander("Klik di sini untuk melihat Tabel Data Selengkapnya (Maks 1000 Baris Pertama)"):
        st.dataframe(df_filtered.head(1000), use_container_width=True) 

    st.write("### ⬇️ Unduh Laporan")
    dl_col1, dl_col2 = st.columns(2)
    def convert_df_to_excel(dataframe):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_to_download = dataframe.drop(columns=['sumber_file'], errors='ignore')
            df_to_download.to_excel(writer, index=False, sheet_name='Data_Filter')
        return output.getvalue()
    
    with dl_col1:
        st.download_button(label="📥 Download Laporan Excel", data=convert_df_to_excel(df_filtered), file_name="Laporan_SIGAP.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")