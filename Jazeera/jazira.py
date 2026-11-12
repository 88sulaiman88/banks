import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime

BASE_URL = "https://www.aljazirabank.com.sa"
URL = f"{BASE_URL}/ar-sa/personal/offers"
OUTPUT_FILE = "../data/jazira.json"

# أقسام ما نسحبها (ليست عروض بطاقات)
SKIP_SECTIONS = ("التأجير التمويلي",)

MONTHS = r"يناير|فبراير|مارس|أبريل|ابريل|إبريل|مايو|يونيو|يوليو|أغسطس|اغسطس|سبتمبر|أكتوبر|اكتوبر|نوفمبر|ديسمبر"
DATE_AR = r"(\d{1,2})\s*(" + MONTHS + r")\s*(\d{4})"
DATE_NUM = r"(\d{1,2})/(\d{1,2})/(\d{4})"


def clean(text):
    return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ")).strip()


def fetch_html():
    from playwright.sync_api import sync_playwright
    print("جاري فتح الصفحة...")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            locale="ar-SA",
            viewport={"width": 1366, "height": 900},
        )
        resp = page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        found = True
        try:
            page.wait_for_selector(".offer-popup-wrapper", state="attached", timeout=45000)
        except Exception:
            found = False
        page.wait_for_timeout(3000)
        html = page.content()

        # ─── تشخيص ───
        print(f"[تشخيص] HTTP status: {resp.status if resp else 'None'}")
        print(f"[تشخيص] الرابط النهائي: {page.url}")
        print(f"[تشخيص] عنوان الصفحة: {page.title()}")
        print(f"[تشخيص] حجم HTML: {len(html)} حرف | offer-popup-wrapper: {html.count('offer-popup-wrapper')}")
        if not found:
            print("[تشخيص] ما ظهرت العروض خلال 45 ثانية. بداية الكود الخام:")
            print(html[:1500])
            try:
                print("[تشخيص] نص الصفحة:")
                print(page.inner_text("body")[:800])
            except Exception as e:
                print(f"(تعذر قراءة النص: {e})")
        browser.close()
    return html


def extract_expiry(*texts):
    """يرجع تاريخ الانتهاء (اللي بعد 'حتى') بصيغة يفهمها rebuild_index"""
    for text in texts:
        text = clean(text)
        if not text:
            continue
        m = re.search(r"(?:حتى|إلى|الى|لغاية)\s*(?:تاريخ\s*)?" + DATE_AR, text)
        if m:
            return f"{int(m.group(1))} {m.group(2)} {m.group(3)}"
        m = re.search(r"(?:حتى|إلى|الى|لغاية)\s*(?:تاريخ\s*)?" + DATE_NUM, text)
        if m:
            return f"{int(m.group(1))}/{int(m.group(2))}/{m.group(3)}"
    return ""


def extract_discount(*texts):
    for text in texts:
        text = clean(text)
        m = re.search(r"(\d{1,3})\s*[%٪]", text) or re.search(r"[%٪]\s*(\d{1,3})", text)
        if m:
            return f"{m.group(1)}%"
    return ""


def extract_promo(*texts):
    for text in texts:
        m = re.search(r"(?:رمز|كود)\s*(?:الخصم|الترويجي)?\s*:?\s*([A-Za-z][A-Za-z0-9]{2,15})", clean(text))
        if m:
            return m.group(1)
    return ""


def img_url(tag):
    if not tag:
        return ""
    src = tag.get("data-src") or tag.get("src") or ""
    if not src or src.startswith("data:") or src.startswith("./"):
        return ""
    if src.startswith("//"):
        return "https:" + src
    if not src.startswith("http"):
        src = BASE_URL + ("" if src.startswith("/") else "/") + src
    return src


def parse_offers(html):
    soup = BeautifulSoup(html, "html.parser")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # الأزرار/الكروت اللي تفتح كل نافذة عرض
    triggers = {}
    for t in soup.find_all(attrs={"modal-id": True}):
        if "offer-popup-wrapper" not in (t.get("class") or []):
            triggers.setdefault(t["modal-id"], t)

    all_offers = []
    seen = set()

    for pop in soup.select(".offer-popup-wrapper"):
        mid = pop.get("modal-id", "")
        trig = triggers.get(mid)
        card = trig.find_parent(class_="offer-card") if trig else None

        # عنوان القسم (أحدث العروض / عروض الشركاء / ماستركارد / فيزا ...)
        h2 = (trig or pop).find_previous("h2")
        section = clean(h2.get_text(" ")) if h2 else ""
        if any(s in section for s in SKIP_SECTIONS):
            continue

        terms_el = pop.select_one(".offer-terms-section")
        terms = clean(terms_el.get_text(" ")) if terms_el else ""
        first_p = ""
        if terms_el:
            p = terms_el.find(["p", "li"])
            first_p = clean(p.get_text(" ")) if p else ""

        header = pop.select_one(".offer-popup-header")
        if header:
            # ─── عروض الشركاء (الكاروسيل) ───
            title = clean(header.get_text(" "))
            info = [clean(p.get_text(" ")) for p in header.parent.find_all("p")]
            code_line = re.sub(r"^Discount Code:\s*", "", info[0]) if info else ""
            date_line = " ".join(info[1:])
            desc = terms
            discount = extract_discount(code_line, title, first_p)
            expiry = extract_expiry(date_line, terms)
            promo = extract_promo(code_line, terms)
            img = img_url(pop.select_one(".offer-popup-logo-wrapper img")) or img_url(trig.find("img") if trig else None)
            # اسم التصنيف من التبويب (تسوق / المطاعم ...)
            category = section or "عروض"
            tab = (trig or pop).find_parent(class_="baj-tab-content")
            if tab is not None and tab.get("data-tab"):
                btn = None
                for box in tab.parents:
                    btn = box.find("button", attrs={"data-tab": tab["data-tab"]})
                    if btn:
                        break
                if btn and clean(btn.get_text(" ")):
                    category = clean(btn.get_text(" "))
        elif card:
            # ─── الكروت (أحدث العروض / ماستركارد / فيزا) ───
            t_el = card.select_one(".title-card")
            title = clean(t_el.get_text(" ")) if t_el else ""
            p_el = card.select_one("p")
            short = clean(p_el.get_text(" ")) if p_el else ""
            desc = short or terms
            discount = extract_discount(title, short)
            expiry = extract_expiry(terms)
            promo = extract_promo(short, terms)
            img = img_url(card.select_one("img.offer-card-img")) or img_url(pop.select_one("img"))
            category = section or "عروض"
        else:
            continue

        if not title:
            continue
        key = (title, discount, expiry)
        if key in seen:
            continue
        seen.add(key)

        all_offers.append({
            "store":       title,
            "discount":    discount,
            "category":    category,
            "expiry":      expiry,
            "description": desc[:150] + ("..." if len(desc) > 150 else ""),
            "img":         img,
            "link":        URL,
            "promo":       promo,
            "_bank":       "jazira",
            "_updated":    now,
        })

    print(f"تم سحب {len(all_offers)} عرض")
    return all_offers


def save_json(offers):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)
    print(f"✅ تم الحفظ في {OUTPUT_FILE}")


if __name__ == "__main__":
    # للتجربة على ملف محفوظ:  python jazira.py page.html
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
            offers = parse_offers(f.read())
    else:
        offers = parse_offers(fetch_html())
    if not offers:
        # لا تمسح البيانات القديمة بقائمة فاضية
        print("❌ صفر عروض — لم يتم تعديل الملف. راجع سطور [تشخيص] فوق.")
        sys.exit(1)
    save_json(offers)
