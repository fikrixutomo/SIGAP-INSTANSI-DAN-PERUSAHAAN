import streamlit as st
import pandas as pd
import glob

# ---------------------------------------------------
# 1. KONFIGURASI HALAMAN & TAMPILAN
# ---------------------------------------------------
URL_LOGO_JR = "logo_jasa_raharja.png" 

st.set_page_config(
    page_title="Dashboard Analisa Data GASPOL", 
    page_icon="🚗", 
    layout="wide"
)

# ---------------------------------------------------
# 2. FUNGSI MEMBACA DATA DENGAN PINTAR (SMART LOAD)
# ---------------------------------------------------
@st.cache_data(ttl=600)
def load_and_combine_data():
    file_list = glob.glob("*.csv")
    # Saring file pendukung agar tidak ikut terbaca sebagai data utama
    file_list = [
        f for f in file_list 
        if "Kode Plat" not in f 
        and "Query result" not in f 
        and "filtered" not in f
    ]
    
    df_list = []
    if not file_list:
        return pd.DataFrame()
        
    for file in file_list:
        try:
            # sep=None dan engine='python' otomatis mendeteksi koma (,) atau titik koma (;)
            df_temp = pd.read_csv(file, sep=None, engine='python', on_bad_lines='skip')
            df_list.append(df_temp)
        except Exception as e:
            st.warning(f"⚠️ Gagal membaca file {file}: {e}")
            
    if df_list:
        df_combined = pd.concat(df_list, ignore_index=True)
        
        # Standarisasi penamaan kolom jika ada perbedaan format
        rename_dict = {}
        if 'samsat_asal_nama' in df_combined.columns and 'nama_samsat' not in df_combined.columns:
            rename_dict['samsat_asal_nama'] = 'nama_samsat'
        if 'status_nomor_hp_valid' in df_combined.columns and 'flag_nomor_hp_valid' not in df_combined.columns:
            rename_dict['status_nomor_hp_valid'] = 'flag_nomor_hp_valid'
            
        if rename_dict:
            df_combined = df_combined.rename(columns=rename_dict)
            
        return df_combined
    else:
        return pd.DataFrame()

df = load_and_combine_data()

# ---------------------------------------------------
# 3. HEADER & LOGO DASHBOARD
# ---------------------------------------------------
col1, col2 = st.columns([1, 8])
with col1:
    try:
        st.image(URL_LOGO_JR, width=80)
    except:
        st.markdown("<h1>🚗</h1>", unsafe_allow_html=True)
with col2:
    st.title("Dashboard Analisa Data Kendaraan GASPOL")

st.markdown("---")

# ---------------------------------------------------
# 4. PANEL FILTER SIDEBAR (LENGKAP)
# ---------------------------------------------------
if df.empty:
    st.error("⚠️ Data CSV tidak ditemukan atau gagal dibaca. Pastikan file CSV ada di dalam folder yang sama dengan app.py.")
else:
    st.sidebar.header("🔍 Filter Data")
    
    # 1. Filter Kantor Cabang / Wilayah (Lhokseumawe, Langsa, Meulaboh, Wilayah Aceh)
    if 'nama_cabang' in df.columns:
        cabang_unique = ["Semua Cabang / Wilayah"] + sorted([str(x) for x in df['nama_cabang'].dropna().unique()])
        selected_cabang = st.sidebar.selectbox("Pilih Kantor Cabang / Wilayah:", cabang_unique)
    else:
        selected_cabang = "Semua Cabang / Wilayah"

    # 2. Filter Unit Samsat (Dinamis berdasarkan Cabang yang dipilih)
    if 'nama_samsat' in df.columns:
        if selected_cabang != "Semua Cabang / Wilayah" and 'nama_cabang' in df.columns:
            df_sub = df[df['nama_cabang'] == selected_cabang]
            samsat_unique = sorted([str(x) for x in df_sub['nama_samsat'].dropna().unique()])
        else:
            samsat_unique = sorted([str(x) for x in df['nama_samsat'].dropna().unique()])
            
        all_samsat = ["Semua Samsat"] + samsat_unique
        selected_samsat = st.sidebar.selectbox("Pilih Unit Samsat:", all_samsat)
    else:
        selected_samsat = "Semua Samsat"

    # 3. Filter Masa Tunggakan
    if 'kelompok_selisih_hari_tunggakan' in df.columns:
        tunggakan_unique = ["Semua Kelompok"] + sorted([str(x) for x in df['kelompok_selisih_hari_tunggakan'].dropna().unique()])
        selected_tunggakan = st.sidebar.selectbox("Masa Tunggakan:", tunggakan_unique)
    else:
        selected_tunggakan = "Semua Kelompok"

    # 4. Filter Status HP Valid
    hp_col = 'flag_nomor_hp_valid' if 'flag_nomor_hp_valid' in df.columns else 'status_nomor_hp_valid' if 'status_nomor_hp_valid' in df.columns else None
    if hp_col:
        hp_unique = ["Semua Status HP"] + sorted([str(x) for x in df[hp_col].dropna().unique()])
        selected_hp = st.sidebar.selectbox("Status Nomor HP:", hp_unique)
    else:
        selected_hp = "Semua Status HP"

    # 5. Filter Status Pembayaran
    if 'status_bayar' in df.columns:
        bayar_unique = ["Semua Status Bayar"] + sorted([str(x) for x in df['status_bayar'].dropna().unique()])
        selected_bayar = st.sidebar.selectbox("Status Pembayaran:", bayar_unique)
    else:
        selected_bayar = "Semua Status Bayar"

    # 6. Filter Status Tindak Lanjut
    if 'status_tindak_lanjut' in df.columns:
        tl_unique = ["Semua Status TL"] + sorted([str(x) for x in df['status_tindak_lanjut'].dropna().unique()])
        selected_tl = st.sidebar.selectbox("Status Tindak Lanjut:", tl_unique)
    else:
        selected_tl = "Semua Status TL"

    # 7. Filter Jenis Pemilik
    if 'pemilik_jenis' in df.columns:
        pemilik_unique = ["Semua Jenis Pemilik"] + sorted([str(x) for x in df['pemilik_jenis'].dropna().unique()])
        selected_pemilik = st.sidebar.selectbox("Jenis Pemilik:", pemilik_unique)
    else:
        selected_pemilik = "Semua Jenis Pemilik"

    # 8. Pencarian Cepat Teks / No. Polisi
    cari_kata = st.sidebar.text_input("Cari No. Polisi / Nama Pemilik:")

    # ---------------------------------------------------
    # 5. TERAPKAN FILTER KE DATASET
    # ---------------------------------------------------
    df_filtered = df.copy()
    
    if selected_cabang != "Semua Cabang / Wilayah" and 'nama_cabang' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_cabang'] == selected_cabang]
    if selected_samsat != "Semua Samsat" and 'nama_samsat' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_samsat'] == selected_samsat]
    if selected_tunggakan != "Semua Kelompok" and 'kelompok_selisih_hari_tunggakan' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['kelompok_selisih_hari_tunggakan'] == selected_tunggakan]
    if selected_hp != "Semua Status HP" and hp_col:
        df_filtered = df_filtered[df_filtered[hp_col] == selected_hp]
    if selected_bayar != "Semua Status Bayar" and 'status_bayar' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_bayar'] == selected_bayar]
    if selected_tl != "Semua Status TL" and 'status_tindak_lanjut' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_tindak_lanjut'] == selected_tl]
    if selected_pemilik != "Semua Jenis Pemilik" and 'pemilik_jenis' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['pemilik_jenis'] == selected_pemilik]
    if cari_kata:
        cond_plat = df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) if 'no_polisi' in df_filtered.columns else False
        cond_nama = df_filtered['nama_pemilik_terakhir'].astype(str).str.contains(cari_kata, case=False, na=False) if 'nama_pemilik_terakhir' in df_filtered.columns else False
        df_filtered = df_filtered[cond_plat | cond_nama]

    # ---------------------------------------------------
    # 6. RINGKASAN METRIK (KPI) & ANALISIS
    # ---------------------------------------------------
    total_kendaraan = len(df_filtered)
    hp_valid = len(df_filtered[df_filtered[hp_col].astype(str).str.upper() == 'VALID']) if hp_col else 0
    persen_hp = (hp_valid / total_kendaraan * 100) if total_kendaraan > 0 else 0

    if 'status_bayar' in df_filtered.columns:
        total_lunas = len(df_filtered[df_filtered['status_bayar'].astype(str).str.upper().str.contains('LUNAS|SUDAH BAYAR', na=False)])
        total_belum_lunas = len(df_filtered[df_filtered['status_bayar'].astype(str).str.upper().str.contains('BELUM LUNAS|BELUM BAYAR', na=False)])
    else:
        total_lunas, total_belum_lunas = 0, 0

    st.subheader(f"📊 Ringkasan Indikator Utama ({selected_cabang})")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Kendaraan Terfilter", f"{total_kendaraan:,} Unit")
    c2.metric("Nomor HP Valid", f"{hp_valid:,} Unit")
    c3.metric("Rasio HP Valid", f"{persen_hp:.1f}%")
    c4.metric("Sudah Lunas", f"{total_lunas:,} Unit")

    st.markdown("---")

    # ---------------------------------------------------
    # 7. TABEL DETAIL DATA & DOWNLOAD
    # ---------------------------------------------------
    st.subheader("📋 Tabel Detail Kendaraan")
    st.info("💡 **Tips:** Klik judul kolom pada tabel untuk mengurutkan (sort) data secara instan.")
    
    kolom_tampilan = [c for c in [
        'no_polisi', 'nama_pemilik_terakhir', 'pemilik_jenis', 'nama_samsat', 'nama_cabang', 
        'kode_jenis_kendaraan_deskripsi', 'tgl_mati_yad', 'nomor_hp', 
        'kelompok_selisih_hari_tunggakan', 'status_nomor_hp_valid', 'flag_nomor_hp_valid',
        'status_tindak_lanjut', 'status_bayar', 'prioritas'
    ] if c in df_filtered.columns]
    
    st.dataframe(df_filtered[kolom_tampilan], use_container_width=True)
    
    # Tombol Unduh CSV
    csv_data = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Hasil Filter Data (.CSV)",
        data=csv_data,
        file_name="data_tunggakan_filtered.csv",
        mime="text/csv"
    )
