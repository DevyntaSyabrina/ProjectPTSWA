import time
import pandas as pd
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    options = Options()
    # PENTING: Wajib Headless di Streamlit Cloud
    options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Tambahkan path binary chromium untuk server Linux
    options.binary_location = "/usr/bin/chromium" 

    # Service akan otomatis mendownload driver yang cocok dengan versi Chrome di server
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_social_media_links(driver, company_name):
    social_data = {"LinkedIn": "N/A", "Instagram": "N/A"}
    try:
        driver.execute_script("window.open('https://www.google.com', '_blank');")
        driver.switch_to.window(driver.window_handles[1])
        
        search_query = f"{company_name} Jombang LinkedIn Instagram official"
        driver.get(f"https://www.google.com/search?q={search_query.replace(' ', '+')}")
        time.sleep(2) 
        
        links = driver.find_elements(By.CSS_SELECTOR, "div.yuRUbf a")
        for res in links:
            href = res.get_attribute("href")
            if not href: continue
            
            if "linkedin.com/company" in href and social_data["LinkedIn"] == "N/A":
                social_data["LinkedIn"] = href
            elif "instagram.com/" in href and social_data["Instagram"] == "N/A":
                if not any(x in href for x in ["/p/", "/reels/", "/explore/", "google.com"]):
                    social_data["Instagram"] = href
        
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    except:
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
    return social_data

def scrape_google_maps(query):
    driver = setup_driver()
    data = []
    
    try:
        # Gunakan link Maps yang benar
        driver.get(f"https://www.google.com/maps/search/{query.replace(' ', '+')}")
        wait = WebDriverWait(driver, 20)
        
        st.info("Mencari daftar perusahaan...")
        scrollable_div = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
        
        for i in range(3): # Dikurangi agar tidak timeout di Streamlit Cloud
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
            time.sleep(2)

        items = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        st.write(f"Ditemukan {len(items)} item. Mulai mengambil detail...")

        for index, item in enumerate(items[:10]): # Batasi 10 data dulu untuk testing
            try:
                link_maps = item.get_attribute("href")
                driver.execute_script("arguments[0].click();", item)
                time.sleep(3) 

                row = {
                    "Nama Perusahaan": "N/A",
                    "Alamat": "N/A",
                    "Link Maps": link_maps,
                    "Telepon": "N/A",
                    "Website": "N/A",
                    "LinkedIn": "N/A",
                    "Instagram": "N/A"
                }

                try:
                    row["Nama Perusahaan"] = driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf").text
                except: pass

                details = driver.find_elements(By.CLASS_NAME, "Io6YTe")
                for d in details:
                    text = d.text
                    if not text: continue
                    if any(key in text for key in ["Jl.", "Kec.", "Kab.", "Jombang"]):
                        row["Alamat"] = text
                    elif text.replace(" ", "").replace("-", "").isdigit() or text.startswith("+62"):
                        row["Telepon"] = text
                    elif "." in text and " " not in text and "maps" not in text:
                        row["Website"] = text

                if row["Nama Perusahaan"] != "N/A":
                    sosmed = get_social_media_links(driver, row["Nama Perusahaan"])
                    row.update(sosmed)

                data.append(row)
                st.write(f"✅ [{index+1}] {row['Nama Perusahaan']}")

            except Exception as e:
                continue

    finally:
        driver.quit()
    return data

# Antarmuka Streamlit
st.title("Google Maps Scraper Jombang")
keyword = st.text_input("Masukkan Kata Kunci", "Pabrik di Jombang")

if st.button("Mulai Scrape"):
    hasil = scrape_google_maps(keyword)
    if hasil:
        df = pd.DataFrame(hasil)
        st.dataframe(df)
        st.download_button("Download CSV", df.to_csv(index=False, sep=';'), "hasil_scrape.csv", "text/csv")
