import pandas as pd
import streamlit as st
import io
import os
import glob
import pdfkit 

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
    # 1. Coba cari dengan nama spesifik terlebih dahulu
    target_file = 'detil_data_sigap_instansi_2026-08-27T09_03_07.260452959Z.csv'
    if os.path.exists(target_file):
        return pd.read_csv(target_file)
    
    # 2. Jika tidak ketemu, otomatis baca file CSV apapun yang ada di folder
    csv_files = glob.glob('*.csv')
    if csv_files:
        return pd.read_csv(csv_files[0])
    
    # 3. Jika tidak ada CSV sama sekali
    return None

df = load_data()

if df is None:
    st.error("⚠️ File CSV tidak ditemukan! Pastikan file data Anda sudah di-upload ke GitHub berbarengan dengan file app.py.")
    st.stop()

# ==========================================
# 1. DETEKSI KOLOM PINTAR (MENCEGAH KEYERROR)
# ==========================================
# Menyeragamkan semua nama kolom (huruf kecil, spasi jadi underscore)
df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')

# Fungsi mencari kolom
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

# Jika sistem gagal menebak kolom, tampilkan dropdown agar user bisa memilih (tanpa error)
if not all([col_jp, col_np, col_sk, col_kunj, col_gol]):
    st.warning("⚠️ Sistem tidak bisa mendeteksi nama beberapa kolom secara otomatis. Silakan pilih kolom yang tepat di bawah ini:")
    c1, c2, c3 = st.columns(3)
    with c1:
        col_jp = st.selectbox("Kolom Jenis Pemilik:", df.columns, index=0)
        col_np = st.selectbox("Kolom Nama Pemilik:", df.columns, index=0)
    with c2:
        col_sk = st.selectbox("Kolom Status Kendaraan:", df.columns, index=0)
        col_kunj = st.selectbox("Kolom Status Kunjungan:", df.columns, index=0)
    with c3:
        col_gol = st.selectbox("Kolom Golongan:", df.columns, index=0)
    st.markdown("---")

# ==========================================
# 2. KONFIGURASI SIDEBAR & FILTER
# ==========================================
st.sidebar.header("Filter Dashboard")

jenis_pemilik = st.sidebar.multiselect("Jenis Pemilik", df[col_jp].dropna().unique())
nama_pemilik = st.sidebar.multiselect("Nama Pemilik", df[col_np].dropna().unique())
status_kend = st.sidebar.multiselect("Status Kendaraan", df[col_sk].dropna().unique())
status_kunjungan = st.sidebar.multiselect("Status Kunjungan", df[col_kunj].dropna().unique())

# Logika Filter
df_filtered = df.copy()
if jenis_pemilik:
    df_filtered = df_filtered[df_filtered[col_jp].isin(jenis_pemilik)]
if nama_pemilik:
    df_filtered = df_filtered[df_filtered[col_np].isin(nama_pemilik)]
if status_kend:
    df_filtered = df_filtered[df_filtered[col_sk].isin(status_kend)]
if status_kunjungan:
    df_filtered = df_filtered[df_filtered[col_kunj].isin(status_kunjungan)]

# ==========================================
# 3. MENAMPILKAN MATRIKS DATA
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
    st.dataframe(df_filtered, use_container_width=True)

    # ==========================================
    # 4. FUNGSI DOWNLOAD EXCEL & PDF
    # ==========================================
    st.write("### Unduh Data")
    
    col1, col2 = st.columns(2)
    
    # --- EXCEL DOWNLOAD ---
    def convert_df_to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Data_Filter')
        return output.getvalue()
    
    with col1:
        st.download_button(
            label="📥 Download Excel",
            data=convert_df_to_excel(df_filtered),
            file_name="Data_SIGAP_Instansi_Terfilter.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    # --- PDF DOWNLOAD ---
    def convert_df_to_pdf(df):
        html = df.to_html(index=False)
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