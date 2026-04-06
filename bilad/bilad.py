import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json
import os

BASE_URL = "https://www.bankalbilad.com.sa"
SEED_URL = f"{BASE_URL}/ar/personal/cards/offers/Pages/Turkish-Airlines-Offer-with-Bank-Albilad.aspx"
OUTPUT_FILE = "../data/bilad.json"

MONTHS_PAT  = r"(\d{1,2})\s*[-\s]\s*(يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s*[-\s]\s*(\d{4})"
MONTHS_PAT2 = r"(\d{1,2})\s+(يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s+(\d{4})"

def clean(t):
    """ينظف النص من الأحرف الخفية"""
    return re.sub(r'\s+', ' ', ''.join(
        c if c.isprintable() and c != '\xa0' else ' '
        for c in str(t)
    )).strip()

def get_all_links(page):
    page.goto(SEED_URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)
    soup = BeautifulSoup(page.content(), "html.parser")
    links = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = clean(a.get_text()).replace("محدد حالياً", "").strip()
        if "offers/Pages" in href and "default" not in href and text and len(text) > 3:
            if not href.startswith("http"):
                href = BASE_URL + href
            if href not in links:
                links[href] = text
    return links

def scrape_offer(page, url, link_text):
    try:
        page.goto(url, wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(2000)
        soup = BeautifulSoup(page.content(), "html.parser")

        # العنوان
        title = ""
        h1 = soup.select_one("h1")
        if h1:
            title = clean(h1.get_text())
        if not title or len(title) < 3:
            title = link_text

        # الخصم والوصف
        description = ""
        discount = ""
        SKIP = "استرداد نقدي عند إصدار بطاقتك"

        for tag in soup.find_all(string=True):
            if tag.parent.name in ["script", "style", "nav", "header", "footer"]:
                continue
            t = clean(tag)
            if not t or len(t) < 10 or SKIP in t:
                continue
            # الخصم
            if not discount:
                m = re.search(r"(\d+)\s*[%٪]", t)
                if m:
                    pct = int(m.group(1))
                    if 1 <= pct <= 100:
                        discount = f"{pct}%"
            # الوصف
            if not description and len(t) > 20 and any(k in t for k in ["خصم", "استمتع", "احصل"]):
                description = t[:150] + ("..." if len(t) > 150 else "")
            if description and discount:
                break

        # تاريخ الانتهاء - آخر تاريخ في الصفحة
        expiry = ""
        all_text = clean(soup.get_text(separator=" "))

        # بعد حتى/الى/–
        m = re.search(r"(?:حتى|الى|إلى|–)\s*" + MONTHS_PAT, all_text)
        if m:
            expiry = f"{m.group(1)} {m.group(2)} {m.group(3)}"

        if not expiry:
            m = re.search(r"(?:حتى|الى|إلى|–)\s*" + MONTHS_PAT2, all_text)
            if m:
                expiry = f"{m.group(1)} {m.group(2)} {m.group(3)}"

        if not expiry:
            # آخر تاريخ بالشرطة
            all_d = re.findall(MONTHS_PAT, all_text)
            if all_d:
                expiry = f"{all_d[-1][0]} {all_d[-1][1]} {all_d[-1][2]}"

        if not expiry:
            # آخر تاريخ عادي
            all_d = re.findall(MONTHS_PAT2, all_text)
            if all_d:
                expiry = f"{all_d[-1][0]} {all_d[-1][1]} {all_d[-1][2]}"

        return {
            "store":       title,
            "discount":    discount,
            "category":    "عروض",
            "expiry":      expiry,
            "description": description,
            "img":         "",
            "link":        url,
            "promo":       "",
            "_bank":       "bilad",
            "_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
    except Exception as e:
        print(f"  خطأ: {e}")
        return None

def scrape_all():
    offers = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({"Accept-Language": "ar,en;q=0.9"})

        print("جاري سحب روابط العروض...")
        links = get_all_links(page)

        seen = set()
        unique_links = {}
        for url, text in links.items():
            if text and text not in seen:
                seen.add(text)
                unique_links[url] = text
        print(f"وجدنا {len(unique_links)} رابط")

        for i, (url, text) in enumerate(unique_links.items(), 1):
            name = url.split("/")[-1].replace(".aspx", "")
            print(f"[{i}/{len(unique_links)}] {name}...")
            offer = scrape_offer(page, url, text)
            if offer and offer["store"]:
                offers.append(offer)

        browser.close()

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
