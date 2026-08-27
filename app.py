import streamlit as st
import pandas as pd
import io
import glob

# 1. Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="Dashboard Analisis Tunggakan Instansi",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Dashboard Analisis Tunggakan Instansi & Perusahaan")
st.markdown("Dashboard interaktif untuk monitoring kepatuhan pajak kendaraan instansi dan perusahaan.")

# 2. Fungsi Membaca File CSV Secara Otomatis & Aman
@st.cache_data(ttl=600)
def load_data():
    file_list = glob.glob("*.csv")
    df_list = []
    for file in file_list:
        try:
            df_temp = pd.read_csv(file, sep=";", on_bad_lines='skip', engine='python')
            if df_temp.shape[1] <= 1:
                df_temp = pd.read_csv(file, sep=",", on_bad_lines='skip', engine='python')
            df_list.append(df_temp)
        except Exception as e:
            st.warning(f"Gagal membaca file {file}: {e}")
            
    if df_list:
        df_combined = pd.concat(df_list, ignore_index=True)
        # Standarisasi nama kolom jika diperlukan
        if 'samsat_asal_nama' in df_combined.columns and 'nama_samsat' not in df_combined.columns:
            df_combined = df_combined.rename(columns={'samsat_asal_nama': 'nama_samsat'})
        if 'status_nomor_hp_valid' in df_combined.columns and 'flag_nomor_hp_valid' not in df_combined.columns:
            df_combined = df_combined.rename(columns={'status_nomor_hp_valid': 'flag_nomor_hp_valid'})
        return df_combined
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("⚠️ File CSV data instansi tidak ditemukan di dalam folder. Pastikan file tersimpan dengan benar.")
else:
    # Identifikasi kolom nama perusahaan/instansi
    col_perusahaan = 'nama_pemilik_terakhir' if 'nama_pemilik_terakhir' in df.columns else 'nama_instansi' if 'nama_instansi' in df.columns else None

    # 3. SIDEBAR - PANEL FILTER LENGKAP
    st.sidebar.header("🔍 Filter Analisis Data")
    
    # Filter 1: Kantor Cabang / Wilayah
    if 'nama_cabang' in df.columns:
        val_cabang = ["Semua Cabang"] + sorted([str(x) for x in df['nama_cabang'].dropna().unique()])
        selected_cabang = st.sidebar.selectbox("Pilih Kantor Cabang:", val_cabang)
    else:
        selected_cabang = "Semua Cabang"

    # Filter 2: Unit Samsat
    if 'nama_samsat' in df.columns:
        if selected_cabang != "Semua Cabang" and 'nama_cabang' in df.columns:
            sub_df = df[df['nama_cabang'] == selected_cabang]
            val_samsat = ["Semua Samsat"] + sorted([str(x) for x in sub_df['nama_samsat'].dropna().unique()])
        else:
            val_samsat = ["Semua Samsat"] + sorted([str(x) for x in df['nama_samsat'].dropna().unique()])
        selected_samsat = st.sidebar.selectbox("Pilih Unit Samsat:", val_samsat)
    else:
        selected_samsat = "Semua Samsat"

    # Filter 3: Nama Instansi / Perusahaan
    if col_perusahaan:
        val_perusahaan = ["Semua Instansi / Perusahaan"] + sorted([str(x) for x in df[col_perusahaan].dropna().unique()])
        selected_perusahaan = st.sidebar.selectbox("Nama Instansi / Perusahaan:", val_perusahaan)
    else:
        selected_perusahaan = "Semua Instansi / Perusahaan"

    # Filter 4: Status Pembayaran (Lunas / Belum Lunas)
    if 'status_bayar' in df.columns:
        val_status = ["Semua Status Bayar"] + sorted([str(x) for x in df['status_bayar'].dropna().unique()])
        selected_status = st.sidebar.selectbox("Status Pembayaran:", val_status)
    else:
        selected_status = "Semua Status Bayar"

    # Filter 5: Status Tindak Lanjut / Kunjungan
    if 'status_tindak_lanjut' in df.columns:
        val_tl = ["Semua Status Kunjungan"] + sorted([str(x) for x in df['status_tindak_lanjut'].dropna().unique()])
        selected_tl = st.sidebar.selectbox("Status Kunjungan / TL:", val_tl)
    else:
        selected_tl = "Semua Status Kunjungan"

    # Filter 6: Jenis Pemilik
    if 'pemilik_jenis' in df.columns:
        val_pemilik = ["Semua Jenis Pemilik"] + sorted([str(x) for x in df['pemilik_jenis'].dropna().unique()])
        selected_pemilik = st.sidebar.selectbox("Jenis Pemilik:", val_pemilik)
    else:
        selected_pemilik = "Semua Jenis Pemilik"

    # Pencarian Cepat Teks / No. Polisi
    cari_kata = st.sidebar.text_input("Cari Plat Nomor / Nama Pemilik:")

    # 4. TERAPKAN FILTER KE DATASET
    df_filtered = df.copy()
    
    if selected_cabang != "Semua Cabang" and 'nama_cabang' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_cabang'] == selected_cabang]
    if selected_samsat != "Semua Samsat" and 'nama_samsat' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_samsat'] == selected_samsat]
    if selected_perusahaan != "Semua Instansi / Perusahaan" and col_perusahaan:
        df_filtered = df_filtered[df_filtered[col_perusahaan].astype(str) == selected_perusahaan]
    if selected_status != "Semua Status Bayar" and 'status_bayar' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_bayar'].astype(str) == selected_status]
    if selected_tl != "Semua Status Kunjungan" and 'status_tindak_lanjut' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_tindak_lanjut'].astype(str) == selected_tl]
    if selected_pemilik != "Semua Jenis Pemilik" and 'pemilik_jenis' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['pemilik_jenis'].astype(str) == selected_pemilik]
    if cari_kata:
        cond_plat = df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) if 'no_polisi' in df_filtered.columns else False
        cond_nama = df_filtered[col_perusahaan].astype(str).str.contains(cari_kata, case=False, na=False) if col_perusahaan else False
        df_filtered = df_filtered[cond_plat | cond_nama]

    # 5. PERHITUNGAN MATRIKS (KPI CARDS)
    total_kendaraan = len(df_filtered)
    
    # Hitung HP Valid
    col_hp = 'flag_nomor_hp_valid' if 'flag_nomor_hp_valid' in df_filtered.columns else 'status_nomor_hp_valid' if 'status_nomor_hp_valid' in df_filtered.columns else None
    hp_valid = len(df_filtered[df_filtered[col_hp].astype(str).str.upper() == 'VALID']) if col_hp else 0
    persen_hp = (hp_valid / total_kendaraan * 100) if total_kendaraan > 0 else 0.0

    # Kalkulasi Lunas/Belum & Kunjungan
    if 'status_bayar' in df_filtered.columns and 'status_tindak_lanjut' in df_filtered.columns:
        s_bayar = df_filtered['status_bayar'].astype(str).str.strip().str.upper()
        s_tl = df_filtered['status_tindak_lanjut'].astype(str).str.strip().str.upper()

        cond_blm_lunas = s_bayar.str.contains('BELUM LUNAS|BELUM BAYAR|BLM BAYAR', na=False)
        cond_lunas = s_bayar.str.contains('LUNAS|SUDAH BAYAR|SDH BAYAR', na=False) & ~cond_blm_lunas
        cond_sdh_tl = s_tl.str.contains('SUDAH DITINDAKLANJUTI|SUDAH DIKUNJUNGI|SUDAH TL|SDH TL', na=False)
        cond_blm_tl = s_tl.str.contains('BELUM DITINDAKLANJUTI|BELUM DIKUNJUNGI|BELUM TL|BLM TL', na=False) & ~cond_sdh_tl

        jml_lunas = len(df_filtered[cond_lunas])
        jml_belum_lunas = len(df_filtered[cond_blm_lunas])
        jml_lunas_sdh_tl = len(df_filtered[cond_lunas & cond_sdh_tl])
        jml_lunas_blm_tl = len(df_filtered[cond_lunas & cond_blm_tl])
        jml_blm_lunas_sdh_tl = len(df_filtered[cond_blm_lunas & cond_sdh_tl])
        jml_blm_lunas_blm_tl = len(df_filtered[cond_blm_lunas & cond_blm_tl])
        
        total_sdh_tl = len(df_filtered[cond_sdh_tl])
        conversion_rate = (jml_lunas_sdh_tl / total_sdh_tl * 100) if total_sdh_tl > 0 else 0.0
    else:
        jml_lunas = jml_belum_lunas = jml_lunas_sdh_tl = jml_lunas_blm_tl = jml_blm_lunas_sdh_tl = jml_blm_lunas_blm_tl = 0
        conversion_rate = 0.0

    persen_lunas = (jml_lunas / total_kendaraan * 100) if total_kendaraan > 0 else 0.0
    persen_belum_lunas = (jml_belum_lunas / total_kendaraan * 100) if total_kendaraan > 0 else 0.0

    # 6. TAMPILAN MATRIKS UTAMA
    st.subheader(f"📊 Ringkasan Indikator ({selected_cabang})")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Kendaraan", f"{total_kendaraan:,} Unit")
    k2.metric("Nomor HP Valid", f"{hp_valid:,} Unit")
    k3.metric("Rasio HP Valid", f"{persen_hp:.1f}%")
    k4.metric("Efektivitas Kunjungan", f"{conversion_rate:.1f}%")

    st.markdown("---")
    st.subheader("Rincian Status Pembayaran & Tindak Lanjut")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Kendaraan Lunas", f"{jml_lunas:,} Unit", f"{persen_lunas:.1f}%")
    m2.metric("Belum Lunas (Tunggakan)", f"{jml_belum_lunas:,} Unit", f"{persen_belum_lunas:.1f}%", delta_color="inverse")
    m3.metric("Lunas Sudah Dikunjungi", f"{jml_lunas_sdh_tl:,} Unit")
    m4.metric("Lunas Belum Dikunjungi", f"{jml_lunas_blm_tl:,} Unit")
    m5.metric("Belum Lunas Sudah TL", f"{jml_blm_lunas_sdh_tl:,} Unit")

    if jml_blm_lunas_blm_tl > 0:
        st.warning(f"⚠️ **Peringatan Beban Kerja:** Terdapat **{jml_blm_lunas_blm_tl:,} Unit** kendaraan instansi yang belum lunas dan belum dikunjungi sama sekali.")

    st.markdown("---")

    # 7. TABEL DETAIL DATA
    st.subheader("📋 Tabel Detail Kendaraan Instansi")
    st.dataframe(df_filtered, use_container_width=True)

    # 8. FITUR DOWNLOAD KHUSUS EXCEL DAN CSV
    st.markdown("### 📥 Download Hasil Filter Data")
    st.info("Anda dapat mengunduh data terfilter di atas ke dalam format Excel (.xlsx) atau CSV (.csv) untuk keperluan pelaporan.")
    
    dl1, dl2 = st.columns(2)
    
    with dl1:
        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='Data_Instansi')
            
            st.download_button(
                label="📊 Download File Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name="Hasil_Filter_Instansi.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.warning("Pastikan pustaka 'openpyxl' terinstal di server untuk mengaktifkan tombol unduh Excel.")
            
    with dl2:
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download File CSV (.csv)",
            data=csv_data,
            file_name="Hasil_Filter_Instansi.csv",
            mime="text/csv"
        )
