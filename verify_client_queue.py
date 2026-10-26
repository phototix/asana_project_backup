#!/usr/bin/env python3
"""One-round automated verification for the Client to verify queue.

Reads the Client to verify section from live Asana, keeps tickets assigned to
Brandon, runs static pre-prod checks, and writes a static HTML page for review.
No Asana data is changed.
"""

import html
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from string import Template

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

from create_uat_tickets import load_env, api_request, ENV_PATH
from generate_report import render_preprod_cell

PROJECT_TASK_URL = "https://app.asana.com/1/1610754927873/project/1212423157941626/task/{gid}"
PREPROD_BASE = "https://pre-prod.d2x7klqewcc6th.amplifyapp.com"
SGT = timezone(timedelta(hours=8))
SECTION_GID = "1212426681919491"
OUTPUT = Path(__file__).resolve().parent / "reports-data" / "client-verify.html"

CHECKS = {
    # Automated static checks
    "1219575485721204": {"category": "manual", "paths": ["/awaken-online"], "note": "The expected 'Awaken Publishing' header text was not found in the server-rendered visible text. Check the live Awaken Online page."},
    "1219573808950447": {"category": "automated", "paths": ["/contact-us"], "expected": ["88 Bright Hill Road, Singapore 574117"], "forbidden": ["88 Bright Hill Road Singapore 574117"]},
    "1219573938802132": {"category": "automated", "paths": ["/contact-us"], "link": "https://awarenessplace.com/"},
    "1219575536623130": {"category": "automated", "paths": ["/awaken-online/magazines"], "expected": ["New Releases"]},
    "1219575486562635": {"category": "automated", "paths": ["/awaken-online/articles"], "expected": ["Featured Articles"]},
    "1219575603657479": {"category": "automated", "paths": ["/awaken-online/books"], "expected": ["Publications"]},
    "1219575226896032": {"category": "automated", "paths": ["/awaken-online/books"], "expected": ["Recommended Publications"]},
    "1219575535926742": {"category": "automated", "paths": ["/awaken-online"], "expected": ["Read. Reflect. Grow."]},
    "1219575416943234": {"category": "automated", "paths": ["/awaken-online"], "expected": ["Latest Issues of the Awaken Magazine"]},
    "1219575227297229": {"category": "automated", "paths": ["/awaken-online"], "expected": ["Latest Publications"]},
    "1219575603344482": {"category": "automated", "paths": ["/awaken-online"], "expected": ["Latest Digital Content"]},
    "1219573590035450": {"category": "automated", "paths": ["/visit/getting-here"], "expected": ["Getting Here"], "forbidden": ["See all Gates"]},
    "1219573626459723": {"category": "automated", "paths": ["/"], "forbidden": ["Singapore Buddhist Free Clinic"]},
    "1219575485734167": {"category": "automated", "paths": ["/awaken-online"], "expected": ["Publications", "Digital Content", "Articles"]},
    "1219573694402884": {"category": "automated", "paths": ["/"], "expected": ["Affiliates"], "forbidden": ["Affilates"]},
    "1219573589097794": {"category": "automated", "paths": ["/contact-us"], "expected": ["Contact Us"], "forbidden": ["Contact us"]},
    "1219730214216446": {"category": "content", "paths": ["/join-us/bright-youth"], "note": "Content action: the Bright Youth intro is CMS-managed. The automated text check did not find the expected intro in the server HTML. Update the EN/CN copy in the CMS and verify."},
    # Visual or interaction checks
    "1213988637581792": {"category": "manual", "paths": ["/dharma-education/school/an-overview"], "note": "Visual banner check required."},
    "1219730040218133": {"category": "manual", "paths": ["/join-us/joyous-heart"], "note": "Visual footer spacing check required."},
    "1219575481338668": {"category": "manual", "paths": ["/awaken-online/articles"], "note": "Interaction check for the Ends On function required."},
    "1219575604552330": {"category": "manual", "paths": ["/awaken-online/digital"], "note": "Download interaction check required."},
    "1219575656344472": {"category": "manual", "paths": ["/awaken-online/magazines"], "note": "Check the publish date in the CMS listing and detail view."},
    "1219575486359563": {"category": "manual", "paths": ["/awaken-online/books"], "note": "Check the publish date in the CMS listing and detail view."},
    "1219570600171995": {"category": "manual", "paths": ["/privacy-policy", "/terms-and-conditions", "/whistleblower-policy"], "note": "Check paragraph spacing and the Terms and Conditions CMS editor."},
    "1219575228008122": {"category": "manual", "paths": ["/awaken-online/books"], "note": "Check featured and recommended sections for duplicates."},
    "1219575603604377": {"category": "manual", "paths": ["/awaken-online/books"], "note": "Check the breadcrumb and tag after upload."},
    "1219570600171991": {"category": "manual", "paths": ["/contact-us"], "note": "Check the ceremony photo is removed."},
    "1219575226602332": {"category": "manual", "paths": ["/awaken-online"], "note": "Check the About Us top banner no longer shows the Awaken Online text."},
    "1219575486141720": {"category": "manual", "paths": ["/awaken-online/books"], "note": "Check the publication card tags show Publication."},
    # Content actions
    "1219575656532229": {"category": "content", "paths": ["/awaken-online/articles"], "note": "Content action: the EN title field contains the Chinese title. Zin asks Brandon to correct and check it."},
    "1219584933906424": {"category": "content", "paths": ["/contact-us"], "note": "Content action: CMS access is restored. Update the Helpdesk department content."},
    "1219575486874259": {"category": "content", "paths": ["/awaken-online/digital"], "note": "Content action: pending Marcomm confirmation on multiple tracks."},
}

GROUP_LABEL = {
    "automated": "Automated check",
    "manual": "Needs manual review",
    "content": "Content action",
}
RESULT_CLASS = {
    "Pass": "pass",
    "Fail": "fail",
    "Needs manual review": "review",
    "Content action": "content",
}

PAGE = Template("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Client verification — Client to verify / Brandon</title>
<meta name="report-title" content="Client verification — Client to verify / Brandon">
<meta name="report-date" content="$date_iso">
<meta name="report-summary" content="Automated verification for the Client to verify queue assigned to Brandon.">
<style>
:root{--bg:#f7f4ee;--panel:#fffdf8;--ink:#1f1a12;--muted:#6d5f4e;--line:#ddd2bf;--accent:#7d2b1f;--pass:#24522a;--passbg:#f0f7ee;--fail:#8c261a;--failbg:#fff0ee;--review:#6a4319;--reviewbg:#fff6e8;--content:#274b6d;--contentbg:#eef3f8;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Georgia,"Times New Roman",serif;line-height:1.5}
.page{max-width:1500px;margin:0 auto;padding:1.25rem}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;border-bottom:1px solid var(--line);padding-bottom:.8rem;margin-bottom:.9rem;flex-wrap:wrap}
.brand{font-size:.85rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
h1{font-size:1.55rem;margin:.15rem 0 .2rem}
.meta{color:var(--muted);font-size:.9rem}
.nav{display:flex;gap:.4rem;flex-wrap:wrap}
.btn{display:inline-block;border:1px solid #d8c9b2;background:#fff;color:#5c3a1f;border-radius:6px;padding:.38rem .65rem;text-decoration:none;font-size:.86rem;font-family:Arial,Helvetica,sans-serif;cursor:pointer}
.btn:hover{background:#f9f2e6;text-decoration:none}
.note{background:#fffdf8;border:1px solid var(--line);border-radius:8px;padding:.65rem .8rem;margin:.4rem 0 1rem;color:var(--muted);font-size:.9rem}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.6rem;margin-bottom:1rem}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:.75rem .85rem}
.card .num{font-size:1.5rem;line-height:1;margin-bottom:.25rem}
.card .label{color:var(--muted);font-size:.85rem}
.filters{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin:.6rem 0 .8rem}
.filters input,.filters select{border:1px solid #d8c9b2;background:#fff;color:#3b2f1f;border-radius:6px;padding:.42rem .6rem;font-size:.9rem}
.filters input{min-width:260px}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:8px;background:var(--panel)}
table{width:100%;border-collapse:collapse;font-size:.87rem;min-width:1350px}
th,td{border-bottom:1px solid #eee2cf;padding:.55rem .6rem;text-align:left;vertical-align:top}
th{background:#f0e4d2;font-family:Arial,Helvetica,sans-serif;font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;position:sticky;top:0;z-index:1}
tr:last-child td{border-bottom:none}
.badge{display:inline-block;border-radius:999px;padding:.12rem .48rem;font-family:Arial,Helvetica,sans-serif;font-size:.75rem;font-weight:700;white-space:nowrap}
.badge.pass{background:var(--passbg);color:var(--pass);border:1px solid #bdd9b8}
.badge.fail{background:var(--failbg);color:var(--fail);border:1px solid #e2b8b0}
.badge.review{background:var(--reviewbg);color:var(--review);border:1px solid #e1c89f}
.badge.content{background:var(--contentbg);color:var(--content);border:1px solid #b9cfe2}
.ticket-name{font-weight:700;margin-bottom:.2rem}
.ticket-link{color:var(--accent);font-size:.84rem;text-decoration:none}
.ticket-link:hover{text-decoration:underline}
.small{color:var(--muted);font-size:.78rem;overflow-wrap:anywhere}
.evidence{font-size:.82rem;color:#3d301f;overflow-wrap:anywhere}
.preprod-path{color:var(--muted);font-family:Arial,Helvetica,sans-serif;font-size:.78rem;margin:0 0 .25rem;overflow-wrap:anywhere}
.btn-view{display:inline-block;border:1px solid #d8c9b2;background:#fff;color:#5c3a1f;border-radius:6px;padding:.25rem .5rem;font-family:Arial,Helvetica,sans-serif;font-size:.78rem;text-decoration:none;white-space:nowrap;margin:.1rem .25rem .1rem 0}
.btn-view:hover{background:#f9f2e6;text-decoration:none}
footer{margin-top:1.2rem;border-top:1px solid var(--line);padding-top:.7rem;color:var(--muted);font-size:.82rem}
@media print{
  body{background:#fff}
  .top,.nav,.filters,.note,footer,.btn-view{display:none}
  .page{max-width:none;padding:0}
  .table-wrap{overflow:visible;border:0}
  table{min-width:0;font-size:.8rem}
  th{position:static;background:#eee}
  tr{break-inside:avoid}
  .cards{grid-template-columns:repeat(4,1fr)}
}
</style>
</head>
<body>
<div class="page">
<header class="top">
  <div>
    <div class="brand">KMSPKS UAT</div>
    <h1>Client verification</h1>
    <div class="meta">Client to verify · assigned to Brandon · last run $generated SGT</div>
  </div>
  <nav class="nav">
    <a class="btn" href="/reports/">Reports</a>
    <a class="btn" href="/reports/cms-managed.html">CMS</a>
    <a class="btn" href="/">Backups</a>
    <a class="btn" href="/logout">Logout</a>
  </nav>
</header>

<div class="note">This is an automated first pass. No Asana data was changed and no tickets were closed. Review each ticket and the pre-prod page before closing. Pre-prod and CMS credentials are not stored in this page.</div>

<div class="cards">
$cards
</div>

<div class="filters">
  <input id="search" type="search" placeholder="Search ticket, evidence or Codigo update..." oninput="applyFilters()">
  <select id="resultFilter" onchange="applyFilters()">
    <option value="">All results</option>
    $result_options
  </select>
  <button class="btn" type="button" onclick="window.print()">Print</button>
</div>

<div class="table-wrap">
<table id="verifyTable">
<thead><tr><th>Ticket</th><th>Asana</th><th>Current status</th><th>Codigo update</th><th>Pre-prod page</th><th>Result</th><th>Evidence</th></tr></thead>
<tbody>
$rows
</tbody>
</table>
</div>

<footer>Generated from live Asana and authenticated pre-prod checks. Review before closing any ticket.</footer>
</div>
<script>
function applyFilters(){
  const q=(document.getElementById('search').value||'').toLowerCase();
  const r=document.getElementById('resultFilter').value;
  document.querySelectorAll('#verifyTable tbody tr').forEach(function(tr){
    const text=(tr.innerText||'').toLowerCase();
    const ok=(!q||text.indexOf(q)!==-1)&&(!r||tr.getAttribute('data-result')===r);
    tr.style.display=ok?'':'none';
  });
}
</script>
</body>
</html>
""")


def section(task):
    return next(
        (m.get("section", {}).get("name", "") for m in task.get("memberships", []) if (m.get("section") or {}).get("name")),
        "Unsectioned",
    )


def visible_text(value):
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.S | re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value)


def latest_comment(task_gid):
    stories = api_request(
        TOKEN,
        "GET",
        f"/tasks/{task_gid}/stories",
        params={"limit": 100, "opt_fields": "created_at,resource_subtype,type,created_by.name,text"},
    ).get("data", [])
    comments = sorted(
        [s for s in stories if s.get("resource_subtype") == "comment_added" or s.get("type") == "comment"],
        key=lambda s: s.get("created_at", ""),
    )
    if not comments:
        return "-", ""
    last = comments[-1]
    who = (last.get("created_by") or {}).get("name") or "?"
    when = (last.get("created_at", "") or "")[:16]
    text = (last.get("text") or "").replace("\n", " ").strip()
    return f"{who} · {when}", text[:220]


def automated_check(spec, session):
    failures = []
    passes = []
    for path in spec.get("paths", []):
        try:
            response = session.get(PREPROD_BASE + path, timeout=30, allow_redirects=True)
        except Exception as exc:
            failures.append(f"Request failed on {path}: {exc}")
            continue
        if response.status_code != 200:
            failures.append(f"HTTP {response.status_code} on {path}")
            continue
        raw = response.text
        text = visible_text(raw)
        for expected in spec.get("expected", []):
            if expected in text:
                passes.append(f"Found “{expected}” on {path}")
            else:
                failures.append(f"Missing “{expected}” on {path}")
        for forbidden in spec.get("forbidden", []):
            if forbidden in text:
                failures.append(f"Found “{forbidden}” on {path}")
            else:
                passes.append(f"“{forbidden}” is absent on {path}")
        if spec.get("link"):
            hrefs = re.findall(r'href="([^"]+)"', raw, flags=re.I)
            if spec["link"] in hrefs:
                passes.append(f"Link {spec['link']} found on {path}")
            else:
                failures.append(f"Link {spec['link']} missing on {path}")
    if failures:
        return "Fail", "; ".join(failures)[:700]
    return "Pass", "; ".join(passes)[:700]


def main():
    global TOKEN
    TOKEN = load_env(ENV_PATH)["ASANA_TOKEN"]
    pre_user = os.environ.get("PRE_USER", "").strip()
    pre_pass = os.environ.get("PRE_PASS", "").strip()
    if not pre_user or not pre_pass:
        raise SystemExit("Set PRE_USER and PRE_PASS for the pre-prod basic authentication.")

    session = requests.Session()
    session.auth = (pre_user, pre_pass)

    tasks = []
    offset = None
    while True:
        params = {"limit": 100, "opt_fields": "name,assignee.name"}
        if offset:
            params["offset"] = offset
        payload = api_request(TOKEN, "GET", f"/sections/{SECTION_GID}/tasks", params=params)
        tasks += payload.get("data", [])
        offset = (payload.get("next_page") or {}).get("offset")
        if not offset:
            break

    tasks = [t for t in tasks if (t.get("assignee") or {}).get("name") == "Brandon"]
    results = []
    for task in tasks:
        gid = task["gid"]
        name = task.get("name") or gid
        spec = CHECKS.get(gid, {"category": "manual", "paths": [], "note": "No automated check defined; review manually."})
        update, update_text = latest_comment(gid)

        if spec["category"] == "automated":
            result, evidence = automated_check(spec, session)
        elif spec["category"] == "content":
            result = "Content action"
            evidence = spec.get("note", "")
        else:
            result = "Needs manual review"
            evidence = spec.get("note", "")

        results.append({
            "gid": gid,
            "name": name,
            "status": "Client to verify",
            "update": update,
            "update_text": update_text,
            "paths": spec.get("paths", []),
            "result": result,
            "evidence": evidence,
        })

    order = {"Fail": 0, "Content action": 1, "Needs manual review": 2, "Pass": 3}
    results.sort(key=lambda row: (order.get(row["result"], 9), row["name"].lower()))

    counts = Counter(row["result"] for row in results)
    cards = "".join(
        f'<div class="card"><div class="num">{counts.get(label, 0)}</div><div class="label">{label}</div></div>'
        for label in ["Pass", "Fail", "Needs manual review", "Content action"]
    )

    result_options = "".join(
        f'<option value="{html.escape(label, quote=True)}">{label}</option>'
        for label in ["Fail", "Content action", "Needs manual review", "Pass"]
        if counts.get(label, 0)
    )

    rows = []
    for row in results:
        preprod = render_preprod_cell(" and ".join(row["paths"])) if row["paths"] else '<span class="small">No frontend page</span>'
        badge_class = RESULT_CLASS.get(row["result"], "review")
        url = PROJECT_TASK_URL.format(gid=row["gid"])
        rows.append(
            "<tr data-result=\"{result}\">"
            "<td><div class=\"ticket-name\">{name}</div><div class=\"small\">{group}</div></td>"
            "<td><a class=\"ticket-link\" href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\">Open ticket</a><div class=\"small\">{gid}</div></td>"
            "<td>Client to verify</td>"
            "<td><div class=\"small\">{update}</div><div class=\"evidence\">{update_text}</div></td>"
            "<td>{preprod}</td>"
            "<td><span class=\"badge {badge_class}\">{result}</span></td>"
            "<td><div class=\"evidence\">{evidence}</div></td>"
            "</tr>".format(
                result=html.escape(row["result"], quote=True),
                name=html.escape(row["name"]),
                group=html.escape(GROUP_LABEL.get(CHECKS.get(row["gid"], {}).get("category", "manual"), "Needs manual review")),
                url=html.escape(url, quote=True),
                gid=html.escape(row["gid"]),
                update=html.escape(row["update"]),
                update_text=html.escape(row["update_text"]),
                preprod=preprod,
                badge_class=badge_class,
                evidence=html.escape(row["evidence"]),
            )
        )

    now = datetime.now(SGT)
    document = PAGE.substitute(
        date_iso=now.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        generated=now.strftime("%d %b %Y, %I:%M %p"),
        cards=cards,
        result_options=result_options,
        rows="\n".join(rows),
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(document, encoding="utf-8")
    print(OUTPUT)
    print("TOTAL", len(results), "COUNTS", dict(counts))


if __name__ == "__main__":
    main()
