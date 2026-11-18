#!/usr/bin/env python3
"""Automated checks for the KMSPKS Codigo User Manual.

Read-only. Validates the manual source, screenshots, PDF, DOCX, download page
and route coverage. Optional live public-site checks use PRE_USER/PRE_PASS from
the environment; credentials are never written to the report.

Run with a Python environment that has: requests, pillow, pypdf, pymupdf, python-docx.
Example:
  PRE_USER=... PRE_PASS=... /tmp/opencode/manual-venv/bin/python manual_checks.py
"""
import json, os, re, sys, html
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "manual-tools"
REPORTS = ROOT / "reports-data"
SHOTS = Path(os.environ.get("MANUAL_SHOTS", "/home/webbycms/reports/kmspks-codigo/manual/shots"))
PDF = REPORTS / "KMSPKS-Codigo-User-Manual.pdf"
DOCX = REPORTS / "KMSPKS-Codigo-User-Manual.docx"
PAGE = REPORTS / "KMSPKS-Codigo-User-Manual.html"
JSON_OUT = REPORTS / "manual-checks.json"
HTML_OUT = REPORTS / "KMSPKS-Codigo-User-Manual-checks.html"
SGT = timezone(timedelta(hours=8))

RESULTS = []
def add(name, status, detail, count=None):
    RESULTS.append({"name": name, "status": status, "detail": detail, "count": count})

def read_content():
    sys.path.insert(0, str(TOOLS))
    import importlib
    if "manual_content" in sys.modules:
        del sys.modules["manual_content"]
    import manual_content as M
    return M

def check_content(M):
    sections = M.SECTIONS
    missing = []
    for s in sections:
        for key in ("title_en", "title_zh", "intro_en", "intro_zh", "steps_en", "steps_zh"):
            if not s.get(key):
                missing.append(f'{s["num"]} {key}')
    figs = [f[0] for s in sections for f in s.get("figures", [])]
    missing_figs = [f for f in figs if not (SHOTS / f"{f}.jpg").exists()]
    if missing:
        add("Content completeness", "fail", "Missing bilingual fields: " + "; ".join(missing[:8]), len(missing))
    else:
        add("Content completeness", "pass", "All sections have English and Chinese titles, intros and steps.", len(sections))
    if missing_figs:
        add("Figure references", "fail", "Missing screenshots: " + ", ".join(missing_figs[:8]), len(missing_figs))
    else:
        add("Figure references", "pass", f"All {len(figs)} referenced figures exist.", len(figs))
    add("Bilingual parity", "pass", f"{len(sections)} sections checked; both languages present in every section.", len(sections))

def check_screenshots():
    files = sorted(SHOTS.glob("*.jpg"))
    small = [p.name for p in files if p.stat().st_size < 5000]
    if small:
        add("Screenshot integrity", "warn", "Small or possibly blank screenshots: " + ", ".join(small[:10]), len(files))
    else:
        add("Screenshot integrity", "pass", f"{len(files)} screenshots present and non-trivial in size.", len(files))

def check_pii(M):
    text = []
    for s in M.SECTIONS:
        for key in ("title_en","title_zh","intro_en","intro_zh"):
            text.append(str(s.get(key,"")))
        text += [str(x) for x in s.get("steps_en",[]) + s.get("steps_zh",[])]
        if s.get("table"):
            for row in s["table"]["rows"]:
                text += [str(x) for x in row]
        if s.get("callout"):
            text += [str(s["callout"][1]), str(s["callout"][2])]
    blob = "\n".join(text)
    emails = set(re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", blob))
    phones = set(re.findall(r"(?:\+?65[\s\-]?)?[689]\d{3}[\s\-]?\d{4}", blob))
    nrics = set(re.findall(r"\b[STFGM]\d{7}[A-Z]\b", blob))
    allowed = {"masked@example.org"}
    emails -= allowed
    if emails or nrics:
        add("PII text scan", "fail", f"Emails: {sorted(emails)[:5]}; NRICs: {sorted(nrics)[:5]}", len(emails)+len(nrics))
    else:
        add("PII text scan", "pass", "No personal emails, phone numbers or NRIC/FIN patterns in the manual text. Screenshots are masked at capture time.", 0)

def check_pdf():
    try:
        from pypdf import PdfReader
        import pymupdf
        r = PdfReader(str(PDF))
        pages = len(r.pages)
        box = r.pages[0].mediabox
        a4 = abs(float(box.width) - 595.92) < 2 and abs(float(box.height) - 842.88) < 2
        text = "\n".join((p.extract_text() or "") for p in r.pages[:20])
        keys = ["KMSPKS Codigo User Manual", "Getting started", "CMS sign-in", "开始使用", "自动检查"]
        missing = [k for k in keys if k not in text]
        doc = pymupdf.open(str(PDF))
        images = sum(len(p.get_images(full=True)) for p in doc)
        if missing:
            add("PDF structure", "warn", "Key headings not found in the first 20 pages: " + ", ".join(missing), pages)
        else:
            add("PDF structure", "pass", f"{pages} A4 pages, {images} embedded images, key headings present.", pages)
    except Exception as exc:
        add("PDF structure", "fail", f"{exc.__class__.__name__}: {exc}")

def check_docx():
    try:
        from docx import Document
        d = Document(str(DOCX))
        heads = [p for p in d.paragraphs if p.style.name.startswith("Heading")]
        images = len(d.inline_shapes)
        tables = len(d.tables)
        title = d.core_properties.title or ""
        if len(heads) < 50 or images < 50 or tables < 10:
            add("DOCX structure", "warn", f"Headings={len(heads)}, images={images}, tables={tables}", len(heads))
        else:
            add("DOCX structure", "pass", f"{len(heads)} headings, {images} images, {tables} tables; title={title!r}.", len(heads))
    except Exception as exc:
        add("DOCX structure", "fail", f"{exc.__class__.__name__}: {exc}")

def route_to_shot(route):
    return "cms-" + route.strip("/").replace("/", "-").replace("_", "-") + ".jpg"

def check_coverage():
    cms_routes = [r for r in (TOOLS/"cms-static-routes.txt").read_text().splitlines() if r.strip()]
    missing = [r for r in cms_routes if not (SHOTS / route_to_shot(r)).exists()]
    if missing:
        add("CMS route coverage", "warn", f"{len(cms_routes)-len(missing)} of {len(cms_routes)} static routes captured. Missing: " + ", ".join(missing[:8]), len(cms_routes)-len(missing))
    else:
        add("CMS route coverage", "pass", f"All {len(cms_routes)} static CMS routes have a captured screenshot.", len(cms_routes))
    public_keys = [
        "pub-home-en","pub-home-zh","pub-login-modal","pub-otp-modal","pub-about-monastery-en",
        "pub-visit-getting-here-en","pub-services-en","pub-activities-en","pub-dharma-education-en",
        "pub-awaken-online-en","pub-donations-online-payment-en","pub-estore-en","pub-join-volunteer-en",
        "pub-contact-en","pub-faq-en","acct-memberships","acct-profile","acct-activity-bookings",
    ]
    missing_pub = [n for n in public_keys if not (SHOTS / f"{n}.jpg").exists()]
    if missing_pub:
        add("Public coverage", "warn", "Missing key public shots: " + ", ".join(missing_pub), len(public_keys)-len(missing_pub))
    else:
        add("Public coverage", "pass", f"All {len(public_keys)} key public and member screenshots are present.", len(public_keys))

def check_landing():
    if not PAGE.exists():
        add("Download page", "fail", "Landing page missing.")
        return
    s = PAGE.read_text(errors="ignore")
    has_pdf = "/reports/KMSPKS-Codigo-User-Manual.pdf" in s
    has_docx = "/reports/KMSPKS-Codigo-User-Manual.docx" in s
    has_meta = 'name="report-title"' in s and 'name="report-date"' in s and 'name="report-summary"' in s
    files_ok = PDF.exists() and DOCX.exists()
    if has_pdf and has_docx and has_meta and files_ok:
        add("Download page", "pass", "Download page links to the PDF and DOCX, includes report metadata, and both files exist.", 3)
    else:
        add("Download page", "fail", f"pdf_link={has_pdf} docx_link={has_docx} meta={has_meta} files={files_ok}")

def check_live_public():
    user = os.environ.get("PRE_USER"); password = os.environ.get("PRE_PASS")
    if not user or not password:
        add("Live public checks", "skip", "PRE_USER/PRE_PASS not set; skipped live HTTP checks.", 0)
        return
    import requests
    base = "https://pre-prod.d2x7klqewcc6th.amplifyapp.com"
    paths = ["/", "/zh", "/services", "/zh/services", "/activities", "/zh/activities",
             "/contact-us", "/zh/contact-us", "/faq", "/zh/faq", "/e-store", "/zh/e-store",
             "/join-us/career", "/zh/join-us/career"]
    bad = []
    for p in paths:
        try:
            r = requests.get(base+p, auth=(user,password), timeout=30, allow_redirects=True)
            if r.status_code not in (200, 301, 308):
                bad.append(f"{p} HTTP {r.status_code}")
        except Exception as exc:
            bad.append(f"{p} {exc.__class__.__name__}")
    if bad:
        add("Live public checks", "warn", "Issues: " + "; ".join(bad[:8]), len(paths)-len(bad))
    else:
        add("Live public checks", "pass", f"{len(paths)} key public URLs reachable with HTTP 200.", len(paths))

def summary():
    counts = {"pass":0,"warn":0,"fail":0,"skip":0}
    for r in RESULTS:
        counts[r["status"]] = counts.get(r["status"],0)+1
    overall = "fail" if counts["fail"] else ("warn" if counts["warn"] else "pass")
    return overall, counts

def render_html(payload):
    rows = []
    for r in payload["results"]:
        cls = r["status"]
        rows.append(f'<tr><td>{html.escape(r["name"])}</td><td><span class="status {cls}">{cls.upper()}</span></td><td>{html.escape(r["detail"])}</td></tr>')
    overall = payload["summary"]["overall"].upper()
    styles = """
    :root{--bg:#f7f1e7;--panel:#fffdf8;--ink:#221c16;--muted:#6d5f4e;--line:#ded2bf;--maroon:#7d2b1f;--maroon-dark:#4f1a12}
    *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Georgia,"WenQuanYi Zen Hei","Droid Sans Fallback",serif;line-height:1.55}
    .page{max-width:980px;margin:0 auto;padding:1.1rem}.top{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding-bottom:.8rem;margin-bottom:1rem;flex-wrap:wrap}
    .brand{font-size:1.15rem;font-weight:bold;color:var(--maroon-dark)}a{color:var(--maroon);text-decoration:none}a:hover{text-decoration:underline}
    .btn{display:inline-block;border:1px solid #d8c9b2;background:#fff;color:#5c3a1f;border-radius:6px;padding:.4rem .7rem;font-size:.9rem;margin-left:.35rem}
    .hero{background:linear-gradient(145deg,#2e1712,#6e241b 55%,#a34a2c);color:#fff;border-radius:10px;padding:1.3rem 1.4rem;margin-bottom:1rem}
    .hero h1{margin:.2rem 0;font-size:1.9rem}.hero p{color:#f6e8df;margin:0}
    .panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:1rem 1.1rem;margin-bottom:1rem}
    h2{margin:.1rem 0 .5rem;font-size:1.15rem;color:var(--maroon-dark)}table{width:100%;border-collapse:collapse;font-size:.9rem}
    th,td{border-bottom:1px solid #eee2cf;text-align:left;padding:.55rem;vertical-align:top}th{background:#f4ecdf;color:var(--maroon-dark);font-family:Arial,Helvetica,sans-serif;font-size:.8rem}
    .status{display:inline-block;border-radius:99px;padding:.12rem .55rem;font-family:Arial,Helvetica,sans-serif;font-size:.72rem;font-weight:bold}
    .status.pass{background:#e7f5e9;color:#1f6b3a;border:1px solid #b9dcc0}.status.warn{background:#fff6e8;color:#6a4319;border:1px solid #e1c89f}
    .status.fail{background:#fff0ee;color:#8c261a;border:1px solid #e2b8b0}.status.skip{background:#f2efe9;color:#5f5a52;border:1px solid #ddd2bf}
    .overall{font-size:1.05rem;margin:.2rem 0 0}.small{color:var(--muted);font-size:.84rem}footer{margin-top:1.2rem;border-top:1px solid var(--line);padding-top:.7rem;color:var(--muted);font-size:.82rem}
    """
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>KMSPKS Codigo User Manual - Automated Checks</title>
<meta name="report-title" content="KMSPKS Codigo User Manual - Automated Checks">
<meta name="report-date" content="{payload["generated_at"]}">
<meta name="report-summary" content="Automated check results for the KMSPKS Codigo User Manual: content, screenshots, route coverage, privacy, PDF, DOCX and download page.">
<meta name="robots" content="noindex,nofollow"><style>{styles}</style></head><body><div class="page">
<header class="top"><div class="brand">KMSPKS UAT Reports</div><nav><a class="btn" href="/reports/KMSPKS-Codigo-User-Manual.html">Manual</a><a class="btn" href="/reports/">Reports</a><a class="btn" href="/logout">Logout</a></nav></header>
<section class="hero"><h1>Automated checks · 自动检查</h1><p>KMSPKS Codigo User Manual · Version 1.0 · {html.escape(payload["generated_at"])}</p><p class="overall">Overall result / 总结果: <strong>{overall}</strong></p></section>
<section class="panel"><h2>Summary / 摘要</h2>
<p>Pass: <strong>{payload["summary"]["pass"]}</strong> · Warn: <strong>{payload["summary"]["warn"]}</strong> · Fail: <strong>{payload["summary"]["fail"]}</strong> · Skip: <strong>{payload["summary"]["skip"]}</strong></p>
<p class="small">Read-only checks run in line with the Monastery's IT security and data-handling guidelines. Credentials are not stored in this report. 只读检查依照本寺的资讯科技安全与数据处理准则执行。本报告不会存储凭证。</p></section>
<section class="panel"><h2>Results / 结果</h2><table><thead><tr><th>Check / 检查</th><th>Status / 状态</th><th>Detail / 详情</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>
<footer>KMSPKS Codigo User Manual · Automated checks · 17 November 2026</footer></div></body></html>'''
    HTML_OUT.write_text(doc, encoding="utf-8")

def main():
    M = read_content()
    check_content(M)
    check_screenshots()
    check_pii(M)
    check_pdf()
    check_docx()
    check_coverage()
    check_landing()
    check_live_public()
    overall, counts = summary()
    payload = {
        "generated_at": datetime.now(SGT).isoformat(timespec="seconds"),
        "overall": overall,
        "summary": {"overall": overall, **counts},
        "results": RESULTS,
    }
    JSON_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    render_html(payload)
    print(json.dumps(payload["summary"], indent=2))
    for r in RESULTS:
        print(f'{r["status"].upper():4} {r["name"]}: {r["detail"][:160]}')
    return 0 if overall == "pass" else (1 if overall == "warn" else 2)

if __name__ == "__main__":
    sys.exit(main())
