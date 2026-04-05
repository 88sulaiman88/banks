import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
import json
import os
from datetime import datetime, timezone

API_URL = "https://www.alrajhibank.com.sa/sitecore/api/graph/edge?sc_apikey=B4E643CA-9AA4-4D3E-BFF3-8E7CA14649D7"
BASE_URL = "https://www.alrajhibank.com.sa"
OUTPUT_FILE = "../data/rajhi.json"   # ← الملف الناتج

KNOWN_CATEGORIES = {
    "B1F6C9499BC149DB80CF92FEA7B6757A": "عروض رمضان",
    "87EE5E2EC80E48329EAB2A69D43F3509": "المأكولات والمشروبات",
    "2DB9969C72E24438B0C7F2CD81F42AB6": "مكافأة",
    "01E2A625C53846AC8083B7CB92CD0C1E": "الصحة",
    "46A48375B0D84DA38816C14522133D26": "سوار",
    "C1197106168742E4AD962A725EDE7E07": "الازياء والتجميل",
    "783D9AB00B714F38AF7BAAEE70D95B85": "الاثاث",
    "5A8804C49AAA4631B88D0F4FF82BBE8D": "السفر والترفيه",
    "5E21A568AC2A47F4A4FFA01FF272A243": "خدمة السيارات",
    "3C8E8E16A8E440E39527F10257F3CFCF": "تحويل",
    "BB0EBCDCDFE4497894E1ED3104D69DFF": "عروض التمويل",
    "6A14812C68D84F4E8AC63B5E1B053598": "اخرى",
}

HEADERS = {
    "content-type": "application/json",
    "accept": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36",
}

# ─── اكتشاف الكاتيجوريز ───
def discover_categories_from_offers():
    print("  جاري مسح العروض لاكتشاف الكاتيجوريز...")
    query_template = """{{
  search(
    where: {{
      AND: [
        {{ name: "_language", value: "ar" }}
        {{ name: "_templates", value: "{{8CCC36A1-440D-44E2-AD6B-3C541F5E6A89}}", operator: EQ }}
        {{ name: "IsActive", value: "true", operator: EQ }}
      ]
    }}
    first: 100
    {after}
  ) {{
    pageInfo {{ endCursor hasNext }}
    results {{
      ancestors(hasLayout: false) {{ id name }}
    }}
  }}
}}"""

    discovered = {}
    cursor = None
    IGNORE = {"sitecore","content","home","personal","discounts","media-campaigns","stores","ar","en","media campaigns"}

    while True:
        after = f'after: "{cursor}"' if cursor else ""
        try:
            res = requests.post(API_URL, json={"query": query_template.format(after=after)}, headers=HEADERS, timeout=15)
            data = res.json().get("data", {}).get("search", {})
            for r in data.get("results", []):
                for anc in r.get("ancestors", []):
                    anc_id = anc.get("id", "").replace("-", "").upper()
                    anc_name = anc.get("name", "").strip()
                    if anc_id and anc_name and anc_name.lower() not in IGNORE and anc_id not in KNOWN_CATEGORIES and len(anc_id) == 32:
                        discovered[anc_id] = anc_name
            page_info = data.get("pageInfo", {})
            if not page_info.get("hasNext") or not page_info.get("endCursor"):
                break
            cursor = page_info["endCursor"]
        except Exception as e:
            print(f"  خطأ: {e}")
            break

    return discovered

def get_categories():
    print("\n🔍 جاري اكتشاف الكاتيجوريز...")
    discovered = discover_categories_from_offers()
    new_cats = {k: v for k, v in discovered.items() if k not in KNOWN_CATEGORIES}
    if new_cats:
        print(f"  ⚠️  كاتيجوريز جديدة: {list(new_cats.values())}")
    else:
        print("  ✅ لا توجد كاتيجوريز جديدة")
    all_cats = {**KNOWN_CATEGORIES, **new_cats}
    print(f"  📂 إجمالي: {len(all_cats)} كاتيجوري\n")
    return all_cats

# ─── سحب العروض ───
def make_query(cat_id, cursor=None):
    after = f'after: "{cursor}"' if cursor else ""
    return {"query": """query cardOfferCategoryItemList {
  search(
    where: {
      AND: [
        { name: "_language", value:"ar" }
        { name: "_path", value: \"""" + cat_id + """\", operator: EQ },
        { name: "_templates", value: "{8CCC36A1-440D-44E2-AD6B-3C541F5E6A89}", operator: EQ }
        { name: "IsActive", value: "true", operator: EQ }
      ]
    }
    first: 20
    """ + after + """
    orderBy: { name: "__sortorder_tl", direction: ASC}
  ) {
    total
    pageInfo { endCursor hasNext }
    results {
      id name
      url { path }
      Title: field(name: "Title") { ... on TextField { jsonValue } }
      AboutOffer: field(name: "AboutOffer") { ... on TextField { jsonValue } }
      ExpiryDate: field(name: "ExpiryDate") { ... on DateField { jsonValue } }
      PromoCode: field(name: "PromoCode") { ... on TextField { jsonValue } }
      CardImage: field(name: "CardImage") { ... on ImageField { jsonValue } }
      Logo: field(name: "Logo") { ... on ImageField { jsonValue } }
      BannerImage: field(name: "BannerImage") { ... on ImageField { jsonValue } }
    }
  }
}"""}

def fetch_all_pages(cat_id):
    all_results = []
    cursor = None
    while True:
        try:
            res = requests.post(API_URL, json=make_query(cat_id, cursor),
                headers={**HEADERS, "referer": f"{BASE_URL}/Personal/Discounts?category={cat_id}"}, timeout=15)
            data = res.json().get("data", {}).get("search", {})
            results = data.get("results", [])
            all_results.extend(results)
            page_info = data.get("pageInfo", {})
            if not page_info.get("hasNext") or not page_info.get("endCursor"):
                break
            cursor = page_info["endCursor"]
        except Exception as e:
            print(f"  خطا: {e}")
            break
    return all_results

def parse_offer(item, cat_name):
    def val(field):
        v = item.get(field)
        if not v: return ""
        jv = v.get("jsonValue", {})
        if isinstance(jv, dict): return jv.get("value", "")
        return str(jv) if jv else ""

    title = val("Title").strip()
    if not title: return None

    expiry_raw = val("ExpiryDate")
    expiry_display = ""
    is_expired = False
    if expiry_raw:
        try:
            expiry_dt = datetime.fromisoformat(expiry_raw.replace("Z", "+00:00"))
            expiry_display = expiry_dt.strftime("%d/%m/%Y")
            is_expired = expiry_dt < datetime.now(timezone.utc)
        except:
            expiry_display = expiry_raw

    if is_expired:
        return None   # تجاهل المنتهية

    img = ""
    for field in ["CardImage", "Logo", "BannerImage"]:
        v = item.get(field)
        if not v: continue
        src = v.get("jsonValue", {}).get("value", {})
        if isinstance(src, dict): src = src.get("src", "")
        if src:
            img = BASE_URL + "/" + src.lstrip("/") if not src.startswith("http") else src
            break

    url_path = item.get("url", {}).get("path", "")

    # استخرج نسبة الخصم
    about = val("AboutOffer")
    import re
    discount = ""
    m = re.search(r"(\d+)\s*%", about)
    if m: discount = m.group(0)

    # الصيغة الموحدة
    return {
        "store":       title,
        "discount":    discount,
        "category":    cat_name,
        "expiry":      expiry_display,
        "description": about[:150] + ("..." if len(about) > 150 else ""),
        "img":         img,
        "link":        BASE_URL + url_path if url_path else "",
        "promo":       val("PromoCode"),
        "_bank":       "rajhi",
        "_updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

def scrape_all():
    categories = get_categories()
    all_offers = []
    seen = set()

    for cat_id, cat_name in categories.items():
        print(f"جاري سحب: {cat_name}...")
        results = fetch_all_pages(cat_id)
        count = 0
        for item in results:
            offer = parse_offer(item, cat_name)
            if offer and offer["store"] not in seen:
                seen.add(offer["store"])
                all_offers.append(offer)
                count += 1
        print(f"  {count} عرض")

    print(f"\nالاجمالي: {len(all_offers)} عرض نشط")
    return all_offers

def save_json(offers):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)
    print(f"✅ تم الحفظ في {OUTPUT_FILE}")

if __name__ == "__main__":
    offers = scrape_all()
    save_json(offers)
