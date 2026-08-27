pip install streamlit pandas plotly openpyxl
import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="Dashboard Instansi & Perusahaan",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Dashboard Analisis Tunggakan (Instansi & Perusahaan)")
st.markdown("Dashboard ini menampilkan data spesifik untuk perusahaan/instansi beserta status pembayarannya.")

# 2. Pemuatan Data File Spesifik
@st.cache_data(ttl=600)
def load_data(file_name):
    try:
        # Mencoba membaca dengan titik koma sebagai delimiter utama
        df_temp = pd.read_csv(file_name, sep=";", on_bad_lines='skip', engine='python')
        if df_temp.shape[1] <= 1:
            # Jika gagal (hanya 1 kolom terbaca), beralih ke koma
            df_temp = pd.read_csv(file_name, sep=",", on_bad_lines='skip', engine='python')
        return df_temp
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        return pd.DataFrame()

# Menggunakan file yang Anda sebutkan
file_path = "detil_data_sigap_instansi_2026-08-27T08_27_56.825562579Z.csv"
df = load_data(file_path)

if df.empty:
    st.error(f"⚠️ File {file_path} tidak ditemukan atau gagal dibaca. Pastikan file berada di folder yang sama dengan app.py.")
else:
    # --- Pengecekan Nama Kolom ---
    # Mencari kolom yang memuat nama Instansi/Perusahaan
    col_perusahaan = 'nama_pemilik_terakhir' if 'nama_pemilik_terakhir' in df.columns else 'nama_instansi' if 'nama_instansi' in df.columns else None
    
    # Mencari kolom status pembayaran
    col_status = 'status_bayar' if 'status_bayar' in df.columns else None

    # 3. Sidebar Filter Utama
    st.sidebar.header("🔍 Filter Data")

    # Filter Nama Perusahaan
    if col_perusahaan:
        val_perusahaan = df[col_perusahaan].dropna().unique()
        perusahaan_list = ["Semua Perusahaan"] + sorted([str(x) for x in val_perusahaan])
        selected_perusahaan = st.sidebar.selectbox("Pilih Nama Instansi / Perusahaan:", perusahaan_list)
    else:
        selected_perusahaan = "Semua Perusahaan"
        st.sidebar.warning("Kolom nama perusahaan tidak ditemukan.")

    # Filter Status Pembayaran
    if col_status:
        val_status = df[col_status].dropna().unique()
        status_list = ["Semua Status"] + sorted([str(x) for x in val_status])
        selected_status = st.sidebar.selectbox("Status Pembayaran (Lunas/Belum):", status_list)
    else:
        selected_status = "Semua Status"
        st.sidebar.warning("Kolom status pembayaran tidak ditemukan.")
        
    # Fitur Pencarian Cepat
    cari_kata = st.sidebar.text_input("Pencarian Bebas (Plat/Nama):")

    # 4. Terapkan Filter
    df_filtered = df.copy()
    
    if selected_perusahaan != "Semua Perusahaan" and col_perusahaan:
        df_filtered = df_filtered[df_filtered[col_perusahaan].astype(str) == selected_perusahaan]
        
    if selected_status != "Semua Status" and col_status:
        df_filtered = df_filtered[df_filtered[col_status].astype(str) == selected_status]
        
    if cari_kata:
        # Mencari di seluruh kolom teks jika memungkinkan
        cond_nama = df_filtered[col_perusahaan].astype(str).str.contains(cari_kata, case=False, na=False) if col_perusahaan else False
        cond_plat = df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) if 'no_polisi' in df_filtered.columns else False
        df_filtered = df_filtered[cond_plat | cond_nama]

    # 5. Menampilkan Metrik (KPI)
    st.subheader("📊 Ringkasan Data Instansi")
    total_data = len(df_filtered)
    
    if col_status:
        s_bayar = df_filtered[col_status].astype(str).str.strip().str.upper()
        jml_lunas = len(df_filtered[s_bayar.str.contains('LUNAS|SUDAH', na=False)])
        jml_belum_lunas = len(df_filtered[s_bayar.str.contains('BELUM LUNAS|BELUM', na=False)])
    else:
        jml_lunas = 0
        jml_belum_lunas = 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Kendaraan Filter", f"{total_data:,} Unit")
    c2.metric("Jumlah Lunas", f"{jml_lunas:,} Unit")
    c3.metric("Jumlah Belum Lunas", f"{jml_belum_lunas:,} Unit")

    st.markdown("---")

    # 6. Tabel Data Interaktif
    st.subheader("📋 Tabel Detail Kendaraan Instansi")
    st.dataframe(df_filtered, use_container_width=True)

    # 7. Fitur Download (Excel & CSV)
    st.markdown("### 📥 Download Hasil Filter")
    st.info("Anda dapat mengunduh data yang telah difilter ke dalam format Excel (.xlsx) atau CSV.")
    
    dl_col1, dl_col2 = st.columns(2)
    
    with dl_col1:
        # Generate Excel File in Memory
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='Data_Instansi')
        excel_data = buffer.getvalue()
        
        st.download_button(
            label="📊 Download File Excel (.xlsx)",
            data=excel_data,
            file_name="Hasil_Filter_Instansi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    with dl_col2:
        # Generate CSV Data
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download File CSV (.csv)",
            data=csv_data,
            file_name="Hasil_Filter_Instansi.csv",
            mime="text/csv"
        )
        
    # Catatan Ekspor PDF
    st.markdown("*💡 **Tips Cetak PDF:** Untuk menyimpan tabel ini sebagai PDF, Anda dapat menekan **Ctrl + P** (atau Cmd + P di Mac) pada browser Anda, lalu pilih **Save as PDF**.*")
