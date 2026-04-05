import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime

BASE_URL = "https://www.aljazirabank.com.sa"
URL = f"{BASE_URL}/ar-sa/personal/promotional-offers"
OUTPUT_FILE = "../data/jazira.json"

def scrape_offers():
    print("جاري فتح الصفحة...")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    all_offers = []
    seen = set()

    for script in soup.find_all("script"):
        text = script.string or ""
        if "initModule" not in text or "Title" not in text:
            continue

        matches = re.findall(r'items:\s*(\[(?:[^[\]]|\[(?:[^[\]]|\[[^\]]*\])*\])*\])', text, re.DOTALL)

        for match in matches:
            try:
                items = json.loads(match)
                if not items or not isinstance(items[0], dict):
                    continue
                if "Title" not in items[0]:
                    continue

                for item in items:
                    title = item.get("Title", "").strip()
                    if not title or title in seen:
                        continue
                    seen.add(title)

                    desc_html = item.get("Description", "") or item.get("Subtitle", "")
                    desc = BeautifulSoup(desc_html, "html.parser").get_text(separator=" ", strip=True)
                    desc = desc[:150] + ("..." if len(desc) > 150 else "")

                    expiry_raw = item.get("EndDate", "").strip()
                    expiry = ""
                    if expiry_raw:
                        try:
                            # صيغة ISO: 2026-12-30T00:00:00
                            dt = datetime.fromisoformat(expiry_raw.replace("Z", ""))
                            expiry = dt.strftime("%d/%m/%Y")
                        except:
                            # إذا فشل التحويل اتركه فارغاً
                            expiry = ""
                    discount_text = item.get("Discount", "").strip()

                    # استخرج نسبة الخصم
                    discount = ""
                    m = re.search(r"(\d+)\s*[%٪]", discount_text + " " + title)
                    if m:
                        discount = m.group(0).replace("٪", "%")
                    elif discount_text:
                        discount = discount_text

                    img = item.get("Logo", "")
                    if img and not img.startswith("http"):
                        img = BASE_URL + img

                    context = item.get("Context", {})
                    link = context.get("DetailUrl", URL) if isinstance(context, dict) else URL
                    if link and not link.startswith("http"):
                        link = BASE_URL + link

                    cat = item.get("Category", {})
                    category = cat.get("Title", "عروض") if isinstance(cat, dict) else "عروض"

                    # الصيغة الموحدة
                    all_offers.append({
                        "store":       title,
                        "discount":    discount,
                        "category":    category,
                        "expiry":      expiry,
                        "description": desc,
                        "img":         img,
                        "link":        link,
                        "promo":       "",
                        "_bank":       "jazira",
                        "_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
            except:
                continue

    print(f"تم سحب {len(all_offers)} عرض")
    return all_offers

def save_json(offers):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)
    print(f"✅ تم الحفظ في {OUTPUT_FILE}")

if __name__ == "__main__":
    offers = scrape_offers()
    save_json(offers)
