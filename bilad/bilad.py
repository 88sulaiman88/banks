import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time
import json
import os

BASE_URL = "https://www.bankalbilad.com.sa"
SEED_URL = f"{BASE_URL}/ar/personal/cards/offers/Pages/Sedra-tea.aspx"
OUTPUT_FILE = "../data/bilad.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.9",
}

def get_all_links():
    res = requests.get(SEED_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")
    links = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if "offers/Pages" in href and "default" not in href:
            if not href.startswith("http"):
                href = BASE_URL + href
            if href not in links:
                links[href] = text
    return links

def scrape_offer(url, link_text):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")

        title = ""
        h1 = soup.select_one("h1")
        if h1:
            title = h1.get_text(strip=True)
        if not title or title == "Sedra-tea":
            title = link_text

        discount = ""
        m = re.search(r"(\d+)\s*[%٪]", title + " " + link_text)
        if m:
            discount = m.group(0).replace("٪", "%")

        description = ""
        for h2 in soup.find_all("h2"):
            t = h2.get_text(strip=True)
            if t and "طريقة" not in t and "الشروط" not in t and len(t) > 5:
                description = t
                break

        expiry = ""
        for tag in soup.find_all(string=lambda t: t and "حتى" in str(t) and re.search(r'\d{4}', str(t))):
            t = str(tag).strip()
            m2 = re.search(r'حتى\s+(.+?)\.?\s*$', t)
            if m2:
                expiry = m2.group(1).strip()
                break

        # الصيغة الموحدة
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
        print(f"  خطا: {e}")
        return None

def scrape_all():
    print("جاري سحب روابط العروض...")
    links = get_all_links()

    seen_titles = set()
    unique_links = {}
    for url, text in links.items():
        clean = text.replace("محدد حالياً", "").strip()
        if clean and clean not in seen_titles:
            seen_titles.add(clean)
            unique_links[url] = clean
    print(f"وجدنا {len(unique_links)} رابط")

    offers = []
    for i, (url, text) in enumerate(unique_links.items(), 1):
        name = url.split("/")[-1].replace(".aspx", "")
        print(f"[{i}/{len(unique_links)}] {name}...")
        offer = scrape_offer(url, text)
        if offer and offer["store"]:
            offers.append(offer)
        time.sleep(0.5)

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
