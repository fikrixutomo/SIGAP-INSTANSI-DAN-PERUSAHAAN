import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Dashboard Instansi & Perusahaan", layout="wide")

@st.cache_data(ttl=600)
def load_data():
    file_path = "detil_data_sigap_instansi_2026-08-27T08_27_56.825562579Z.csv"
    try:
        # Deteksi pemisah secara otomatis
        df = pd.read_csv(file_path, sep=";", on_bad_lines='skip', engine='python')
        if df.shape[1] <= 1:
            df = pd.read_csv(file_path, sep=",", on_bad_lines='skip', engine='python')
        return df
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("⚠️ File CSV tidak ditemukan. Pastikan nama file dan lokasinya sesuai.")
else:
    # Identifikasi kolom target secara dinamis
    col_perusahaan = 'nama_pemilik_terakhir' if 'nama_pemilik_terakhir' in df.columns else 'nama_instansi' if 'nama_instansi' in df.columns else df.columns[0]
    col_status = 'status_bayar' if 'status_bayar' in df.columns else df.columns[-1]

    st.sidebar.header("🔍 Filter Data")
    
    # 1. Filter Nama Perusahaan
    val_perusahaan = df[col_perusahaan].dropna().unique()
    list_perusahaan = ["Semua Perusahaan"] + sorted([str(x) for x in val_perusahaan])
    selected_perusahaan = st.sidebar.selectbox("Nama Perusahaan / Instansi:", list_perusahaan)

    # 2. Filter Status Lunas / Belum Lunas
    val_status = df[col_status].dropna().unique()
    list_status = ["Semua Status"] + sorted([str(x) for x in val_status])
    selected_status = st.sidebar.selectbox("Status Pembayaran:", list_status)

    # Terapkan Filter
    df_filtered = df.copy()
    if selected_perusahaan != "Semua Perusahaan":
        df_filtered = df_filtered[df_filtered[col_perusahaan].astype(str) == selected_perusahaan]
    if selected_status != "Semua Status":
        df_filtered = df_filtered[df_filtered[col_status].astype(str) == selected_status]

    # Tampilan Dashboard
    st.title("🏢 Dashboard Analisis Tunggakan Instansi")
    st.metric("Total Kendaraan Terfilter", f"{len(df_filtered)} Unit")
    st.dataframe(df_filtered, use_container_width=True)

    # Fitur Download Excel & PDF
    st.write("**📥 Unduh Hasil Filter**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Konversi ke memori untuk Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='Data Instansi')
            
        st.download_button(
            label="📊 Download File Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name="Hasil_Filter_Instansi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    with col2:
        st.info("💡 **Tips Cetak PDF:** Untuk mengunduh tabel sebagai PDF, tekan tombol **Ctrl + P** (Windows) atau **Cmd + P** (Mac) pada browser Anda, lalu pilih opsi **Save as PDF**.")
