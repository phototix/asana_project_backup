#!/usr/bin/env python3
"""Generate the CMS-managed issues tracker.

The tracker is a static HTML page stored in reports-data/ and served by
index.php behind the existing login. It reads live status from Asana but does
not change any Asana data.
"""

import html
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from string import Template

sys.path.insert(0, str(Path(__file__).resolve().parent))

from create_uat_tickets import load_env, api_request, ENV_PATH
from generate_report import render_preprod_cell

PROJECT_TASK_URL = "https://app.asana.com/1/1610754927873/project/1212423157941626/task/{gid}"
SGT = timezone(timedelta(hours=8))

ITEMS = [
    {
        "gid": "1219730214216446",
        "group": "Confirmed CMS-managed",
        "key": "confirmed",
        "feedback": "Zin: the Bright Youth intro is CMS-managed. Please update the EN/CN copy in the CMS.",
        "action": "Update the Bright Youth intro EN/CN copy in the CMS and verify on pre-prod.",
        "paths": ["/join-us/bright-youth"],
    },
    {
        "gid": "1219573809552366",
        "group": "Confirmed CMS-managed",
        "key": "confirmed",
        "feedback": "Zin: the social media links can be updated in the CMS.",
        "action": "Update the LinkedIn, WhatsApp and Xiaohongshu links in the CMS and verify.",
        "paths": ["/", "/contact-us"],
    },
    {
        "gid": "1219584601884997",
        "group": "CMS content blocked or guidance needed",
        "key": "blocked",
        "feedback": "Dexter: change the labels in Contact Management > Contact Us > Subject Master Data. A CMS access error was reported.",
        "action": "Fix CMS access, update the enquiry category labels and verify.",
        "paths": ["/contact-us"],
    },
    {
        "gid": "1219584933906424",
        "group": "CMS content blocked or guidance needed",
        "key": "blocked",
        "feedback": "Ticket: Contact Us CMS error. Department contact content is incomplete.",
        "action": "Fix the Contact Us CMS error, update department names, descriptions, phone and email, then verify.",
        "paths": ["/contact-us"],
    },
    {
        "gid": "1219477239416627",
        "group": "CMS content blocked or guidance needed",
        "key": "blocked",
        "feedback": "Ticket: the CMS description has a 500-character limit. Images are not required for now.",
        "action": "Remove the 500-character limit, update the description and verify.",
        "paths": [],
    },
    {
        "gid": "1219526058649071",
        "group": "CMS content blocked or guidance needed",
        "key": "blocked",
        "feedback": "Zin: only the title and description of two locations can be edited. The CMS path is unclear.",
        "action": "Confirm the CMS path, update the title and description, and standardise the Dharma School content.",
        "paths": ["/dharma-education/school/location"],
    },
    {
        "gid": "1219575656532229",
        "group": "CMS display or editor issue",
        "key": "display",
        "feedback": "Zin: paragraph breaks entered in the CMS are not reflected on the website. The page is gone after the CMS update.",
        "action": "Fix the CMS paragraph rendering and page loading, then verify.",
        "paths": ["/awaken-online/articles"],
    },
    {
        "gid": "1219570600171995",
        "group": "CMS display or editor issue",
        "key": "display",
        "feedback": "Zin: paragraph spacing from the CMS is missing. The Terms and Conditions CMS editor shows an application error.",
        "action": "Fix the CMS paragraph spacing and the Terms and Conditions editor, then verify all three pages.",
        "paths": ["/privacy-policy", "/terms-and-conditions", "/whistleblower-policy"],
    },
    {
        "gid": "1219575486359563",
        "group": "CMS display or editor issue",
        "key": "display",
        "feedback": "Zin: the publish date is missing from the CMS listing and detail view for publications.",
        "action": "Fix or verify the publish date field in the CMS and on pre-prod.",
        "paths": ["/awaken-online/books"],
    },
    {
        "gid": "1219575656344472",
        "group": "CMS display or editor issue",
        "key": "display",
        "feedback": "Zin: the publish date column is not visible in the CMS listing for Awaken Magazine.",
        "action": "Fix or verify the publish date column and field.",
        "paths": ["/awaken-online/magazines"],
    },
    {
        "gid": "1219692039810792",
        "group": "CMS display or editor issue",
        "key": "display",
        "feedback": "Zin: the product Chinese name is saved in the CMS but the storefront shows English. Backend may be involved.",
        "action": "Fix the CMS-to-storefront display and verify the Chinese locale.",
        "paths": ["/e-store", "/zh/e-store"],
    },
    {
        "gid": "1213988637581792",
        "group": "CMS status to confirm",
        "key": "confirm",
        "feedback": "Zin: confirm whether the Dharma School banner and hover-menu images are hardcoded or CMS-managed. The CMS paths show no editable landing form.",
        "action": "Confirm the CMS status, provide the required image sizes and update the images.",
        "paths": ["/dharma-education/school/an-overview"],
    },
]

GROUP_ORDER = [
    "Confirmed CMS-managed",
    "CMS content blocked or guidance needed",
    "CMS display or editor issue",
    "CMS status to confirm",
]
GROUP_CLASS = {
    "Confirmed CMS-managed": "confirmed",
    "CMS content blocked or guidance needed": "blocked",
    "CMS display or editor issue": "display",
    "CMS status to confirm": "confirm",
}

PAGE = Template("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CMS-managed issues — quick tracker</title>
<meta name="report-title" content="CMS-managed issues — quick tracker">
<meta name="report-date" content="$date_iso">
<meta name="report-summary" content="12 CMS-related items: 2 confirmed, 4 blocked or guidance, 5 display or editor issues, 1 status to confirm.">
<style>
:root{--bg:#f7f4ee;--panel:#fffdf8;--ink:#1f1a12;--muted:#6d5f4e;--line:#ddd2bf;--accent:#7d2b1f;--pass:#24522a;--passbg:#f0f7ee;--fail:#8c261a;--failbg:#fff0ee;--review:#6a4319;--reviewbg:#fff6e8;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Georgia,"Times New Roman",serif;line-height:1.5}
.page{max-width:1400px;margin:0 auto;padding:1.25rem}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;border-bottom:1px solid var(--line);padding-bottom:.8rem;margin-bottom:.9rem;flex-wrap:wrap}
.brand{font-size:.85rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
h1{font-size:1.6rem;margin:.15rem 0 .2rem}
.meta{color:var(--muted);font-size:.9rem}
.nav{display:flex;gap:.4rem;flex-wrap:wrap}
.btn{display:inline-block;border:1px solid #d8c9b2;background:#fff;color:#5c3a1f;border-radius:6px;padding:.38rem .65rem;text-decoration:none;font-size:.86rem;font-family:Arial,Helvetica,sans-serif;cursor:pointer}
.btn:hover{background:#f9f2e6;text-decoration:none}
.note{background:#fffdf8;border:1px solid var(--line);border-radius:8px;padding:.65rem .8rem;margin:.4rem 0 1rem;color:var(--muted);font-size:.9rem}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:.6rem;margin-bottom:1rem}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:.75rem .85rem}
.card .num{font-size:1.5rem;line-height:1;margin-bottom:.25rem}
.card .label{color:var(--muted);font-size:.85rem}
.filters{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin:.6rem 0 .8rem}
.filters input,.filters select{border:1px solid #d8c9b2;background:#fff;color:#3b2f1f;border-radius:6px;padding:.42rem .6rem;font-size:.9rem}
.filters input{min-width:250px}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:8px;background:var(--panel)}
table{width:100%;border-collapse:collapse;font-size:.88rem;min-width:1200px}
th,td{border-bottom:1px solid #eee2cf;padding:.55rem .6rem;text-align:left;vertical-align:top}
th{background:#f0e4d2;font-family:Arial,Helvetica,sans-serif;font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;position:sticky;top:0;z-index:1}
tr:last-child td{border-bottom:none}
.group-tag{display:inline-block;border-radius:999px;padding:.14rem .45rem;font-family:Arial,Helvetica,sans-serif;font-size:.75rem;font-weight:700;white-space:nowrap}
.group-tag.confirmed{background:var(--passbg);color:var(--pass);border:1px solid #bdd9b8}
.group-tag.blocked{background:var(--reviewbg);color:var(--review);border:1px solid #e1c89f}
.group-tag.display{background:var(--failbg);color:var(--fail);border:1px solid #e2b8b0}
.group-tag.confirm{background:#eef3f8;color:#274b6d;border:1px solid #b9cfe2}
.badge{display:inline-block;border-radius:999px;padding:.12rem .48rem;font-family:Arial,Helvetica,sans-serif;font-size:.75rem;font-weight:700;white-space:nowrap}
.badge.pass{background:var(--passbg);color:var(--pass);border:1px solid #bdd9b8}
.badge.fail{background:var(--failbg);color:var(--fail);border:1px solid #e2b8b0}
.badge.review{background:var(--reviewbg);color:var(--review);border:1px solid #e1c89f}
.ticket-name{font-weight:700;margin-bottom:.2rem}
.ticket-link{color:var(--accent);font-size:.85rem;text-decoration:none}
.ticket-link:hover{text-decoration:underline}
.preprod-path{color:var(--muted);font-family:Arial,Helvetica,sans-serif;font-size:.78rem;margin:0 0 .25rem;overflow-wrap:anywhere}
.btn-view{display:inline-block;border:1px solid #d8c9b2;background:#fff;color:#5c3a1f;border-radius:6px;padding:.25rem .5rem;font-family:Arial,Helvetica,sans-serif;font-size:.78rem;text-decoration:none;white-space:nowrap;margin:.1rem .25rem .1rem 0}
.btn-view:hover{background:#f9f2e6;text-decoration:none}
.muted{color:var(--muted)}
footer{margin-top:1.2rem;border-top:1px solid var(--line);padding-top:.7rem;color:var(--muted);font-size:.82rem}
@media print{
  body{background:#fff}
  .top,.nav,.filters,.note,footer,.btn-view,.ticket-link{display:none}
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
    <h1>CMS-managed issues</h1>
    <div class="meta">Quick tracker · Last updated $generated SGT</div>
  </div>
  <nav class="nav">
    <a class="btn" href="/reports/">Reports</a>
    <a class="btn" href="/">Backups</a>
    <a class="btn" href="/reports/cms-managed.html">Reload</a>
    <a class="btn" href="/logout">Logout</a>
  </nav>
</header>

<div class="note">CMS access is private. This tracker never stores CMS credentials. Use your saved CMS link to manage the content. The Asana and pre-prod links open in a new tab. This is a static snapshot; rerun the tracker generator to refresh the Asana status.</div>

<div class="cards">
$cards
</div>

<div class="filters">
  <input id="search" type="search" placeholder="Search ticket, feedback or action..." oninput="applyFilters()">
  <select id="groupFilter" onchange="applyFilters()">
    <option value="">All groups</option>
    $group_options
  </select>
  <select id="statusFilter" onchange="applyFilters()">
    <option value="">All statuses</option>
    $status_options
  </select>
  <button class="btn" type="button" onclick="window.print()">Print</button>
  <button class="btn" type="button" onclick="downloadCsv()">Download CSV</button>
</div>

<div class="table-wrap">
<table id="cmsTable">
<thead><tr><th>Group</th><th>Ticket</th><th>Feedback</th><th>What to manage</th><th>Status</th><th>Assignee</th><th>Requester</th><th>Pre-prod</th><th>Last updated</th></tr></thead>
<tbody>
$rows
</tbody>
</table>
</div>

<footer>CMS-managed tracker generated from live Asana data. No Asana data was changed.</footer>
</div>
<script>
function applyFilters(){
  const q=(document.getElementById('search').value||'').toLowerCase();
  const g=document.getElementById('groupFilter').value;
  const s=document.getElementById('statusFilter').value;
  document.querySelectorAll('#cmsTable tbody tr').forEach(function(tr){
    const text=(tr.innerText||'').toLowerCase();
    const ok=(!q||text.indexOf(q)!==-1)&&(!g||tr.getAttribute('data-group')===g)&&(!s||tr.getAttribute('data-status')===s);
    tr.style.display=ok?'':'none';
  });
}
function csvCell(value){
  return '"'+String(value||'').replace(/"/g,'""')+'"';
}
function downloadCsv(){
  const table=document.getElementById('cmsTable');
  const lines=[];
  const headers=Array.from(table.querySelectorAll('thead th')).map(function(th){return csvCell(th.innerText.trim());});
  lines.push(headers.join(','));
  table.querySelectorAll('tbody tr').forEach(function(tr){
    if(tr.style.display==='none') return;
    const cells=Array.from(tr.querySelectorAll('td')).map(function(td){return csvCell(td.innerText.trim());});
    if(cells.length) lines.push(cells.join(','));
  });
  const blob=new Blob([lines.join('\\n')],{type:'text/csv;charset=utf-8'});
  const link=document.createElement('a');
  link.href=URL.createObjectURL(blob);
  link.download='cms-managed.csv';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
}
</script>
</body>
</html>
""")


def is_client(user):
    name = (user.get("name") or "").strip()
    email = (user.get("email") or "").strip().lower()
    if email in ("brandonchong@kmspks.org", "ivanling@kmspks.org"):
        return False
    if email.endswith("codigo.co"):
        return False
    if name in ("Brandon", "Ivan Ling", "Dexter", "Kaung Myat Hein", "Zin Nhin", "Reeve Low", "Danh", "Harry"):
        return False
    return bool(email.endswith("kmspks.org") or name)


def status_badge(status):
    low = (status or "").lower()
    if low == "closed":
        css = "pass"
    elif low.startswith("fail"):
        css = "fail"
    else:
        css = "review"
    return f'<span class="badge {css}">{html.escape(status or "Unknown")}</span>'


def format_datetime(value):
    if not value:
        return "-"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(SGT)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return value


def main():
    token = load_env(ENV_PATH)["ASANA_TOKEN"]
    now = datetime.now(SGT)
    rows = []
    statuses = set()

    for item in ITEMS:
        task = api_request(
            token,
            "GET",
            f"/tasks/{item['gid']}",
            params={"opt_fields": "name,assignee.name,memberships.section.name,modified_at,followers.name,followers.email"},
        ).get("data", {})
        name = task.get("name") or item["gid"]
        section = next(
            (m.get("section", {}).get("name", "") for m in task.get("memberships", []) if (m.get("section") or {}).get("name")),
            "Unsectioned",
        )
        assignee = (task.get("assignee") or {}).get("name") or "-"
        requester_names = sorted(
            {
                (u.get("name") or u.get("email") or "").strip()
                for u in task.get("followers", [])
                if is_client(u)
            }
        )
        requester = ", ".join([n for n in requester_names if n]) or "-"
        statuses.add(section)
        preprod = render_preprod_cell(" and ".join(item["paths"])) if item["paths"] else '<span class="muted">CMS only</span>'
        rows.append(
            "<tr data-group=\"{key}\" data-status=\"{status}\">"
            "<td><span class=\"group-tag {group_class}\">{group}</span></td>"
            "<td><div class=\"ticket-name\">{name}</div><a class=\"ticket-link\" href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\">Open ticket</a></td>"
            "<td>{feedback}</td>"
            "<td>{action}</td>"
            "<td>{badge}</td>"
            "<td>{assignee}</td>"
            "<td>{requester}</td>"
            "<td>{preprod}</td>"
            "<td>{updated}</td>"
            "</tr>".format(
                key=html.escape(item["key"], quote=True),
                status=html.escape(section, quote=True),
                group_class=GROUP_CLASS[item["group"]],
                group=html.escape(item["group"]),
                name=html.escape(name),
                url=html.escape(PROJECT_TASK_URL.format(gid=item["gid"]), quote=True),
                feedback=html.escape(item["feedback"]),
                action=html.escape(item["action"]),
                badge=status_badge(section),
                assignee=html.escape(assignee),
                requester=html.escape(requester),
                preprod=preprod,
                updated=html.escape(format_datetime(task.get("modified_at", ""))),
            )
        )

    group_counts = {group: 0 for group in GROUP_ORDER}
    for item in ITEMS:
        group_counts[item["group"]] += 1

    cards = "".join(
        f'<div class="card"><div class="num">{group_counts[group]}</div><div class="label">{html.escape(group)}</div></div>'
        for group in GROUP_ORDER
    )
    group_options = "".join(
        f'<option value="{html.escape(GROUP_CLASS[group], quote=True)}">{html.escape(group)}</option>'
        for group in GROUP_ORDER
    )
    status_options = "".join(
        f'<option value="{html.escape(status, quote=True)}">{html.escape(status)}</option>'
        for status in sorted(statuses)
    )

    document = PAGE.substitute(
        date_iso=now.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        generated=now.strftime("%d %b %Y, %I:%M %p"),
        cards=cards,
        group_options=group_options,
        status_options=status_options,
        rows="\n".join(rows),
    )

    output = Path(__file__).resolve().parent / "reports-data" / "cms-managed.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
