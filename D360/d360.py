import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import json
import os
import time
from datetime import datetime

BASE_URL = "https://d360.com"
OFFERS_URL = f"{BASE_URL}/ar/offers"
OUTPUT_FILE = "../data/d360.json"

def create_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def accept_cookies(driver):
    try:
        for btn in driver.find_elements(By.TAG_NAME, "button"):
            if any(k in btn.text for k in ["قبول", "Accept", "موافق", "OK"]):
                btn.click()
                time.sleep(1)
                break
    except:
        pass

def get_offers_list(driver):
    driver.get(OFFERS_URL)
    time.sleep(4)
    accept_cookies(driver)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    offers = []

    for item in soup.select("div.group a"):
        href = item.get("href", "")
        if not href or "offers/" not in href:
            continue

        link = BASE_URL + "/ar/" + href if not href.startswith("http") else href

        store_el = item.select_one("h3")
        store = store_el.get_text(strip=True) if store_el else ""
        if not store:
            continue

        img_el = item.select_one("img[alt]")
        img = ""
        if img_el and img_el.get("alt") != "calendar":
            img = img_el.get("src", "")

        expiry_el = item.select_one("span")
        expiry = expiry_el.get_text(strip=True) if expiry_el else ""

        offers.append({
            "store": store,
            "link":  link,
            "img":   img,
            "expiry": expiry,
        })

    print(f"  وجدنا {len(offers)} عرض في القائمة")
    return offers

def get_offer_details(driver, offer):
    """يسحب الخصم والوصف من صفحة التفاصيل"""
    try:
        driver.get(offer["link"])
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # ابحث عن الخصم في كل النصوص
        discount = ""
        description = ""
        full_text = soup.get_text(separator=" ")
        full_text = re.sub(r'\s+', ' ', full_text)

        m = re.search(r"(\d+)\s*[%٪]", full_text)
        if m:
            discount = m.group(0).replace("٪", "%")

        # الوصف — أول جملة مفيدة
        for tag in soup.find_all(["p", "div"]):
            t = tag.get_text(strip=True)
            if t and len(t) > 20 and tag.parent.name not in ["script","style"]:
                if any(k in t for k in ["خصم", "استرداد", "احصل", "%", "٪", "عرض"]):
                    description = t[:150] + ("..." if len(t) > 150 else "")
                    break

        # كود الترويج
        promo = ""
        m2 = re.search(r'"([A-Z0-9]{4,})"', full_text)
        if m2:
            promo = m2.group(1)

        return discount, description, promo
    except:
        return "", "", ""

def scrape_all():
    print("جاري تشغيل Chrome...")
    driver = create_driver()
    all_offers = []

    try:
        print("جاري سحب قائمة العروض...")
        offers_list = get_offers_list(driver)
        total = len(offers_list)

        for i, offer in enumerate(offers_list, 1):
            print(f"[{i}/{total}] {offer['store']}...")
            discount, description, promo = get_offer_details(driver, offer)

            all_offers.append({
                "store":       offer["store"],
                "discount":    discount,
                "category":    "عروض",
                "expiry":      offer["expiry"],
                "description": description,
                "img":         offer["img"],
                "link":        offer["link"],
                "promo":       promo,
                "_bank":       "d360",
                "_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

    finally:
        driver.quit()

    print(f"\nتم سحب {len(all_offers)} عرض")
    return all_offers

def save_json(offers):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)
    print(f"✅ تم الحفظ في {OUTPUT_FILE}")

if __name__ == "__main__":
    offers = scrape_all()
    save_json(offers)
