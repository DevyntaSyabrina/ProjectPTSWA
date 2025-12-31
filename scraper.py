import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    options = Options()
    # Aktifkan headless jika ingin berjalan di background
    # options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_social_media_links(driver, company_name):
    """Mencari LinkedIn dan Instagram dengan membuka tab baru agar Maps tidak terganggu"""
    social_data = {"LinkedIn": "N/A", "Instagram": "N/A"}
    
    try:
        # Buka tab baru
        driver.execute_script("window.open('https://www.google.com', '_blank');")
        driver.switch_to.window(driver.window_handles[1])
        
        search_query = f"{company_name} Jombang LinkedIn Instagram official"
        driver.get(f"https://www.google.com/search?q={search_query.replace(' ', '+')}")
        time.sleep(2) # Tunggu loading Google Search
        
        links = driver.find_elements(By.CSS_SELECTOR, "div.yuRUbf a")
        for res in links:
            href = res.get_attribute("href")
            if not href: continue
            
            if "linkedin.com/company" in href and social_data["LinkedIn"] == "N/A":
                social_data["LinkedIn"] = href
            elif "instagram.com/" in href and social_data["Instagram"] == "N/A":
                if not any(x in href for x in ["/p/", "/reels/", "/explore/", "google.com"]):
                    social_data["Instagram"] = href
        
        # Tutup tab sosmed dan kembali ke tab Maps
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
        # Masuk ke Google Maps
        driver.get(f"https://www.google.com/maps/search/{query.replace(' ', '+')}")
        wait = WebDriverWait(driver, 20)
        
        print("Mencari daftar perusahaan...")
        # Tunggu hingga panel hasil muncul
        scrollable_div = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
        
        # Scroll lebih banyak untuk hasil maksimal
        for i in range(5):
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
            print(f"Scrolling ke-{i+1}...")
            time.sleep(2)

        items = driver.find_elements(By.CLASS_NAME, "hfpxzc")
        print(f"Ditemukan {len(items)} item. Mulai mengambil detail...")

        for index, item in enumerate(items[:20]): # Ambil 20 data pertama
            try:
                # Ambil link maps sebelum klik
                link_maps = item.get_attribute("href")
                
                # Klik elemen menggunakan JavaScript agar lebih stabil
                driver.execute_script("arguments[0].click();", item)
                time.sleep(3) # Tunggu panel detail terbuka sempurna

                row = {
                    "Nama Perusahaan": "N/A",
                    "Alamat": "N/A",
                    "Link Maps": link_maps,
                    "Telepon": "N/A",
                    "Website": "N/A",
                    "LinkedIn": "N/A",
                    "Instagram": "N/A"
                }

                # Ambil Nama
                try:
                    row["Nama Perusahaan"] = driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf").text
                except: pass

                # Ambil Detail dari class Io6YTe
                details = driver.find_elements(By.CLASS_NAME, "Io6YTe")
                for d in details:
                    text = d.text
                    if not text: continue
                    
                    if any(key in text for key in ["Jl.", "Kec.", "Kab.", "Jombang", "Jawa Timur"]):
                        row["Alamat"] = text
                    elif text.replace(" ", "").replace("-", "").isdigit() or text.startswith("+62") or text.startswith("(0"):
                        row["Telepon"] = text
                    elif "." in text and " " not in text and "maps" not in text:
                        row["Website"] = text

                # Cari Sosmed hanya jika nama perusahaan ditemukan
                if row["Nama Perusahaan"] != "N/A":
                    print(f"[{index+1}] Mencari sosmed untuk: {row['Nama Perusahaan']}")
                    sosmed = get_social_media_links(driver, row["Nama Perusahaan"])
                    row.update(sosmed)

                data.append(row)
                print(f"[{index+1}] Berhasil mengambil data.")

            except Exception as e:
                print(f"Error pada item ke-{index+1}: {e}")
                continue

    finally:
        driver.quit()
    return data

if __name__ == "__main__":
    keyword = "Pabrik di Jombang" 
    hasil = scrape_google_maps(keyword)
    
    if hasil:
        cols = ["Nama Perusahaan", "Alamat", "Link Maps", "Telepon", "Website", "LinkedIn", "Instagram"]
        df = pd.DataFrame(hasil, columns=cols)
        
        # Simpan ke CSV
        output_name = "Data_Scraping_Jombang_Lengkap.csv"
        df.to_csv(output_name, index=False, sep=';')
        
        print(f"\n--- HASIL AKHIR ({len(hasil)} Data) ---")
        print(df.to_markdown(index=False))
        print(f"\nSelesai! Data disimpan di: {output_name}")
