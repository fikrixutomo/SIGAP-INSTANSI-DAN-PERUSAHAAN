import pandas as pd
import streamlit as st
import io
import pdfkit # Pastikan wkhtmltopdf sudah terinstal di sistem Anda

@st.cache_data
def load_data():
    # Menggunakan file data sigap instansi sesuai referensi Anda
    return pd.read_csv('detil_data_sigap_instansi_2026-08-27T09_03_07.260452959Z.csv')

df = load_data()

st.title("Dashboard Data SIGAP Instansi")

# ==========================================
# 1. KONFIGURASI SIDEBAR & FILTER
# ==========================================
st.sidebar.header("Filter Dashboard")

# Mengambil nilai unik dari kolom
jenis_pemilik = st.sidebar.multiselect("Jenis Pemilik", df['jenis_pemilik'].dropna().unique())
nama_pemilik = st.sidebar.multiselect("Nama Pemilik", df['nama_pemilik'].dropna().unique())
status_kend = st.sidebar.multiselect("Status Kendaraan", ['Lunas', 'Belum Lunas'])
status_kunjungan = st.sidebar.multiselect("Status Kunjungan", df['status_kunjungan'].dropna().unique())

# Logika Filter
df_filtered = df.copy()
if jenis_pemilik:
    df_filtered = df_filtered[df_filtered['jenis_pemilik'].isin(jenis_pemilik)]
if nama_pemilik:
    df_filtered = df_filtered[df_filtered['nama_pemilik'].isin(nama_pemilik)]
if status_kend:
    df_filtered = df_filtered[df_filtered['status_kendaraan'].isin(status_kend)]
if status_kunjungan:
    df_filtered = df_filtered[df_filtered['status_kunjungan'].isin(status_kunjungan)]

# ==========================================
# 2. MENAMPILKAN MATRIKS DATA
# ==========================================
st.subheader("Matriks Ringkasan")
total_kendaraan = df_filtered.shape[0]
st.metric(label="Total Kendaraan (Terfilter)", value=total_kendaraan)

st.subheader("Matriks Golongan vs Jenis Pemilik")
if not df_filtered.empty:
    matriks = pd.crosstab(df_filtered['jenis_golongan'], df_filtered['jenis_pemilik'])
    st.dataframe(matriks, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Data Hasil Filter")
    st.dataframe(df_filtered, use_container_width=True)

    # ==========================================
    # 3. FUNGSI DOWNLOAD EXCEL & PDF
    # ==========================================
    st.write("### Unduh Data")
    
    col1, col2 = st.columns(2)
    
    # --- EXCEL DOWNLOAD ---
    def convert_df_to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Data_Filter')
        return output.getvalue()
    
    excel_data = convert_df_to_excel(df_filtered)
    
    with col1:
        st.download_button(
            label="📥 Download Excel",
            data=excel_data,
            file_name="Data_SIGAP_Instansi_Terfilter.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    # --- PDF DOWNLOAD ---
    def convert_df_to_pdf(df):
        # Ubah dataframe menjadi format HTML terlebih dahulu
        html = df.to_html(index=False)
        # Konversi HTML ke PDF
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
            st.error("Gagal memuat PDF. Pastikan 'wkhtmltopdf' sudah terinstal di sistem Anda.")

else:
    st.warning("Tidak ada data kendaraan yang sesuai dengan kombinasi filter tersebut.")
