import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime

BASE_URL = "https://stcbank.com.sa"
OFFERS_URL = f"{BASE_URL}/web/guest/offers"
OUTPUT_FILE = "../data/stc.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.9",
}

def scrape_all():
    print("جاري سحب عروض STC Bank...")
    res = requests.get(OFFERS_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")

    offers = []
    seen = set()

    for item in soup.select("a.offers-lister__offer"):
        # الاسم
        store_el = item.select_one("h4.offer__title")
        store = store_el.get_text(strip=True) if store_el else ""
        if not store or store in seen:
            continue
        seen.add(store)

        # الصورة
        img_el = item.select_one("img.offer__image-element")
        img = ""
        if img_el:
            src = img_el.get("src", "")
            img = BASE_URL + src if src.startswith("/") else src

        # الوصف
        desc_el = item.select_one("p.offer__description")
        description = desc_el.get_text(strip=True) if desc_el else ""

        # الخصم من العنوان
        discount = ""
        m = re.search(r"(\d+)\s*[%٪]", store)
        if m:
            discount = m.group(0).replace("٪", "%")

        # تاريخ الانتهاء
        expiry_el = item.select_one("div.offer__expiry")
        expiry = ""
        if expiry_el:
            expiry = expiry_el.get_text(strip=True).replace("صالح الى", "").strip()

        # الرابط
        href = item.get("href", "")
        link = BASE_URL + href if href.startswith("/") else href

        offers.append({
            "store":       store,
            "discount":    discount,
            "category":    "عروض",
            "expiry":      expiry,
            "description": description[:150] + ("..." if len(description) > 150 else ""),
            "img":         img,
            "link":        link,
            "promo":       "",
            "_bank":       "stc",
            "_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    print(f"تم سحب {len(offers)} عرض")
    return offers

def save_json(offers):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)
    print(f"✅ تم الحفظ في {OUTPUT_FILE}")

if __name__ == "__main__":
    offers = scrape_all()
    save_json(offers)
