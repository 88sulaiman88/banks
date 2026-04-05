import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime

BASE_URL = "https://www.alahli.com"
URLS = [
    f"{BASE_URL}/ar/pages/personal-banking/credit-cards/credit-card-promotions/snb-dalilak/",
    f"{BASE_URL}/ar/pages/personal-banking/credit-cards/credit-card-promotions/views",
]
OUTPUT_FILE = "../data/ahli.json"

def parse_items(soup, url):
    offers = []
    for item in soup.select("div.singleItem-wrap"):
        # الاسم
        store_el = item.select_one("div.item_title")
        store = store_el.get_text(strip=True) if store_el else ""
        if not store:
            continue

        # الصورة
        img_el = item.select_one("div.image img")
        img = img_el.get("src", "") if img_el else ""

        # الوصف والخصم
        desc_el = item.select_one("div.ico-text")
        description = desc_el.get_text(strip=True) if desc_el else ""
        discount = ""
        m = re.search(r"(\d+)\s*[%٪]", description)
        if m:
            discount = m.group(0).replace("٪", "%")

        # تاريخ الانتهاء
        expiry_el = item.select_one("div.type-text")
        expiry = ""
        if expiry_el:
            expiry_text = expiry_el.get_text(strip=True)
            m2 = re.search(r"حتى\s+(.+?)م?$", expiry_text)
            if m2:
                expiry = m2.group(1).strip()

        # الكاتيجوري
        cat_el = item.select_one("div.global-category-tag")
        category = cat_el.get_text(strip=True) if cat_el else "عروض"

        # الرابط
        link_el = item.select_one("a")
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
            "link":        link or url,
            "promo":       "",
            "_bank":       "ahli",
            "_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    return offers

def scrape_page(page, url):
    print(f"  جاري سحب: {url.split('/')[-2]}...")
    page.goto(url, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)

    all_offers = []
    page_num = 1

    while True:
        soup = BeautifulSoup(page.content(), "html.parser")
        offers = parse_items(soup, url)
        all_offers.extend(offers)
        print(f"    صفحة {page_num}: {len(offers)} عرض")

        # ابحث عن زر التالي
        try:
            next_btn = None
            for btn in page.locator("button, a").all():
                try:
                    text = btn.inner_text()
                    if "التالي" in text and btn.is_visible():
                        next_btn = btn
                        break
                except:
                    pass

            if next_btn:
                next_btn.click()
                page.wait_for_timeout(2000)
                page.wait_for_load_state("networkidle")
                page_num += 1
            else:
                break
        except:
            break

    print(f"  إجمالي: {len(all_offers)} عرض")
    return all_offers

def scrape_all():
    print("جاري سحب عروض البنك الأهلي...")
    all_offers = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in URLS:
            offers = scrape_page(page, url)
            for o in offers:
                if o["store"] not in seen:
                    seen.add(o["store"])
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
