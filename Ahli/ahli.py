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
MAX_PAGES = 20  # حد أقصى للصفحات

MONTHS_PAT = r"(\d{1,2})\s+(يناير|فبراير|مارس|أبريل|ابريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s+(\d{4})"

def get_expiry(expiry_text):
    m = re.search(r"حتى\s*" + MONTHS_PAT, expiry_text)
    if m:
        return f"{m.group(1)} {m.group(2)} {m.group(3)}"
    all_d = re.findall(MONTHS_PAT, expiry_text)
    if all_d:
        return f"{all_d[-1][0]} {all_d[-1][1]} {all_d[-1][2]}"
    return ""

def get_links(page, url):
    """يسحب روابط العروض بفتح كل بطاقة في tab جديد"""
    links = []
    n = page.locator("div.singleItem-wrap").count()

    for i in range(n):
        try:
            card = page.locator("div.singleItem-wrap").nth(i)
            with page.context.expect_page() as new_page_info:
                card.click(modifiers=["Control"])
            new_page = new_page_info.value
            new_page.wait_for_load_state("domcontentloaded")
            link = new_page.url
            new_page.close()
            links.append(link if link != url and "/ar/" in link else url)
        except:
            links.append(url)

    return links

def scrape_page(page, url):
    print(f"  جاري سحب: {url.split('/')[-2] or url.split('/')[-1]}...")
    page.goto(url, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)

    all_offers = []
    seen_stores = set()
    page_num = 1

    while page_num <= MAX_PAGES:
        soup = BeautifulSoup(page.content(), "html.parser")
        cards_els = soup.select("div.singleItem-wrap")

        print(f"    صفحة {page_num}: {len(cards_els)} بطاقة — جاري سحب الروابط...")
        links = get_links(page, url)

        # رجّع للصفحة الحالية بعد سحب الروابط
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)
        for _ in range(page_num - 1):
            try:
                for btn in page.locator("button, a").all():
                    try:
                        if "التالي" in btn.inner_text() and btn.is_visible():
                            btn.click()
                            page.wait_for_timeout(1500)
                            break
                    except:
                        pass
            except:
                pass

        soup = BeautifulSoup(page.content(), "html.parser")
        new_count = 0
        for i, item in enumerate(soup.select("div.singleItem-wrap")):
            store_el = item.select_one("div.item_title")
            store = store_el.get_text(strip=True) if store_el else ""
            if not store or store in seen_stores:
                continue
            seen_stores.add(store)
            new_count += 1

            img_el = item.select_one("div.image img")
            img = img_el.get("src", "") if img_el else ""

            desc_el = item.select_one("div.ico-text")
            description = desc_el.get_text(strip=True) if desc_el else ""
            discount = ""
            m = re.search(r"(\d+)\s*[%٪]", description)
            if m:
                discount = m.group(0).replace("٪", "%")

            expiry_el = item.select_one("div.type-text")
            expiry = get_expiry(expiry_el.get_text(strip=True)) if expiry_el else ""

            cat_el = item.select_one("div.global-category-tag")
            category = cat_el.get_text(strip=True) if cat_el else "عروض"

            link = links[i] if i < len(links) else url

            all_offers.append({
                "store":       store,
                "discount":    discount,
                "category":    category,
                "expiry":      expiry,
                "description": description[:150] + ("..." if len(description) > 150 else ""),
                "img":         img,
                "link":        link,
                "promo":       "",
                "_bank":       "ahli",
                "_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

        print(f"    تم: {new_count} عرض جديد")

        if new_count == 0:
            break

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
