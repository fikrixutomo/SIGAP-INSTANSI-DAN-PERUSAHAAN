import streamlit as st
import pandas as pd
import io

# 1. Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="Dashboard Tunggakan Instansi",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Dashboard Analisis Tunggakan Instansi & Perusahaan")
st.markdown("Gunakan panel di sebelah kiri untuk memfilter data instansi. Hasil filter dapat Anda unduh ke dalam format Excel atau PDF.")

# 2. Fungsi Membaca File Spesifik
@st.cache_data(ttl=600)
def load_data():
    # Menggunakan nama file yang Anda berikan secara verbatim
    file_path = "detil_data_sigap_instansi_2026-08-27T08_27_56.825562579Z.csv"
    try:
        # Coba deteksi pemisah titik koma (;)
        df = pd.read_csv(file_path, sep=";", on_bad_lines='skip', engine='python')
        # Jika gagal atau tergabung di 1 kolom, gunakan koma (,)
        if df.shape[1] <= 1:
            df = pd.read_csv(file_path, sep=",", on_bad_lines='skip', engine='python')
        return df
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("⚠️ File data tidak ditemukan atau gagal dibaca. Pastikan file CSV tersebut berada di folder yang sama dengan app.py.")
else:
    # Deteksi otomatis nama kolom (beradaptasi dengan berbagai format)
    col_perusahaan = 'nama_pemilik_terakhir' if 'nama_pemilik_terakhir' in df.columns else 'nama_instansi' if 'nama_instansi' in df.columns else df.columns[0]
    col_status = 'status_bayar' if 'status_bayar' in df.columns else df.columns[-1]

    # 3. Sidebar Filter Utama
    st.sidebar.header("🔍 Filter Data")
    
    # Filter 1: Nama Perusahaan / Instansi
    val_perusahaan = df[col_perusahaan].dropna().unique()
    list_perusahaan = ["Semua Perusahaan"] + sorted([str(x) for x in val_perusahaan])
    selected_perusahaan = st.sidebar.selectbox("Pilih Nama Instansi / Perusahaan:", list_perusahaan)

    # Filter 2: Status Lunas / Belum Lunas
    val_status = df[col_status].dropna().unique()
    list_status = ["Semua Status"] + sorted([str(x) for x in val_status])
    selected_status = st.sidebar.selectbox("Status Pembayaran:", list_status)

    # Pencarian Ekstra (Opsional)
    cari_kata = st.sidebar.text_input("Cari Teks / No. Polisi (Opsional):")

    # 4. Terapkan Filter
    df_filtered = df.copy()
    if selected_perusahaan != "Semua Perusahaan":
        df_filtered = df_filtered[df_filtered[col_perusahaan].astype(str) == selected_perusahaan]
    
    if selected_status != "Semua Status":
        df_filtered = df_filtered[df_filtered[col_status].astype(str) == selected_status]
        
    if cari_kata:
        # Pencarian ke seluruh kolom yang berisi teks perusahaan atau plat nomor
        cond_nama = df_filtered[col_perusahaan].astype(str).str.contains(cari_kata, case=False, na=False)
        cond_plat = df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) if 'no_polisi' in df.columns else False
        df_filtered = df_filtered[cond_nama | cond_plat]

    # 5. Menampilkan Metrik Ringkasan
    st.subheader("📊 Ringkasan Data Instansi")
    total_data = len(df_filtered)
    st.metric("Total Kendaraan (Hasil Filter)", f"{total_data:,} Unit")

    st.markdown("---")

    # 6. Menampilkan Tabel Data Interaktif
    st.subheader("📋 Tabel Detail Kendaraan Instansi")
    st.dataframe(df_filtered, use_container_width=True)

    # 7. Fitur Download (Excel, CSV, dan Panduan PDF)
    st.markdown("### 📥 Download Hasil Filter")
    st.info("Pilih format unduhan di bawah ini berdasarkan tabel data yang sudah difilter.")
    
    dl_col1, dl_col2 = st.columns(2)
    
    with dl_col1:
        # Ekspor ke Excel (Menggunakan openpyxl)
        try:
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
        except Exception as e:
            st.warning("Pustaka 'openpyxl' belum terinstal. Jalankan `pip install openpyxl` di Terminal untuk mengaktifkan fitur unduh Excel.")
            
    with dl_col2:
        # Alternatif Stabil: Unduh ke CSV
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download File Data (.csv)",
            data=csv_data,
            file_name="Hasil_Filter_Instansi.csv",
            mime="text/csv"
        )
        
    # Panduan Unduh ke PDF
    st.markdown("---")
    st.markdown("#### 🖨️ Cara Download/Ekspor ke PDF")
    st.markdown("""
    Untuk menyimpan tabel hasil filter ini ke dalam format PDF dengan rapi, Anda dapat memanfaatkan fitur bawaan *Browser* yang Anda gunakan:
    1. Pastikan Anda sudah memfilter data yang ingin Anda ambil.
    2. Tekan kombinasi tombol **Ctrl + P** (Windows) atau **Cmd + P** (Mac) pada keyboard Anda.
    3. Pada menu pilihan *Printer* (Pencetak), ubah menjadi **Save as PDF** (Simpan sebagai PDF).
    4. Pada pengaturan *Layout* (Tata Letak), ubah menjadi **Landscape** (Mendatar) agar seluruh kolom tabel muat dan tidak terpotong.
    5. Klik tombol **Save** (Simpan).
    """)
