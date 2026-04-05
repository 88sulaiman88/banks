import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json
import os

BASE_URL = "https://www.riyadbank.com"
OFFERS_URL = f"{BASE_URL}/ar/personal-banking/credit-cards/offers"
OUTPUT_FILE = "../data/riyadh.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.9",
}

def scrape_all():
    print("جاري سحب عروض بنك الرياض...")
    res = requests.get(OFFERS_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")

    offers = []
    seen = set()

    for card in soup.select("div.rb-offers-card"):
        store_el = card.select_one("div.rb-brand-name")
        store = store_el.get_text(strip=True) if store_el else ""
        if not store or store in seen:
            continue
        seen.add(store)

        img_el = card.select_one("img.rb-brand-logo")
        img = img_el.get("src", "") if img_el else ""

        discount_el = card.select_one("span.discount-percent-text")
        discount_text = discount_el.get_text(strip=True) if discount_el else ""
        discount = ""
        m = re.search(r"(\d+)\s*[%٪]", discount_text)
        if m:
            discount = m.group(0).replace("٪", "%")

        expiry_el = card.select_one("div.discount-expiry")
        expiry = ""
        if expiry_el:
            expiry = expiry_el.get_text(strip=True).replace("صالحة حتى:", "").replace("صالحة حتى :", "").strip()

        link_el = card.select_one("a.rb-offer-link")
        link = ""
        if link_el:
            href = link_el.get("href", "")
            link = BASE_URL + href if href.startswith("/") else href

        offers.append({
            "store":       store,
            "discount":    discount,
            "category":    "عروض",
            "expiry":      expiry,
            "description": discount_text,
            "img":         img,
            "link":        link or OFFERS_URL,
            "promo":       "",
            "_bank":       "riyadh",
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
