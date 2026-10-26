#!/usr/bin/env python3
"""Generate the full UAT board report from the live-data snapshot.

Reads /tmp/opencode/uat_full_data.json (fetched from live Asana), applies the
requester and last-comment ownership rules, and writes a static HTML page in
reports-data/. No Asana data is changed.
"""

import html
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from string import Template

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_report import render_preprod_cell

SGT = timezone(timedelta(hours=8))
DATA = Path("/tmp/opencode/uat_full_data.json")
OUT = Path(__file__).resolve().parent / "reports-data" / "2026-10-25-1600-uat-full-report.html"

MARCOMM_VIA_BRANDON = {
    "1219575481392590",
    "1219575486874259",
    "1219575604575951",
    "1219575656937178",
}

MARCOMM = {
    "Chang Xiu Mei", "Si Hui", "Chloe See", "Ming Jie", "Lee Ming Jie",
    "Rui Ying", "ruiying@kmspks.org", "Carrlin Fong", "carrlinfong@kmspks.org",
}

SECTION_ORDER = [
    "To disscuss/confirm",
    "New Request on Pre-prod",
    "To update hardcoded content on Pre-prod",
    "Fix In Progress",
    "Fail (To fix again)",
    "QA to verify",
    "Client to verify",
]

PATHS = {
    "1219729871505000": ["/"],
    "1219729871681039": ["/"],
    "1219730038770916": ["/"],
    "1219729966737873": ["/"],
    "1219729884657529": ["/join-us/volunteer"],
    "1219730156544417": ["/join-us/volunteer"],
    "1219746446656349": ["/join-us/volunteer"],
    "1219730039233996": ["/join-us/volunteer"],
    "1219730213867125": ["/join-us/volunteer"],
    "1219729885418308": ["/join-us/volunteer"],
    "1219730157051326": ["/join-us/bright-youth"],
    "1219730214216446": ["/join-us/bright-youth"],
    "1219730214000918": ["/join-us/bright-youth"],
    "1219729872643659": ["/join-us/bright-youth"],
    "1219729872441193": ["/join-us/bright-youth"],
    "1219729885362231": ["/join-us/bright-youth"],
    "1219730040037065": ["/join-us/joyous-heart"],
    "1219730214602139": ["/join-us/joyous-heart"],
    "1219730157523754": ["/join-us/joyous-heart"],
    "1219730214327943": ["/join-us/joyous-heart"],
    "1219730040218133": ["/join-us/joyous-heart"],
    "1219730214723788": ["/join-us/career"],
    "1219729886373019": ["/join-us/career"],
    "1219729885998686": ["/join-us/career"],
    "1219730215265066": ["/join-us/career"],
    "1219730158203178": ["/join-us/career"],
    "1219730152343193": ["/join-us/career"],
    "1219730041124358": ["/join-us/career"],
    "1219573694440141": ["/"],
    "1219575486029162": ["/awaken-online/books"],
    "1219575536473541": ["/awaken-online/magazines"],
    "1219575604118790": ["/awaken-online/articles"],
    "1219575656367817": ["/awaken-online/digital"],
    "1219584612769805": ["/contact-us"],
    "1219575603219202": ["/awaken-online"],
    "1219570452486142": ["/contact-us"],
    "1219573938599764": ["/"],
    "1219526058649071": ["/dharma-education/school/location"],
    "1219573716472510": ["/"],
    "1219575604730061": ["/awaken-online/digital"],
    "1219573589963215": ["/"],
    "1219692039810792": ["/e-store", "/zh/e-store"],
    "1219584933906424": ["/contact-us"],
    "1219575656532229": ["/awaken-online/articles"],
    "1213988637581792": ["/dharma-education/school/an-overview"],
    "1219575481338668": ["/awaken-online/articles"],
    "1219575604552330": ["/awaken-online/digital"],
    "1219575656344472": ["/awaken-online/magazines"],
    "1219575486359563": ["/awaken-online/books"],
    "1219570600171995": ["/privacy-policy", "/terms-and-conditions", "/whistleblower-policy"],
    "1219575486141720": ["/awaken-online/books"],
    "1219575228008122": ["/awaken-online/books"],
    "1219575603604377": ["/awaken-online/books"],
    "1219575416943234": ["/awaken-online"],
    "1219575535926742": ["/awaken-online"],
    "1219575226602332": ["/awaken-online"],
    "1219570600171991": ["/contact-us"],
    "1219573809552366": ["/", "/contact-us"],
    "1219477239250114": ["/activities"],
    "1219575486816225": ["/awaken-online/digital"],
    "1219575481392590": ["/awaken-online/digital"],
    "1219575486874259": ["/awaken-online/digital"],
    "1219575604575951": ["/awaken-online/digital"],
    "1219575656937178": ["/awaken-online/digital"],
    "1219584601884997": ["/contact-us"],
    "1219584909565579": ["/contact-us"],
    "1219584776062295": ["/contact-us"],
    "1219804537175138": ["/dharma-education/school"],
}

OVERRIDES = {
    "1219566240500919": ("None; internal requirement.", "Confirm the audit-trail requirement with Codigo.", "Technical"),
    "1219804537175138": ("Confirm the missing course page with the Dharma School owner.", "Follow up with Codigo and the Dharma School owner.", "Comm"),
    "1219688580627862": ("None.", "Review the empty ticket and close or provide details.", "IT"),
    "1219729871505000": ("Confirm the banner layout and content.", "Resolve the scope and approach with Codigo.", "Comm"),
    "1219730039233996": ("Confirm the application process requirements.", "Get Codigo's approach and confirm the Figma.", "Comm"),
    "1219730213867125": ("Confirm the role list and expandable-list design.", "Get Codigo's approach and confirm the Figma.", "Comm"),
    "1219570452486114": ("Ming Jie to confirm the section placement.", "Reply to Codigo with the confirmed placement.", "Comm"),
    "1219573694440141": ("Confirm the removal and dynamic footer requirement.", "Reply to Codigo on the approach.", "Comm"),
    "1219575486029162": ("Provide the banner image and confirm the copy.", "Follow up with Marcomm and update Codigo.", "Comm"),
    "1219575536473541": ("Provide the banner image and confirm the copy.", "Follow up with Marcomm and update Codigo.", "Comm"),
    "1219575604118790": ("Provide the banner image and confirm the copy.", "Follow up with Marcomm and update Codigo.", "Comm"),
    "1219575656367817": ("Provide the banner image and confirm the copy.", "Follow up with Marcomm and update Codigo.", "Comm"),
    "1219584612769805": ("Provide the placement, condition, wording and policy link.", "Follow up with Marcomm and update Codigo.", "Comm"),
    "1219729872643659": ("Confirm the Four Pillars copy.", "Verify the update on pre-prod.", "IT"),
    "1219729886373019": ("Confirm the image and copy.", "Reply to Codigo on the image quality.", "Comm"),
    "1219730215265066": ("Confirm the How to Apply copy.", "Confirm Codigo has applied the content.", "Comm"),
    "1219730158203178": ("Confirm the Walk-In Interview copy.", "Confirm Codigo has applied the content.", "Comm"),
    "1219575603219202": ("Provide the charity mailing address and details.", "Follow up with Marcomm and update Codigo.", "Comm"),
    "1219570452486142": ("Provide the banner image.", "Follow up with Marcomm and update Codigo.", "Comm"),
    "1219570452486112": ("Carrlin to confirm the About and Visit content updates.", "Follow up with Marcomm and Codigo.", "Comm"),
    "1219573938599764": ("Confirm the subscription feedback requirement.", "Follow up with Codigo.", "Comm"),
    "1219526058649071": ("Confirm the Location content.", "Follow up with Codigo on the CMS path.", "Technical"),
    "1219477239416627": ("Confirm the no-limit/content requirement.", "Follow up with Codigo.", "Technical"),
    "1219573716472510": ("Confirm the approved copy.", "Chase Codigo for the fix.", "Technical"),
    "1219729885418308": ("Confirm the image asset.", "Chase Codigo for the fix.", "Technical"),
    "1219746446656349": ("Confirm the section copy and order.", "Chase Codigo for the fix.", "Technical"),
    "1219729884657529": ("Confirm the approved copy and button labels.", "Chase Codigo for the fix.", "Technical"),
    "1219730214602139": ("None.", "Chase Codigo for the fix.", "Technical"),
    "1219575604730061": ("None.", "Chase Codigo for the fix.", "Technical"),
    "1219692039810792": ("Confirm the Chinese product name content.", "Verify QA/staging and pre-prod.", "IT"),
    "1219636982479482": ("None.", "Follow up with Codigo on the staging blocker.", "Technical"),
    "1219387971268301": ("None.", "Follow up with Codigo on the staging blocker.", "Technical"),
    "1219566240500914": ("None.", "Follow up with Codigo on the staging blocker.", "Technical"),
    "1219584933906424": ("Update the Helpdesk content in the CMS.", "Follow up with Marcomm and verify.", "Comm"),
    "1219575656532229": ("Correct the EN title field and confirm the copy.", "Follow up with Marcomm/Rui Ying and Codigo.", "Comm"),
    "1213988637581792": ("Confirm the banner image and advise on the ticket.", "Decide whether a new ticket is needed and proceed.", "Comm"),
    "1219730040218133": ("Check the visual spacing.", "Verify on pre-prod and close if pass.", "IT"),
    "1219575481338668": ("Check the Ends On behaviour.", "Verify on pre-prod and close if pass.", "IT"),
    "1219575604552330": ("Check the download button.", "Verify on pre-prod and close if pass.", "IT"),
    "1219575656344472": ("Check the publish date in the CMS listing.", "Verify on pre-prod and close if pass.", "IT"),
    "1219575486359563": ("Check the publish date in the CMS listing.", "Verify on pre-prod and close if pass.", "IT"),
    "1219570600171995": ("Check the paragraph spacing and T&C editor.", "Verify on pre-prod and close if pass.", "IT"),
    "1219575486141720": ("Confirm the Publication tag content.", "Follow up with Codigo on the remaining tag issue.", "Technical"),
    "1219575228008122": ("Check the publication display.", "Verify on pre-prod and close if pass.", "IT"),
    "1219575603604377": ("Check the publication display.", "Verify on pre-prod and close if pass.", "IT"),
    "1219575416943234": ("Check the About Us content.", "Verify on pre-prod and close if pass.", "IT"),
    "1219575535926742": ("Check the About Us content.", "Verify on pre-prod and close if pass.", "IT"),
    "1219575226602332": ("Check the About Us banner.", "Verify on pre-prod and close if pass.", "IT"),
    "1219570600171991": ("Check the ceremony image is removed.", "Verify on pre-prod and close if pass.", "IT"),
    "1219573809552366": ("Update the social links in the CMS.", "Verify the links and close if pass.", "Comm"),
    "1219477239250114": ("Si Hui to confirm the UX/usability expectation.", "Follow up with Marcomm and Codigo.", "Comm"),
    "1219575486816225": ("Confirm the intended label.", "Follow up with Marcomm and Codigo.", "Comm"),
    "1219575481392590": ("Confirm the Digital Content label.", "Verify the label on pre-prod.", "Comm"),
    "1219575486874259": ("Confirm the 10-track configuration, video and order.", "Follow up with Codigo on the approach.", "Comm"),
    "1219575604575951": ("Confirm the 500-character fallback, lyrics and title removal.", "Follow up with Codigo.", "Comm"),
    "1219575656937178": ("Confirm the audio hosting and URL format.", "Follow up with Codigo.", "Comm"),
    "1219584601884997": ("Provide the final enquiry category labels.", "Fix CMS access and update the labels.", "Comm"),
    "1219584909565579": ("None.", "Follow up with Codigo on the pre-prod error.", "Technical"),
    "1219584776062295": ("None.", "Test the failure handling and follow up with Codigo.", "Technical"),
}


def requester_label(row):
    names = []
    for user in row.get("followers", []):
        name = (user.get("name") or "").strip()
        email = (user.get("email") or "").strip().lower()
        if "bee" in name.lower() or email == "beeneo@kmspks.org":
            names.append("Bee Neo (Dharma School)")
        elif name in MARCOMM or email in {m.lower() for m in MARCOMM if "@" in m}:
            names.append(f"{name or email} (Marcomm)")
        elif email.endswith("kmspks.org") and name not in ("Brandon", "Ivan Ling"):
            names.append(f"{name} (KMSPKS)")
    if not names:
        return "Brandon (IT Project Executive)"
    return ", ".join(sorted(set(names)))


def last_owner(row):
    gid = row["gid"]
    raw = row.get("last_author_type") or "None"
    if gid in MARCOMM_VIA_BRANDON:
        return "Marcomm (via Brandon)"
    if raw == "IT":
        return "IT (Brandon/Ivan)"
    if raw == "Codigo":
        return "Codigo"
    if raw == "Marcomm":
        return "Marcomm"
    if raw == "None":
        return "No comments"
    return "Unknown"


def default_action(row):
    section = row["section"]
    if section == "Client to verify":
        return "Check the page and confirm the content.", "Verify on pre-prod and close if pass.", "IT"
    if section == "QA to verify":
        return "None.", "Verify QA/staging and move to Client to verify or close.", "IT"
    if section == "Fail (To fix again)":
        return "Confirm the approved content if needed.", "Chase Codigo for the fix.", "Technical"
    if section == "Fix In Progress":
        return "Confirm the requirement if needed.", "Monitor Codigo and confirm the next update.", "Technical"
    if section == "New Request on Pre-prod":
        return "Confirm the content and requirements.", "Coordinate the approach with Codigo.", "Comm"
    if section == "To update hardcoded content on Pre-prod":
        return "Confirm the content.", "Confirm Codigo has applied the content.", "Comm"
    if section == "To disscuss/confirm":
        return "Join the discussion.", "Arrange and confirm the discussion.", "Comm"
    return "Review the ticket.", "Review and follow up.", "IT"


def action(row):
    return OVERRIDES.get(row["gid"], default_action(row))


def badge_class(owner):
    if owner.startswith("Marcomm"):
        return "marcomm"
    if owner.startswith("Codigo"):
        return "codigo"
    if owner.startswith("IT"):
        return "it"
    return "none"


def category_class(category):
    return {"Comm": "comm", "Technical": "tech", "IT": "it"}.get(category, "it")


PAGE = Template("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>25th October 2026 report</title>
<meta name="report-title" content="25th October 2026 report">
<meta name="report-date" content="$date_iso">
<meta name="report-summary" content="Full UAT board report: 75 tickets, progress, last-comment ownership and actions for Marcomm and Brandon.">
<style>
:root{--bg:#f7f4ee;--panel:#fffdf8;--ink:#1f1a12;--muted:#6d5f4e;--line:#ddd2bf;--accent:#7d2b1f;--pass:#24522a;--passbg:#f0f7ee;--fail:#8c261a;--failbg:#fff0ee;--review:#6a4319;--reviewbg:#fff6e8;--blue:#274b6d;--bluebg:#eef3f8;--grey:#5f5a52;--greybg:#f2efe9;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Georgia,"Times New Roman",serif;line-height:1.5}
.page{max-width:1700px;margin:0 auto;padding:1.25rem}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;border-bottom:1px solid var(--line);padding-bottom:.8rem;margin-bottom:.9rem;flex-wrap:wrap}
.brand{font-size:.82rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
h1{font-size:1.55rem;margin:.15rem 0 .2rem}
.meta{color:var(--muted);font-size:.9rem}
.nav{display:flex;gap:.4rem;flex-wrap:wrap}
.btn{display:inline-block;border:1px solid #d8c9b2;background:#fff;color:#5c3a1f;border-radius:6px;padding:.38rem .65rem;text-decoration:none;font-size:.86rem;font-family:Arial,Helvetica,sans-serif;cursor:pointer}
.btn:hover{background:#f9f2e6;text-decoration:none}
.note{background:#fffdf8;border:1px solid var(--line);border-radius:8px;padding:.65rem .8rem;margin:.4rem 0 1rem;color:var(--muted);font-size:.9rem}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.55rem;margin-bottom:.7rem}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:.65rem .75rem}
.card .num{font-size:1.35rem;line-height:1;margin-bottom:.2rem}
.card .label{color:var(--muted);font-size:.8rem}
.subhead{font-family:Arial,Helvetica,sans-serif;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:.7rem 0 .35rem}
.filters{display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin:.6rem 0 .8rem}
.filters input,.filters select{border:1px solid #d8c9b2;background:#fff;color:#3b2f1f;border-radius:6px;padding:.42rem .6rem;font-size:.88rem}
.filters input{min-width:240px}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:8px;background:var(--panel)}
table{width:100%;border-collapse:collapse;font-size:.85rem;min-width:1600px}
th,td{border-bottom:1px solid #eee2cf;padding:.52rem .55rem;text-align:left;vertical-align:top}
th{background:#f0e4d2;font-family:Arial,Helvetica,sans-serif;font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;position:sticky;top:0;z-index:1}
tr:last-child td{border-bottom:none}
.ticket-name{font-weight:700;margin-bottom:.18rem}
.ticket-link{color:var(--accent);font-size:.8rem;text-decoration:none}
.ticket-link:hover{text-decoration:underline}
.small{color:var(--muted);font-size:.76rem;overflow-wrap:anywhere}
.badge{display:inline-block;border-radius:999px;padding:.11rem .45rem;font-family:Arial,Helvetica,sans-serif;font-size:.72rem;font-weight:700;white-space:nowrap}
.badge.marcomm{background:var(--passbg);color:var(--pass);border:1px solid #bdd9b8}
.badge.codigo{background:var(--reviewbg);color:var(--review);border:1px solid #e1c89f}
.badge.it{background:var(--bluebg);color:var(--blue);border:1px solid #b9cfe2}
.badge.none{background:var(--greybg);color:var(--grey);border:1px solid #d8d3ca}
.cat-comm{background:var(--bluebg);color:var(--blue);border:1px solid #b9cfe2}
.cat-tech{background:var(--reviewbg);color:var(--review);border:1px solid #e1c89f}
.cat-it{background:var(--passbg);color:var(--pass);border:1px solid #bdd9b8}
.preprod-path{color:var(--muted);font-family:Arial,Helvetica,sans-serif;font-size:.76rem;margin:0 0 .22rem;overflow-wrap:anywhere}
.btn-view{display:inline-block;border:1px solid #d8c9b2;background:#fff;color:#5c3a1f;border-radius:6px;padding:.22rem .45rem;font-family:Arial,Helvetica,sans-serif;font-size:.75rem;text-decoration:none;white-space:nowrap;margin:.08rem .2rem .08rem 0}
.btn-view:hover{background:#f9f2e6;text-decoration:none}
.evidence{font-size:.8rem;color:#3d301f;overflow-wrap:anywhere}
footer{margin-top:1.2rem;border-top:1px solid var(--line);padding-top:.7rem;color:var(--muted);font-size:.82rem}
@media print{
  body{background:#fff}
  .top,.nav,.filters,.note,footer,.btn-view{display:none}
  .page{max-width:none;padding:0}
  .table-wrap{overflow:visible;border:0}
  table{min-width:0;font-size:.75rem}
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
    <h1>Full UAT board report</h1>
    <div class="meta">25th October 2026 · generated $generated SGT · read-only</div>
  </div>
  <nav class="nav">
    <a class="btn" href="/reports/">Reports</a>
    <a class="btn" href="/reports/cms-managed.html">CMS</a>
    <a class="btn" href="/reports/client-verify.html">Verify</a>
    <a class="btn" href="/">Backups</a>
    <a class="btn" href="/logout">Logout</a>
  </nav>
</header>

<div class="note">Read-only report. No Asana data was changed. Actions are suggested from the current section and the latest comment; review them before acting or closing tickets. Skipped sections: Closed, Invalid / Duplicate, Out of scope and To verify again.</div>

<div class="subhead">Tickets by section</div>
<div class="cards">$section_cards</div>

<div class="subhead">Latest comment ownership</div>
<div class="cards">$owner_cards</div>

<div class="filters">
  <input id="search" type="search" placeholder="Search ticket, requester, comment or action..." oninput="applyFilters()">
  <select id="sectionFilter" onchange="applyFilters()"><option value="">All sections</option>$section_options</select>
  <select id="requesterFilter" onchange="applyFilters()"><option value="">All requesters</option>$requester_options</select>
  <select id="ownerFilter" onchange="applyFilters()"><option value="">All last-comment owners</option>$owner_options</select>
  <select id="categoryFilter" onchange="applyFilters()"><option value="">All action owners</option>$category_options</select>
  <button class="btn" type="button" onclick="window.print()">Print</button>
</div>

<div class="table-wrap">
<table id="uatTable">
<thead><tr><th>Ticket</th><th>Section</th><th>Requester</th><th>Assignee</th><th>Last comment by</th><th>Last update</th><th>Progress / latest comment</th><th>Marcomm action</th><th>Your action</th><th>Pre-prod</th></tr></thead>
<tbody>
$rows
</tbody>
</table>
</div>

<footer>Full UAT board report generated from live Asana data. 75 tickets across the active sections. Read-only.</footer>
</div>
<script>
function applyFilters(){
  const q=(document.getElementById('search').value||'').toLowerCase();
  const section=document.getElementById('sectionFilter').value;
  const requester=document.getElementById('requesterFilter').value;
  const owner=document.getElementById('ownerFilter').value;
  const category=document.getElementById('categoryFilter').value;
  document.querySelectorAll('#uatTable tbody tr').forEach(function(tr){
    const text=(tr.innerText||'').toLowerCase();
    const ok=(!q||text.indexOf(q)!==-1)
      &&(!section||tr.getAttribute('data-section')===section)
      &&(!requester||tr.getAttribute('data-requester')===requester)
      &&(!owner||tr.getAttribute('data-owner')===owner)
      &&(!category||tr.getAttribute('data-category')===category);
    tr.style.display=ok?'':'none';
  });
}
</script>
</body>
</html>
""")


def main():
    rows = json.loads(DATA.read_text(encoding="utf-8"))
    rows.sort(key=lambda r: (SECTION_ORDER.index(r["section"]) if r["section"] in SECTION_ORDER else 99, (r["name"] or "").lower()))

    section_counts = Counter(r["section"] for r in rows)
    owner_counts = Counter(last_owner(r) for r in rows)

    section_cards = f'<div class="card"><div class="num">{len(rows)}</div><div class="label">Total tickets</div></div>'
    section_cards += "".join(
        f'<div class="card"><div class="num">{section_counts.get(s, 0)}</div><div class="label">{html.escape(s)}</div></div>'
        for s in SECTION_ORDER
    )
    owner_cards = "".join(
        f'<div class="card"><div class="num">{owner_counts.get(o, 0)}</div><div class="label">{html.escape(o)}</div></div>'
        for o in ["Codigo", "Marcomm (via Brandon)", "IT (Brandon/Ivan)", "No comments"]
    )

    section_options = "".join(
        f'<option value="{html.escape(s, quote=True)}">{html.escape(s)}</option>'
        for s in SECTION_ORDER if section_counts.get(s)
    )
    requester_values = sorted({requester_label(r) for r in rows})
    requester_options = "".join(
        f'<option value="{html.escape(v, quote=True)}">{html.escape(v)}</option>' for v in requester_values
    )
    owner_options = "".join(
        f'<option value="{html.escape(o, quote=True)}">{html.escape(o)}</option>'
        for o in ["Codigo", "Marcomm (via Brandon)", "IT (Brandon/Ivan)", "No comments"]
        if owner_counts.get(o)
    )
    category_counts = Counter(action(r)[2] for r in rows)
    category_options = "".join(
        f'<option value="{html.escape(c, quote=True)}">{html.escape(c)}</option>'
        for c in ["Comm", "Technical", "IT"] if category_counts.get(c)
    )

    out_rows = []
    for r in rows:
        owner = last_owner(r)
        marcomm_action, your_action, category = action(r)
        requester = requester_label(r)
        paths = PATHS.get(r["gid"], [])
        preprod = render_preprod_cell(" and ".join(paths)) if paths else '<span class="small">No frontend page</span>'
        text = (r.get("last_text") or "").replace("\n", " ").strip()
        if not text:
            text = "No comments."
        text = text[:420]
        url = f"https://app.asana.com/1/1610754927873/project/1212423157941626/task/{r['gid']}"
        out_rows.append(
            "<tr data-section=\"{section}\" data-requester=\"{requester_attr}\" data-owner=\"{owner_attr}\" data-category=\"{category_attr}\">"
            "<td><div class=\"ticket-name\">{name}</div><a class=\"ticket-link\" href=\"{url}\" target=\"_blank\" rel=\"noopener noreferrer\">Open ticket</a><div class=\"small\">{gid}</div></td>"
            "<td>{section_text}</td><td>{requester_text}</td><td>{assignee}</td>"
            "<td><span class=\"badge {owner_class}\">{owner}</span><div class=\"small\">{last_at}</div></td>"
            "<td>{last_at}</td>"
            "<td><div class=\"evidence\">{text}</div></td>"
            "<td><div class=\"evidence\">{marcomm_action}</div></td>"
            "<td><div class=\"evidence\">{your_action}</div><span class=\"badge {cat_class}\">{category}</span></td>"
            "<td>{preprod}</td></tr>".format(
                section=html.escape(r["section"], quote=True),
                requester_attr=html.escape(requester, quote=True),
                owner_attr=html.escape(owner, quote=True),
                category_attr=html.escape(category, quote=True),
                name=html.escape(r["name"] or "(untitled)"),
                url=html.escape(url, quote=True),
                gid=html.escape(r["gid"]),
                section_text=html.escape(r["section"]),
                requester_text=html.escape(requester),
                assignee=html.escape(r.get("assignee") or "-"),
                owner_class=badge_class(owner),
                owner=html.escape(owner),
                last_at=html.escape(r.get("last_at") or "-"),
                text=html.escape(text),
                marcomm_action=html.escape(marcomm_action),
                your_action=html.escape(your_action),
                cat_class=category_class(category),
                category=html.escape(category),
                preprod=preprod,
            )
        )

    now = datetime.now(SGT)
    document = PAGE.substitute(
        date_iso=now.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        generated=now.strftime("%d %b %Y, %I:%M %p"),
        section_cards=section_cards,
        owner_cards=owner_cards,
        section_options=section_options,
        requester_options=requester_options,
        owner_options=owner_options,
        category_options=category_options,
        rows="\n".join(out_rows),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(document, encoding="utf-8")
    print(OUT)
    print("TOTAL", len(rows), "SECTIONS", dict(section_counts), "OWNERS", dict(owner_counts), "ACTIONS", dict(category_counts))


if __name__ == "__main__":
    main()
