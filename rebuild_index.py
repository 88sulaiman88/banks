import subprocess
import sys
import os
import json
from datetime import datetime

# ─── قائمة البنوك ───
# لإضافة بنك جديد: أضف سطراً هنا فقط
BANKS = [
    {"name": "مصرف الراجحي",          "id": "rajhi", "script": "rajhi/rajhi.py", "json": "data/rajhi.json"},
    {"name": "مصرف الإنماء",          "id": "inma",  "script": "inma/Alinma.py", "json": "data/alinma.json"},
    {"name": "البنك السعودي الفرنسي",  "id": "bsf",   "script": "bsf/bsf.py",    "json": "data/bsf.json"},
    {"name": "بنك البلاد",             "id": "bilad", "script": "bilad/bilad.py", "json": "data/bilad.json"},
    {"name": "البنك السعودي للاستثمار",  "id": "saib",  "script": "saib/saib.py",   "json": "data/saib.json"},
    {"name": "بنك الرياض",         "id": "riyadh","script": "riyadh/riyadh.py","json": "data/riyadh.json"},
    {"name": "بنك الجزيرة",        "id": "jazira","script": "Jazeera/jazira.py","json": "data/jazira.json"},
    {"name": "البنك الأهلي السعودي",        "id": "ahli",  "script": "ahli/ahli.py",   "json": "data/ahli.json"},
    {"name": "بنك الإمارات دبي الوطني", "id": "enbd",  "script": "enbd/enbd.py",   "json": "data/enbd.json"},
    {"name": "البنك العربي الوطني", "id": "arabi", "script": "arabi/arabi.py", "json": "data/arabi.json"},
    {"name": "البنك السعودي الأول",             "id": "sab",   "script": "sab/sab.py",     "json": "data/sab.json"},
    {"name": "STC Bank",              "id": "stc",   "script": "stc/stc.py",     "json": "data/stc.json"},
]

ROOT = os.path.dirname(os.path.abspath(__file__))

# ألوان كل بنك
BANK_COLORS = {
    "rajhi": {"main": "#C8860A", "light": "#F0B040", "bg": "rgba(200,134,10,0.1)", "border": "rgba(200,134,10,0.3)"},
    "inma":  {"main": "#1B6FB5", "light": "#4AA0E8", "bg": "rgba(27,111,181,0.1)", "border": "rgba(27,111,181,0.3)"},
    "bsf":   {"main": "#C9A84C", "light": "#F0D080", "bg": "rgba(201,168,76,0.1)", "border": "rgba(201,168,76,0.3)"},
    "bilad": {"main": "#C41E3A", "light": "#E74C3C", "bg": "rgba(196,30,58,0.1)",  "border": "rgba(196,30,58,0.3)"},
    "saib":   {"main": "#1A5276", "light": "#2E86C1", "bg": "rgba(26,82,118,0.1)",  "border": "rgba(26,82,118,0.3)"},
    "riyadh": {"main": "#006838", "light": "#2ECC71", "bg": "rgba(0,104,56,0.1)",   "border": "rgba(0,104,56,0.3)"},
    "jazira": {"main": "#2D8C4E", "light": "#4CAF72", "bg": "rgba(45,140,78,0.1)",  "border": "rgba(45,140,78,0.3)"},
    "ahli":  {"main": "#006C35", "light": "#00A550", "bg": "rgba(0,108,53,0.1)",   "border": "rgba(0,108,53,0.3)"},
    "enbd":  {"main": "#E31837", "light": "#FF6B6B", "bg": "rgba(227,24,55,0.1)",  "border": "rgba(227,24,55,0.3)"},
    "arabi": {"main": "#8B1A1A", "light": "#CC3333", "bg": "rgba(139,26,26,0.1)",  "border": "rgba(139,26,26,0.3)"},
    "sab":   {"main": "#6D1F7E", "light": "#A855C8", "bg": "rgba(109,31,126,0.1)", "border": "rgba(109,31,126,0.3)"},
    "stc":   {"main": "#6A1B9A", "light": "#CE93D8", "bg": "rgba(106,27,154,0.1)", "border": "rgba(106,27,154,0.3)"},
}

# ────────────────────────────────────────────
def run_bank(bank):
    print(f"\n{'='*50}")
    print(f"🏦  {bank['name']}  —  {bank['script']}")
    print(f"{'='*50}")
    start = datetime.now()
    try:
        result = subprocess.run(
            [sys.executable, bank["script"]],
            cwd=ROOT, encoding="utf-8", errors="replace",
            timeout=600,
        )
        elapsed = (datetime.now() - start).seconds
        if result.returncode == 0:
            print(f"\n✅ {bank['name']} — اكتمل في {elapsed} ثانية")
            return True
        else:
            print(f"\n❌ {bank['name']} — فشل (exit code {result.returncode})")
            return False
    except subprocess.TimeoutExpired:
        print(f"\n❌ {bank['name']} — تجاوز الوقت المحدد (10 دقائق)")
        return False
    except KeyboardInterrupt:
        print(f"\n⏭️  تم تخطي {bank['name']} — جاري الانتقال للبنك التالي")
        return False
    except Exception as e:
        print(f"\n❌ {bank['name']} — خطأ: {e}")
        return False

def load_json(path):
    full = os.path.join(ROOT, path)
    if os.path.exists(full):
        with open(full, encoding="utf-8") as f:
            return json.load(f)
    return None

MONTHS_AR = {
    "يناير":"01","جانفي":"01","january":"01","jan":"01",
    "فبراير":"02","فيفري":"02","february":"02","feb":"02",
    "مارس":"03","march":"03","mar":"03",
    "أبريل":"04","ابريل":"04","april":"04","apr":"04",
    "مايو":"05","may":"05",
    "يونيو":"06","جوان":"06","june":"06","jun":"06",
    "يوليو":"07","جويلية":"07","july":"07","jul":"07",
    "أغسطس":"08","اغسطس":"08","august":"08","aug":"08",
    "سبتمبر":"09","september":"09","sep":"09",
    "أكتوبر":"10","اكتوبر":"10","october":"10","oct":"10",
    "نوفمبر":"11","november":"11","nov":"11",
    "ديسمبر":"12","december":"12","dec":"12",
}

MONTHS_KEYS = "|".join(MONTHS_AR.keys())

def parse_expiry(expiry_str):
    """يحوّل أي صيغة تاريخ لـ datetime — يرجع None إذا فشل"""
    if not expiry_str:
        return None
    import re as _re
    s = expiry_str.strip()
    s = s.replace("\u200b","").replace("\xa0"," ")
    s = _re.sub(r"\s+", " ", s)

    # ابحث بعد حتى/الى/إلى أولاً
    for keyword in [r"حتى\s*", r"الى\s*", r"إلى\s*", r"–\s*", r"-\s*(?=\d)"]:
        m = _re.search(keyword + r"(\d{1,2})\s*[-–\s]\s*(" + MONTHS_KEYS + r")\s*[-–\s]?\s*(\d{4})", s, _re.IGNORECASE)
        if m:
            try:
                month = MONTHS_AR.get(m.group(2).strip(), "01")
                return datetime(int(m.group(3)), int(month), int(m.group(1)))
            except: pass
        m = _re.search(keyword + r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
        if m:
            try:
                return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except: pass

    # صيغة: 30 ديسمبر 2026 أو 30-ديسمبر-2026 — آخر تاريخ
    all_m = list(_re.finditer(r"(\d{1,2})\s*[-–\s]\s*(" + MONTHS_KEYS + r")\s*[-–\s]?\s*(\d{4})", s, _re.IGNORECASE))
    if all_m:
        m = all_m[-1]
        try:
            month = MONTHS_AR.get(m.group(2).strip(), "01")
            return datetime(int(m.group(3)), int(month), int(m.group(1)))
        except: pass

    # صيغة: 30/12/2026 — آخر تاريخ
    all_m = list(_re.finditer(r"(\d{1,2})/(\d{1,2})/(\d{4})", s))
    if all_m:
        m = all_m[-1]
        try:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except: pass

    # صيغة: 2026-12-30
    m = _re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except: pass

    # صيغة: ديسمبر 2026 (بدون يوم)
    m = _re.search(r"(" + MONTHS_KEYS + r")\s*(\d{4})", s, _re.IGNORECASE)
    if m:
        try:
            month = MONTHS_AR.get(m.group(1).strip(), "01")
            return datetime(int(m.group(2)), int(month), 28)
        except: pass

    return None

def is_expired(offer):
    """يتحقق إذا العرض منتهي"""
    expiry_dt = parse_expiry(offer.get("expiry", ""))
    if expiry_dt is None:
        return False  # إذا ما عرفنا التاريخ نعرضه
    return expiry_dt < datetime.now()

# ────────────────────────────────────────────
def build_index(all_offers, bank_status):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ok_count = sum(1 for s in bank_status.values() if s["ok"])
    total = len(all_offers)

    # CSS متغيرات البنوك
    bank_css = ""
    for bid, c in BANK_COLORS.items():
        bank_css += f"\n    --{bid}: {c['main']}; --{bid}-l: {c['light']}; --{bid}-bg: {c['bg']}; --{bid}-br: {c['border']};"

    # status bar
    status_html = ""
    for bank in BANKS:
        s = bank_status.get(bank["id"], {})
        dot = "dot-ok" if s.get("ok") else "dot-err"
        label = f"{bank['name']} — {s.get('count',0)} عرض" if s.get("ok") else f"{bank['name']} — تعذّر التحديث"
        status_html += f'<div class="si"><span class="sd {dot}"></span>{label}</div>\n'

    # أزرار البنوك مع العدد
    total_count = sum(s.get("count", 0) for s in bank_status.values() if s.get("ok"))
    bank_btns = f"<button class='fb active' onclick=\"setBank('all',this)\">الكل <span class='bc'>({total_count})</span></button>\n"
    for bank in BANKS:
        cnt = bank_status.get(bank["id"], {}).get("count", 0)
        if cnt > 0:
            bank_btns += f"<button class='fb f-{bank['id']}' onclick=\"setBank('{bank['id']}',this)\">{bank['name']} <span class='bc'>({cnt})</span></button>\n"

    cat_btns = ""  # تم حذف الكاتيجوريز

    # البطاقات
    cards = ""
    for o in all_offers:
        bid   = o.get("_bank", "")
        bname = o.get("_bankName", "")
        img   = f'<img src="{o["img"]}" onerror="this.remove()">' if o.get("img") else ""
        disc  = f'<span class="db">{o["discount"]}</span>' if o.get("discount") else ""
        exp   = f'ينتهي {o["expiry"]}' if o.get("expiry") else ""

        disc_text = f'<span class="disc-tag">{o["discount"]}</span>' if o.get("discount") else ""
        cards += f"""<a class="card" href="{o.get('link','#')}" target="_blank" data-bank="{bid}" data-cat="{o.get('category','')}">
  <div class="ci">{img}<div class="cf">🏷️</div></div>
  <div class="cb">
    <div class="sn">{o.get('store','—')}</div>
    <div class="card-meta"><span class="bb {bid}">{bname}</span>{disc_text}</div>
    <div class="ft"><span class="ed">{exp}</span><span class="vl">عرض ←</span></div>
  </div>
</a>\n"""

    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>عروض البنوك السعودية</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-H8RW3B0YM5"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-H8RW3B0YM5');
</script>
<style>
:root {{{bank_css}
  --bg:#F4F6F9;--sf:#FFFFFF;--cd:#FFFFFF;--br:rgba(0,0,0,.08);
  --tx:#1A1A2E;--mt:#6B7280;--hn:#E8ECF0;
  --gn:#16A34A;--gn-bg:rgba(22,163,74,.08);
  --rd:#DC2626;--rd-bg:rgba(220,38,38,.06);--rd-br:rgba(220,38,38,.2);
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Cairo',sans-serif;background:var(--bg);color:var(--tx);min-height:100vh}}

.tb{{background:var(--sf);border-bottom:1px solid var(--br);padding:1.25rem 2rem;display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:1rem;position:sticky;top:0;z-index:100}}
.bi{{width:36px;height:36px;background:linear-gradient(135deg,var(--rajhi),var(--inma));border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px}}
.bn{{font-size:1.4rem;font-weight:700;text-align:center;width:100%}}
.bs{{font-size:.75rem;color:var(--mt)}}
.tm{{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center}}
.pl{{font-size:.75rem;font-weight:600;padding:.25rem .75rem;border-radius:20px;white-space:nowrap}}
.pl-c{{background:rgba(255,255,255,.08);color:var(--tx);border:1px solid var(--br)}}
.pl-ok{{background:var(--gn-bg);color:var(--gn);border:1px solid rgba(61,190,110,.25)}}
.pl-er{{background:var(--rd-bg);color:var(--rd);border:1px solid var(--rd-br)}}

.stb{{display:none}}
.si{{display:none}}
.sd{{display:none}}

.ct{{max-width:1400px;margin:1.5rem auto 0;padding:0 2rem;display:flex;flex-direction:column;gap:.75rem;align-items:center}}
.cl{{font-size:.75rem;color:var(--mt)}}
.fg{{display:flex;gap:.4rem;flex-wrap:wrap;justify-content:center}}
.sp{{width:1px;height:24px;background:var(--br);flex-shrink:0}}
.fb{{font-family:'Cairo',sans-serif;font-size:.78rem;font-weight:500;padding:.3rem .85rem;border-radius:20px;border:1px solid var(--br);background:transparent;color:var(--mt);cursor:pointer;transition:all .18s;white-space:nowrap}}
.bc{{font-size:.7rem;opacity:.7;font-weight:400}}
.search-bar{{position:relative;width:100%;margin-bottom:.5rem}}
.search-bar input{{font-family:'Cairo',sans-serif;font-size:.95rem;background:var(--sf);border:1.5px solid var(--br);color:var(--tx);padding:.6rem 1rem;border-radius:12px;outline:none;width:100%;transition:border-color .2s;box-shadow:0 1px 4px rgba(0,0,0,.06);text-align:center}}
.search-bar input:focus{{border-color:#4A90D9}}
.search-bar input::placeholder{{color:var(--mt)}}

.hero{{background:var(--sf);border-bottom:1px solid var(--br);padding:2.5rem 2rem}}
.hero-inner{{max-width:700px;margin:0 auto;text-align:center}}
.search-big{{position:relative;margin-bottom:.75rem}}
.search-big input{{font-family:'Cairo',sans-serif;width:100%;font-size:1.1rem;padding:.9rem 1.25rem .9rem 3rem;border-radius:14px;border:2px solid var(--br);background:var(--bg);color:var(--tx);outline:none;transition:border-color .2s,box-shadow .2s}}
.search-big input:focus{{border-color:rgba(0,0,0,.25);box-shadow:0 4px 20px rgba(0,0,0,.08)}}
.search-big input::placeholder{{color:var(--mt)}}
.search-big-icon{{position:absolute;right:1rem;top:50%;transform:translateY(-50%);font-size:1.2rem;pointer-events:none}}
.rc-hero{{font-size:.85rem;color:var(--mt)}}
.fb:hover{{background:var(--hn);color:var(--tx)}}
.fb.active{{color:var(--tx);border-color:rgba(255,255,255,.3);background:var(--hn)}}














.sw{{margin-right:auto;position:relative}}
.sw input{{font-family:'Cairo',sans-serif;font-size:.82rem;background:var(--sf);border:1px solid var(--br);color:var(--tx);padding:.35rem .85rem .35rem 2rem;border-radius:20px;outline:none;width:200px}}
.sw input::placeholder{{color:var(--mt)}}
.si-icon{{position:absolute;left:.65rem;top:50%;transform:translateY(-50%);color:var(--mt);font-size:.85rem;pointer-events:none}}

.gw{{max-width:1400px;margin:1.25rem auto 0;padding:0 2rem 3rem}}
.rc{{font-size:.78rem;color:var(--mt);margin-bottom:1rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:1rem}}

.card{{background:var(--cd);border:1px solid var(--br);border-radius:14px;overflow:hidden;display:flex;flex-direction:column;transition:transform .2s,border-color .2s,box-shadow .2s;text-decoration:none;color:inherit}}
.card:hover{{transform:translateY(-4px);border-color:rgba(0,0,0,.15);box-shadow:0 12px 40px rgba(0,0,0,.1)}}
.ci{{position:relative;height:130px;background:var(--sf);display:flex;align-items:center;justify-content:center;overflow:hidden;border-bottom:1px solid var(--br)}}
.ci img{{width:100%;height:100%;object-fit:cover;transition:transform .3s;position:absolute}}
.card:hover .ci img{{transform:scale(1.04)}}
.cf{{font-size:2rem;opacity:.15}}
.bb{{font-size:.68rem;font-weight:700;padding:.15rem .5rem;border-radius:20px;display:inline-block;background:#F0F2F5;color:#4B5563;border:1px solid #D1D5DB}}















.cb{{padding:.85rem 1rem;flex:1;display:flex;flex-direction:column;gap:5px}}
.sn{{font-size:.92rem;font-weight:700;color:var(--tx);line-height:1.3}}
.cn{{font-size:.73rem;color:var(--mt)}}
.card-meta{{display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;margin-top:2px}}
.disc-tag{{font-size:.68rem;font-weight:700;padding:.15rem .5rem;border-radius:20px;background:var(--gn-bg);color:var(--gn);border:1px solid rgba(22,163,74,.25)}}
.ft{{display:flex;justify-content:space-between;align-items:center;margin-top:auto;padding-top:.6rem;border-top:1px solid var(--br)}}
.ed{{font-size:.7rem;color:var(--mt)}}
.vl{{font-size:.7rem;color:var(--mt);opacity:.6}}

.empty{{grid-column:1/-1;text-align:center;padding:4rem 2rem;color:var(--mt)}}

@media(max-width:700px){{
  .tb,.ct,.gw{{padding-right:.75rem;padding-left:.75rem}}
  .stb{{padding:.6rem .75rem}}
  .grid{{grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:.6rem}}
  .cb{{padding:.65rem .75rem}}
  .sn{{font-size:.85rem}}
  .ci{{height:110px}}
  .bn{{font-size:1rem}}
  .search-bar input{{font-size:.88rem}}
}}
</style>
</head>
<body>

<div class="tb">
  <div style="text-align:center;width:100%">
    <div class="bn">عروض البنوك السعودية</div>
    <div class="bs">آخر تحديث: {now}</div>
  </div>
  <div class="tm">
    <span class="pl pl-c">{total} عرض</span>
    <span class="pl {'pl-ok' if ok_count == len(BANKS) else 'pl-er'}">{ok_count}/{len(BANKS)} بنك</span>
  </div>
</div>

<div class="stb">{status_html}</div>

<div class="ct">
  <div class="search-bar">
    <input type="text" id="q" placeholder="ابحث عن متجر..." oninput="fil()">
  </div>
  <div class="fg">{bank_btns}</div>
</div>

<div class="gw">
  <div class="rc" id="rc" style="display:none">{total} عرض</div>
  <div class="grid" id="grid">{cards}</div>
</div>

<script>
let aB='all';
function setBank(b,btn){{aB=b;document.querySelectorAll('.ct .fb').forEach(x=>x.classList.remove('active'));btn.classList.add('active');fil();}}
function fuzzyMatch(text,query){{
  if(!query)return true;
  text=text.toLowerCase();query=query.toLowerCase();
  if(text.includes(query))return true;
  let qi=0;
  for(let i=0;i<text.length&&qi<query.length;i++){{if(text[i]===query[qi])qi++;}}
  return qi===query.length;
}}
function fil(){{
  const q=document.getElementById('q').value.trim();
  let n=0;
  document.querySelectorAll('.card').forEach(c=>{{
    const sn=c.querySelector('.sn')?.textContent||'';
    const cn=c.querySelector('.cn')?.textContent||'';
    const ok=(aB==='all'||c.dataset.bank===aB)&&(!q||fuzzyMatch(sn,q)||fuzzyMatch(cn,q));
    c.style.display=ok?'':'none';
    if(ok)n++;
  }});
  document.getElementById('rc').textContent=n+' عرض';
  const hero=document.getElementById('rc-hero');
  if(hero)hero.textContent=n+' عرض متاح';
}}
</script>
</body>
</html>"""

# ────────────────────────────────────────────
def main():
    print(f"\n📦 جاري بناء index.html من البيانات المحفوظة...")

    all_offers = []
    bank_status = {}

    for bank in BANKS:
        data = load_json(bank["json"])
        if data:
            for o in data:
                o["_bank"] = bank["id"]
                o["_bankName"] = bank["name"]
            # فلتر المنتهية
            active = [o for o in data if not is_expired(o)]
            expired_count = len(data) - len(active)
            all_offers.extend(active)
            bank_status[bank["id"]] = {"ok": True, "count": len(active)}
            print(f"  ✅ {bank['name']}: {len(active)} عرض نشط (تم حذف {expired_count} منتهي)")
        else:
            bank_status[bank["id"]] = {"ok": False, "count": 0}
            print(f"  ❌ {bank['name']}: ملف JSON غير موجود — شغّل update_all.py أولاً")

    html = build_index(all_offers, bank_status)
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  ✅ تم تحديث index.html — {len(all_offers)} عرض")
    print(f"  افتحه مباشرة في المتصفح")

if __name__ == "__main__":
    main()
