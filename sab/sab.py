import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime

BASE_URL = "https://www.sab.com"
OFFERS_URL = f"{BASE_URL}/ar/personal/compare-credit-cards/credit-card-special-offers/all-offers/"
OUTPUT_FILE = "../data/sab.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.9",
}

def scrape_all():
    print("جاري سحب عروض بنك ساب...")
    res = requests.get(OFFERS_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")

    offers = []
    seen = set()

    for item in soup.select("div.sab-cardsListingTab-v3__mainContent"):
        # الاسم
        store_el = item.select_one("h2.sab-cardsListingTab-v3__cards-title")
        store = store_el.get_text(strip=True) if store_el else ""
        if not store or store in seen:
            continue
        seen.add(store)

        # الصورة
        img_el = item.select_one("img.sab-cardsListingTab-v3__cards-image")
        img = ""
        if img_el:
            src = img_el.get("src", "")
            img = BASE_URL + src if src.startswith("/") else src

        # الوصف والخصم
        desc_el = item.select_one("div.sab-cardsListingTab-v3__cards-desc")
        description = desc_el.get_text(strip=True) if desc_el else ""
        discount = ""
        m = re.search(r"(\d+)\s*[%٪]", description)
        if m:
            discount = m.group(0).replace("٪", "%")

        # تاريخ الانتهاء
        expiry_el = item.select_one("span.sab-cardsListingTab-v3__promotion-date")
        expiry = expiry_el.get_text(strip=True) if expiry_el else ""
        if not expiry:
            promo_text_el = item.select_one("span.sab-cardsListingTab-v3__promotion-text")
            if promo_text_el:
                m2 = re.search(r"إلى\s+(.+?)$", promo_text_el.get_text(strip=True))
                if m2:
                    expiry = m2.group(1).strip()

        # الكاتيجوري
        cat_el = item.select_one("button.sab-cardsListingTab-v3__category")
        category = cat_el.get_text(strip=True) if cat_el else item.get("data-category", "عروض")

        # الرابط
        link_el = item.select_one("a.cmp-minimalRed")
        link = ""
        if link_el:
            href = link_el.get("href", "")
            link = BASE_URL + href if href.startswith("/") else href

        offers.append({
            "store":       store,
            "discount":    discount,
            "category":    category,
            "expiry":      expiry,
            "description": description[:150] + ("..." if len(description) > 150 else ""),
            "img":         img,
            "link":        link or OFFERS_URL,
            "promo":       "",
            "_bank":       "sab",
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
