import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os

URL = "https://bsf.sa/arabic/personal/cards/offers/all-offers"
OUTPUT_FILE = "../data/bsf.json"

CATEGORY_MAP = {
    "travel":        "سفر",
    "live-well":     "اسلوب حياة",
    "shopping":      "تسوق",
    "restaurants":   "مطاعم",
    "entertainment": "ترفيه",
}

def get_category(link):
    for key, val in CATEGORY_MAP.items():
        if f"/offers/{key}" in link:
            return val
    return "عروض"

def scrape_offers():
    print("جاري فتح المتصفح وسحب العروض...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        clicks = 0
        while clicks < 20:
            try:
                btn = None
                for selector in ["a.load-more","button.load-more","[class*='load']","[class*='more']"]:
                    el = page.locator(selector).first
                    if el.is_visible(timeout=1000):
                        btn = el
                        break
                if btn:
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    page.wait_for_timeout(2000)
                    clicks += 1
                    print(f"  تحميل المزيد... ({clicks})")
                else:
                    break
            except:
                break

        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    offers = []
    seen = set()

    for item in soup.select("ul li a[href*='/offers/']"):
        img_tag = item.find("img")
        if not img_tag:
            continue
        title = img_tag.get("alt", "").strip()
        if not title:
            continue

        img_url = img_tag.get("src", "")
        if img_url.startswith("/"):
            img_url = "https://bsf.sa" + img_url

        link = item.get("href", "")
        if link.startswith("/"):
            link = "https://bsf.sa" + link

        if link in seen:
            continue
        seen.add(link)

        texts = [t.strip() for t in item.stripped_strings if t.strip() and t.strip() != title]
        description = texts[0] if texts else ""
        expiry = texts[1] if len(texts) > 1 else ""

        # استخرج نسبة الخصم
        import re
        discount = ""
        m = re.search(r"(\d+)\s*%", description)
        if m:
            discount = m.group(0)

        # الصيغة الموحدة
        offers.append({
            "store":       title,
            "discount":    discount,
            "category":    get_category(link),
            "expiry":      expiry,
            "description": description[:150] + ("..." if len(description) > 150 else ""),
            "img":         img_url,
            "link":        link,
            "promo":       "",
            "_bank":       "bsf",
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
    offers = scrape_offers()
    save_json(offers)
