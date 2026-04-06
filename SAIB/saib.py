import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json
import os

BASE_URL = "https://www.saib.com.sa"
OFFERS_URL = f"{BASE_URL}/ar/aseel_program"
OUTPUT_FILE = "../data/saib.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.9",
}

MONTHS_PAT = r"(\d{1,2})\s+(يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|أغسطس|اغسطس|سبتمبر|أكتوبر|اكتوبر|نوفمبر|ديسمبر)\s+(\d{4})"

def get_expiry(link):
    """يفتح صفحة العرض ويسحب تاريخ الانتهاء"""
    try:
        res = requests.get(link, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text(separator=" ")
        text = re.sub(r'\s+', ' ', text)

        # بعد "حتى" بتاريخ عربي
        m = re.search(r"حتى\s*" + MONTHS_PAT, text)
        if m:
            return f"{m.group(1)} {m.group(2)} {m.group(3)}"

        # بعد "حتى" بتاريخ أرقام مثل 31-12-2026
        m = re.search(r"حتى\s*(\d{1,2})[-/](\d{1,2})[-/](\d{4})", text)
        if m:
            return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"

        # آخر تاريخ عربي
        all_dates = re.findall(MONTHS_PAT, text)
        if all_dates:
            return f"{all_dates[-1][0]} {all_dates[-1][1]} {all_dates[-1][2]}"

        # آخر تاريخ أرقام
        all_num = re.findall(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", text)
        if all_num:
            return f"{all_num[-1][0]}/{all_num[-1][1]}/{all_num[-1][2]}"

    except:
        pass
    return ""

def scrape_page(page_num):
    url = OFFERS_URL if page_num == 0 else f"{OFFERS_URL}?page={page_num}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        offers = []
        for item in soup.select("div.offer-style"):
            a = item.select_one("a")
            if not a:
                continue
            link = a.get("href", "")
            if link.startswith("/"):
                link = BASE_URL + link

            img_el = item.select_one("img")
            img = ""
            if img_el:
                src = img_el.get("src", "")
                img = BASE_URL + src if src.startswith("/") else src

            store = item.select_one("div.title")
            store = store.get_text(strip=True) if store else ""

            discount_el = item.select_one("div.info")
            discount_text = discount_el.get_text(strip=True) if discount_el else ""

            discount = ""
            m = re.search(r"(\d+)\s*[%٪]", discount_text)
            if m:
                discount = m.group(0).replace("٪", "%")

            if store:
                offers.append({
                    "store":       store,
                    "discount":    discount,
                    "category":    "عروض أصيل",
                    "expiry":      "",
                    "description": discount_text,
                    "img":         img,
                    "link":        link,
                    "promo":       "",
                    "_bank":       "saib",
                    "_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
                })

        has_next = bool(soup.select_one("a[href*='page=']"))
        return offers, has_next
    except Exception as e:
        print(f"  خطأ في الصفحة {page_num}: {e}")
        return [], False

def scrape_all():
    print("جاري سحب عروض برنامج أصيل...")
    all_offers = []
    seen = set()
    page = 0

    while True:
        print(f"  صفحة {page}...")
        offers, has_next = scrape_page(page)
        for o in offers:
            if o["store"] not in seen:
                seen.add(o["store"])
                all_offers.append(o)
        print(f"  {len(offers)} عرض — المجموع: {len(all_offers)}")
        if not has_next or not offers:
            break
        page += 1

    # سحب تاريخ الانتهاء من كل صفحة عرض
    print("\nجاري سحب تواريخ الانتهاء...")
    total = len(all_offers)
    for i, o in enumerate(all_offers, 1):
        print(f"  [{i}/{total}] {o['store']}...")
        o["expiry"] = get_expiry(o["link"])

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
