import streamlit as st
import pandas as pd
from wilayah import WILAYAH
from scraper import scrape_google_maps

# Konfigurasi halaman
st.set_page_config(page_title="Scraper Perusahaan DI Indonesia", layout="wide", page_icon="🏢")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    /* Background Utama Gradasi Biru */
    .stApp {
        background: linear-gradient(150deg, #1e3a8a 0%, #76B6DD 50%);
        color: white;
    }

    /* Top Bar (Garis atas seperti Footer) */
    .top-bar {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: rgba(0, 0, 0, 0.3);
        border-bottom: 2px solid #1e3a8a;
        z-index: 999;
        height: 5px;
    }

    /* Parameter Sidebar: Font Putih */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h2 {
        color: white !important;
    }

    /* Kontainer Hasil Scraping: Background Putih & Teks Hitam */
    .result-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        color: black !important;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* Memaksa teks di dalam tabel dan metrik hasil agar hitam */
    .result-container p, .result-container h3, .result-container span {
        color: black !important;
    }

    /* Footer Styling */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(0, 0, 0, 0.3);
        border-top: 1px solid rgba(255,255,255,0.1);
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        z-index: 999;
    }
    </style>
    
    <div class="top-bar"></div>
    """, unsafe_allow_html=True)

# --- JUDUL ---
st.title("🏢 Web Scraping Perusahaan Di Indonesia")
st.markdown("Aplikasi ini mengambil data nama, alamat, telepon, website, dan sosial media dari berbagai sumber.")

# --- SIDEBAR / PILIHAN WILAYAH ---
with st.sidebar:
    st.header("📍 Parameter Pencarian")
    provinsi = st.selectbox("Pilih Provinsi", list(WILAYAH.keys()))
    
    kab_kota = st.selectbox(
        "Pilih Kabupaten / Kota",
        WILAYAH[provinsi]
    )

    keyword = st.text_input(
        "Kata Kunci Usaha",
        value="Perusahaan Kontraktor"
    )
    
    st.divider()
    st.info("Tips: Gunakan kata kunci yang spesifik untuk hasil maksimal.")

# Gabungkan query
query = f"{keyword} {kab_kota} {provinsi}"

# --- TAMPILAN UTAMA ---
st.subheader(f"Hasil Pencarian: `{query}`")

if st.button("🚀 Mulai Scraping", use_container_width=True):
    with st.spinner(f"Sedang mencari data di {kab_kota}... Mohon tunggu."):
        try:
            hasil = scrape_google_maps(query)
            
            if hasil and len(hasil) > 0:
                df = pd.DataFrame(hasil)
                
                # Membungkus hasil dalam div putih agar teks berwarna hitam
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                col1.metric("Total Data Ditemukan", len(df))
                st.success("Scraping Berhasil!")

                # Menampilkan tabel (Otomatis menyesuaikan warna di dalam container)
                st.dataframe(df, use_container_width=True)

                # Tombol Download
                csv = df.to_csv(index=False, sep=';').encode("utf-8")
                st.download_button(
                    label="⬇️ Download Hasil (CSV)",
                    data=csv,
                    file_name=f"data_{kab_kota.replace(' ', '_')}.csv",
                    mime="text/csv",
                )
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ Tidak ada data yang ditemukan. Coba ganti kata kunci atau wilayah.")
        
        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {e}")

# --- FOOTER ---
st.markdown("""
    <div class="footer">
        <p>© 2025 Copyright by <b>Devynta Syabrina ITS</b> | All Rights Reserved</p>
    </div>
    """, unsafe_allow_html=True)