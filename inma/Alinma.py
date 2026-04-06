import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
import json
import os

BASE_URL = "https://www.alinma.com"
OUTPUT_FILE = "../data/alinma.json"   # ← الملف الناتج

CATEGORY_PAGES = [
    "/ar/Media-Campaigns/Stores",
    "/ar/Media-Campaigns/Stores/Restaurants-and-Sweets",
    "/ar/Media-Campaigns/Stores/Fashion-and-beauty",
    "/ar/Media-Campaigns/Stores/Travel-and-Tour",
    "/ar/Media-Campaigns/Stores/E-commerce-websites",
    "/ar/Media-Campaigns/Stores/International-Offers",
    "/ar/Media-Campaigns/Stores/Jewelry-and-watches-and-perfumes",
    "/ar/Media-Campaigns/Stores/Cars-Accessories-and-Services",
    "/ar/Media-Campaigns/Stores/Health-and-Medical",
    "/ar/Media-Campaigns/Stores/Education-and-Training",
    "/ar/Media-Campaigns/Stores/alinma-Products-and-Services-Offers",
]

CATEGORY_MAP = {
    "Restaurants-and-Sweets":              "مطاعم وحلويات",
    "Fashion-and-beauty":                  "أزياء وجمال",
    "Health-and-Medical":                  "صحة وطب",
    "Travel-and-Tour":                     "سفر وسياحة",
    "E-commerce-websites":                 "تجارة إلكترونية",
    "International-Offers":                "عروض دولية",
    "Jewelry-and-watches-and-perfumes":    "مجوهرات وعطور",
    "Cars-Accessories-and-Services":       "سيارات وخدمات",
    "Education-and-Training":              "تعليم وتدريب",
    "alinma-Products-and-Services-Offers": "عروض الإنماء",
}

def get_category(path):
    for key, val in CATEGORY_MAP.items():
        if key in path: return val
    return "عروض"

def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def discover_offer_links(driver):
    print("\n🔍 جاري اكتشاف روابط العروض...")
    discovered = set()
    for cat_page in CATEGORY_PAGES:
        url = BASE_URL + cat_page
        try:
            driver.get(url)
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            before = len(discovered)
            for a in soup.find_all("a", href=True):
                href = a["href"].split("?")[0].rstrip("/")
                if "/ar/Media-Campaigns/Stores/" in href:
                    parts = [p for p in href.split("/") if p]
                    if len(parts) >= 5:
                        discovered.add(href)
            added = len(discovered) - before
            print(f"  ✅ {cat_page.split('/')[-1]}: +{added} رابط")
        except Exception as e:
            print(f"  ⚠️  خطأ في {cat_page}: {e}")

    links = sorted(discovered)
    print(f"\n  📋 إجمالي الروابط: {len(links)}\n")
    return links

def scrape_offer(driver, path):
    url = BASE_URL + path
    try:
        driver.get(url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        page_text = soup.get_text()
        if "الصفحة التي تبحث عنها غير موجودة" in page_text or "Page Not Found" in page_text:
            return None

        title = ""
        for sel in ["h1", "h2"]:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                title = el.get_text(strip=True)
                break

        description = ""
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if text and ("خصم" in text or "%" in text or len(text) > 30):
                description = text[:150] + ("..." if len(text) > 150 else "")
                break

        discount = ""
        m = re.search(r"(\d+)\s*%", description)
        if m: discount = m.group(0)

        img = ""
        for img_el in soup.find_all("img"):
            src = img_el.get("src", "")
            if src and ("ExtraImages" in src or ("media" in src.lower() and "logo" not in src.lower() and "svg" not in src.lower())):
                img = BASE_URL + src if src.startswith("/") else src
                break

        expiry = ""
        MONTHS_PAT = r"(\d{1,2})\s+(يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s+(\d{4})"
        for tag in soup.find_all(string=lambda t: t and ("حتى" in t or "ينتهي" in t or "يسري" in t)):
            t = str(tag).strip()
            # ابحث عن التاريخ بعد "حتى" أولاً
            after_hatta = re.search(r"حتى\s*" + MONTHS_PAT, t)
            if after_hatta:
                expiry = f"{after_hatta.group(1)} {after_hatta.group(2)} {after_hatta.group(3)}"
                break
            # ابحث عن تاريخ بالأرقام بعد "حتى"
            after_hatta_num = re.search(r"حتى\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", t)
            if after_hatta_num:
                expiry = f"{after_hatta_num.group(1)}/{after_hatta_num.group(2)}/{after_hatta_num.group(3)}"
                break
            # إذا ما في "حتى" خذ آخر تاريخ في النص
            all_dates = re.findall(MONTHS_PAT, t)
            if all_dates:
                last = all_dates[-1]
                expiry = f"{last[0]} {last[1]} {last[2]}"
                break
            # تاريخ بالأرقام
            all_num = re.findall(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", t)
            if all_num:
                last = all_num[-1]
                expiry = f"{last[0]}/{last[1]}/{last[2]}"
                break

        # الصيغة الموحدة
        return {
            "store":       title,
            "discount":    discount,
            "category":    get_category(path),
            "expiry":      expiry,
            "description": description,
            "img":         img,
            "link":        url,
            "promo":       "",
            "_bank":       "inma",
            "_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
    except Exception as e:
        print(f"  خطا: {e}")
        return None

def scrape_all():
    print("جاري تشغيل Chrome...")
    driver = create_driver()
    offers = []
    try:
        offer_links = discover_offer_links(driver)
        total = len(offer_links)
        for i, path in enumerate(offer_links, 1):
            name = path.split("/")[-1]
            print(f"[{i}/{total}] {name}...")
            offer = scrape_offer(driver, path)
            if offer and offer["store"]:
                offers.append(offer)
    finally:
        driver.quit()

    print(f"\nتم سحب {len(offers)} عرض")
    return offers

def save_json(offers):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)
    print(f"✅ تم الحفظ في {OUTPUT_FILE}")

if __name__ == "__main__":
    offers = scrape_all()
    save_json(offers)
