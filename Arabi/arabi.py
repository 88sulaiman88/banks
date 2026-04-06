import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime

BASE_URL = "https://anb.com.sa"
OUTPUT_FILE = "../data/arabi.json"

# أضف روابط جديدة هنا عند إطلاق حملات جديدة
OFFER_PAGES = [
    {"url": f"{BASE_URL}/ar/web/anb/anb-x-iherb-offer",    "category": "تسوق"},
    {"url": f"{BASE_URL}/ar/web/anb/anb-x-jeddah-season",  "category": "عروض موسم جدة"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.9",
}


MONTHS_PAT = r"(\d{1,2})\s+(يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|أغسطس|اغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s+(\d{4})"

def get_expiry(text):
    # بعد حتى/الى بتاريخ عربي
    m = re.search(r"(?:حتى|الى|إلى)\s*" + MONTHS_PAT, text)
    if m:
        return f"{m.group(1)} {m.group(2)} {m.group(3)}"
    # بعد حتى بأرقام
    m = re.search(r"(?:حتى|الى|إلى)\s*([\d/]+)", text)
    if m:
        return m.group(1)
    # آخر تاريخ عربي
    all_d = re.findall(MONTHS_PAT, text)
    if all_d:
        return f"{all_d[-1][0]} {all_d[-1][1]} {all_d[-1][2]}"
    return ""

def scrape_page(url, default_category):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
    except Exception as e:
        print(f"  خطأ: {e}")
        return []

    offers = []

    # صفحة بها عروض متعددة (dynamic-item-list)
    cards = soup.select("div.cards-item")
    if cards:
        for card in cards:
            # الاسم
            name_el = card.select_one("div.font-weight-bold.anb-clr-primary-color")
            store = name_el.get_text(strip=True) if name_el else ""
            if not store:
                continue

            # صورة البطاقة
            img_el = card.select_one("img.w-auto")
            img = img_el.get("src", "") if img_el else ""
            if img and not img.startswith("http"):
                img = BASE_URL + img

            # الـ modal ID
            item_div = card.select_one("div.item-card")
            modal_id = ""
            if item_div:
                onclick = item_div.get("onclick", "")
                m = re.search(r"#(detailsModal\w+)", onclick)
                if m:
                    modal_id = m.group(1)

            # الوصف من الـ modal
            description = ""
            discount = ""
            expiry = ""
            banner_img = ""

            if modal_id:
                modal = soup.find("div", {"id": modal_id})
                if modal:
                    # صورة الـ modal
                    banner = modal.select_one("img.w-100")
                    if banner:
                        src = banner.get("src", "")
                        banner_img = BASE_URL + src if src.startswith("/") else src

                    # الوصف
                    subtext = modal.select_one("div.subtext")
                    full_modal_text = ""
                    if subtext:
                        full_modal_text = re.sub(r'\s+', ' ', subtext.get_text(separator=" ", strip=True))
                        description = full_modal_text[:150] + ("..." if len(full_modal_text) > 150 else "")

                    # الخصم
                    m2 = re.search(r"(\d+)\s*[%٪]", full_modal_text)
                    if m2:
                        discount = m2.group(0).replace("٪", "%")

                    # تاريخ الانتهاء من النص الكامل
                    expiry = get_expiry(full_modal_text)

            offers.append({
                "store":       store,
                "discount":    discount,
                "category":    default_category,
                "expiry":      expiry,
                "description": description,
                "img":         banner_img or img,
                "link":        url,
                "promo":       "",
                "_bank":       "arabi",
                "_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

    else:
        # صفحة عرض واحد (مثل iherb)
        title_el = soup.select_one("h1, h2, .portlet-title")
        store = title_el.get_text(strip=True) if title_el else url.split("/")[-1].replace("-", " ")

        img_el = soup.select_one("div.portlet-body img, .journal-content-article img")
        img = ""
        if img_el:
            src = img_el.get("src", "")
            img = BASE_URL + src if src.startswith("/") else src

        # الوصف من كل النص
        content = soup.select_one("div.journal-content-article, div.portlet-body")
        description = ""
        discount = ""
        expiry = ""
        if content:
            text = content.get_text(separator=" ", strip=True)
            text = re.sub(r'\s+', ' ', text)

            # الخصم
            m = re.search(r"(\d+)\s*[%٪]", text)
            if m:
                discount = m.group(0).replace("٪", "%")

            # تاريخ الانتهاء
            expiry = get_expiry(text)

            description = text[:150] + ("..." if len(text) > 150 else "")

        # كود الترويج
        promo = ""
        full_text = soup.get_text()
        m3 = re.search(r'"([A-Z]{4,}\d*)"', full_text)
        if m3:
            promo = m3.group(1)

        offers.append({
            "store":       store,
            "discount":    discount,
            "category":    default_category,
            "expiry":      expiry,
            "description": description,
            "img":         img,
            "link":        url,
            "promo":       promo,
            "_bank":       "arabi",
            "_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
        })

    return offers

def scrape_all():
    print("جاري سحب عروض البنك العربي الوطني...")
    all_offers = []
    seen = set()

    for page_info in OFFER_PAGES:
        url = page_info["url"]
        cat = page_info["category"]
        print(f"  {url.split('/')[-1]}...")
        offers = scrape_page(url, cat)
        for o in offers:
            key = f"{o['store']}_{o['link']}"
            if key not in seen:
                seen.add(key)
                all_offers.append(o)
        print(f"  {len(offers)} عرض")

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
