import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime

BASE_URL = "https://www.emiratesnbd.com.sa"

CATEGORIES = {
    "furniture":              "أثاث",
    "dining":                 "مطاعم",
    "fashion":                "أزياء",
    "super-market":           "سوبرماركت",
    "cars-and-accessories":   "سيارات",
    "health-and-lifestyle":   "صحة ورياضة",
    "travel":                 "سفر",
    "electronics":            "إلكترونيات",
    "leisure-and-entertainment": "ترفيه",
}

OUTPUT_FILE = "../data/enbd.json"

def scrape_category(page, slug, cat_name):
    url = f"{BASE_URL}/ar/deals/{slug}"
    print(f"  {cat_name}...")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
    except:
        print(f"  ⚠️ timeout: {slug}")
        return []

    offers = []
    page_num = 1

    while True:
        soup = BeautifulSoup(page.content(), "html.parser")
        cards = soup.select("a.deal-card")
        new = 0

        for card in cards:
            store_el = card.select_one("h3")
            store = store_el.get_text(strip=True) if store_el else ""
            if not store:
                continue

            img_el = card.select_one("figure img")
            img = img_el.get("src", "") if img_el else ""

            desc_el = card.select_one("div.deal-card__description")
            description = desc_el.get_text(strip=True) if desc_el else ""

            discount = ""
            m = re.search(r"(\d+)\s*[%٪]", description)
            if m:
                discount = m.group(0).replace("٪", "%")

            expiry_el = card.select_one("li.blue")
            expiry = ""
            if expiry_el:
                expiry = expiry_el.get_text(strip=True).replace("تنتهي:", "").strip()

            href = card.get("href", "")
            link = BASE_URL + href if href.startswith("/") else href

            offers.append({
                "store":       store,
                "discount":    discount,
                "category":    cat_name,
                "expiry":      expiry,
                "description": description[:150] + ("..." if len(description) > 150 else ""),
                "img":         img,
                "link":        link,
                "promo":       "",
                "_bank":       "enbd",
                "_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
            new += 1

        print(f"    صفحة {page_num}: {new} عرض")

        # ابحث عن "تحميل المزيد"
        try:
            load_more = None
            for btn in page.locator("button, a").all():
                try:
                    text = btn.inner_text()
                    if "تحميل المزيد" in text and btn.is_visible():
                        load_more = btn
                        break
                except:
                    pass

            if load_more:
                load_more.click()
                page.wait_for_timeout(2000)
                page_num += 1
            else:
                break
        except:
            break

    return offers

def scrape_all():
    print("جاري سحب عروض ENBD...")
    all_offers = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for slug, cat_name in CATEGORIES.items():
            offers = scrape_category(page, slug, cat_name)
            for o in offers:
                key = f"{o['store']}_{o['category']}"
                if key not in seen:
                    seen.add(key)
                    all_offers.append(o)

        browser.close()

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
