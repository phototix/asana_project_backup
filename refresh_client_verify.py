#!/usr/bin/env python3
"""Refresh the Client verification page.

Merges all current Client to verify tickets into the existing page, preserves
closed history, updates live status/assignee/change/next action, and adds new
tickets. No Asana writes.
"""

import html
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from string import Template

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_uat_tickets import load_env, api_request, ENV_PATH
from generate_report import render_preprod_cell

SGT = timezone(timedelta(hours=8))
PAGE = Path(__file__).resolve().parent / "reports-data" / "client-verify.html"
TOKEN = load_env(ENV_PATH)["ASANA_TOKEN"]
SECTION_GID = "1212426681919491"

NEW_PATHS = {
    "1219730158203178": ["/join-us/career"],
    "1219730215265066": ["/join-us/career"],
    "1219729872643659": ["/join-us/bright-youth"],
    "1219573809552366": ["/", "/contact-us"],
    "1219477239250114": ["/activities"],
    "1219575486816225": ["/awaken-online/digital"],
    "1219575481392590": ["/awaken-online/digital"],
    "1219575604575951": ["/awaken-online/digital"],
    "1219575656937178": ["/awaken-online/digital"],
    "1219584601884997": ["/contact-us"],
    "1219584909565579": ["/contact-us"],
    "1219584776062295": ["/contact-us"],
}

CHECKS = {
    "1219730158203178": {
        "result": "Content action",
        "evidence": "Expected Walk-In Interview copy and schedule not found in the server-rendered page. Update the content in the CMS and verify.",
        "action": "Update the CMS content and verify.",
    },
    "1219730215265066": {
        "result": "Content action",
        "evidence": "Expected How to Apply copy not found in the server-rendered page. Update the content in the CMS and verify.",
        "action": "Update the CMS content and verify.",
    },
    "1219729872643659": {
        "result": "Content action",
        "evidence": "Expected Four Pillars header/intro not found in the server-rendered page. Update the remaining content in the CMS and verify.",
        "action": "Update the CMS content and verify.",
    },
    "1219477239250114": {
        "result": "Needs manual review",
        "evidence": "CMS UI check required; the front end cannot confirm the edit icon.",
        "action": "Brandon to check manually; update Dexter only if a defect is found.",
    },
    "1219575481392590": {
        "result": "Pass",
        "evidence": "Found “Digital Content” on /awaken-online/digital and “数位资源” on /zh/awaken-online/digital.",
        "action": "Pass; Dexter to confirm and close.",
    },
    "1219575604575951": {
        "result": "Needs manual review",
        "evidence": "CMS field limit/title check required; not verified from the pre-prod page.",
        "action": "Brandon to check manually; update Dexter only if a defect is found.",
    },
    "1219575656937178": {
        "result": "Needs manual review",
        "evidence": "Audio player check required on a digital post; not verified from the listing page.",
        "action": "Brandon to check manually; update Dexter only if a defect is found.",
    },
    "1219575486816225": {
        "result": "Fail",
        "evidence": "Neither “Featured” nor “精选” was found on /awaken-online/digital.",
        "action": "Dexter to update the Featured label and verify.",
    },
    "1219584776062295": {
        "result": "Needs manual review",
        "evidence": "Submission failure test must be checked manually.",
        "action": "Brandon to check manually; update Dexter only if a defect is found.",
    },
    "1219584601884997": {
        "result": "Needs manual review",
        "evidence": "Internal labels are absent, but the new enquiry categories still need confirmation.",
        "action": "Brandon to check manually; update Dexter only if a defect is found.",
    },
    "1219584909565579": {
        "result": "Needs manual review",
        "evidence": "Form submission and mailbox delivery must be checked manually.",
        "action": "Brandon to check manually; update Dexter only if a defect is found.",
    },
    "1219573809552366": {
        "result": "Fail",
        "evidence": "Only the Facebook link was found. Instagram, YouTube, LinkedIn, WhatsApp and Xiaohongshu are missing.",
        "action": "Dexter to update the social links and verify.",
    },
}


def badge_for(result):
    cls = {"Pass": "pass", "Fail": "fail", "Needs manual review": "review", "Content action": "content"}.get(result, "review")
    return f'<span class="badge {cls}">{html.escape(result)}</span>'


def ticket_label(result):
    return "Automated check" if result in ("Pass", "Fail") else result


def relabel_ticket(ticket, label):
    return re.sub(
        r'<div class="small">[^<]*</div>',
        f'<div class="small">{html.escape(label)}</div>',
        ticket,
        count=1,
    )


def section_of(task):
    return next(
        (m.get("section", {}).get("name", "") for m in task.get("memberships", []) if (m.get("section") or {}).get("name")),
        "Unsectioned",
    )


def live_state(gid):
    task = api_request(
        TOKEN,
        "GET",
        f"/tasks/{gid}",
        params={"opt_fields": "name,assignee.name,memberships.section.name,completed"},
    ).get("data", {})
    section = section_of(task)
    assignee = (task.get("assignee") or {}).get("name") or "-"
    if task.get("completed") or section == "Closed":
        return "Closed", assignee, task.get("name") or ""
    if section == "Client to verify":
        return "Client to verify", assignee, task.get("name") or ""
    return section or "Other", assignee, task.get("name") or ""


def latest_comment(gid):
    stories = api_request(
        TOKEN,
        "GET",
        f"/tasks/{gid}/stories",
        params={"limit": 100, "opt_fields": "created_at,resource_subtype,type,created_by.name,text"},
    ).get("data", [])
    comments = sorted(
        [s for s in stories if s.get("resource_subtype") == "comment_added" or s.get("type") == "comment"],
        key=lambda s: s.get("created_at", ""),
    )
    if not comments:
        return '<div class="small">No comments</div>'
    last = comments[-1]
    who = (last.get("created_by") or {}).get("name") or "?"
    when = (last.get("created_at") or "")[:16]
    text = (last.get("text") or "").replace("\n", " ").strip()[:400]
    return f'<div class="small">{html.escape(who)} · {html.escape(when)}</div><div class="evidence">{html.escape(text)}</div>'


def next_action(live, assignee, result):
    if live == "Closed":
        return "None; closed."
    if live == "Client to verify":
        if assignee == "Dexter":
            return "Dexter to confirm the technical approach; follow up."
        if result == "Pass":
            return "Verify on pre-prod and close if pass."
        if result == "Needs manual review":
            return "Review on pre-prod and close if pass."
        if result == "Content action":
            return "Complete the content action and verify."
        return "Verify on pre-prod and close if pass."
    return "Review and follow up."


def main():
    old = PAGE.read_text(encoding="utf-8")
    style = re.search(r"<style>(.*?)</style>", old, re.S)
    style_text = style.group(1) if style else ""
    if "min-width:1800px" not in style_text:
        style_text += """
table{min-width:1800px}
.change.added{color:var(--content)}
"""

    existing = {}
    for attrs, body in re.findall(r'<tr ([^>]*data-result="[^"]+"[^>]*)>(.*?)</tr>', old, re.S):
        rm = re.search(r'data-result="([^"]+)"', attrs)
        if not rm:
            continue
        result = rm.group(1)
        pm = re.search(r'data-live="([^"]+)"', attrs)
        prior_live = pm.group(1) if pm else "Client to verify"
        cells = re.findall(r"<td[^>]*>(.*?)</td>", body, re.S)
        if len(cells) >= 10:
            ticket, asana, codigo, preprod, result_cell, evidence = cells[0], cells[1], cells[5], cells[6], cells[7], cells[8]
        elif len(cells) >= 9:
            ticket, asana, codigo, preprod, result_cell, evidence = cells[0], cells[1], cells[4], cells[5], cells[6], cells[7]
        elif len(cells) >= 7:
            ticket, asana, codigo, preprod, result_cell, evidence = cells[0], cells[1], cells[3], cells[4], cells[5], cells[6]
        else:
            continue
        gm = re.search(r"/task/(\d+)", asana)
        if not gm:
            continue
        gid = gm.group(1)
        nm = re.search(r'<div class="ticket-name">(.*?)</div>', ticket, re.S)
        name = re.sub(r"<[^>]+>", "", nm.group(1)).strip() if nm else gid
        existing[gid] = {
            "result": result,
            "prior_live": prior_live,
            "ticket": ticket,
            "asana": asana,
            "codigo": codigo,
            "preprod": preprod,
            "result_cell": result_cell,
            "evidence": evidence,
            "name": html.unescape(name),
        }

    current = []
    offset = None
    while True:
        params = {"limit": 100, "opt_fields": "name,assignee.name"}
        if offset:
            params["offset"] = offset
        payload = api_request(TOKEN, "GET", f"/sections/{SECTION_GID}/tasks", params=params)
        current += payload.get("data", [])
        offset = (payload.get("next_page") or {}).get("offset")
        if not offset:
            break

    built = []
    live_counts = Counter()
    result_counts = Counter()
    assignee_counts = Counter()

    for gid, item in existing.items():
        live, assignee, _ = live_state(gid)
        check = CHECKS.get(gid)
        if check:
            result = check["result"]
            ticket = relabel_ticket(item["ticket"], ticket_label(result))
            result_cell = badge_for(result)
            evidence = check["evidence"]
            action = "None; closed." if live == "Closed" else check["action"]
            if live == "Closed":
                change = "Closed since last run" if item["prior_live"] != "Closed" else "No change"
            else:
                change = "Added to Client to verify"
        else:
            result = item["result"]
            ticket = item["ticket"]
            result_cell = item["result_cell"]
            evidence = item["evidence"]
            if live == "Closed":
                change = "Closed since last run" if item["prior_live"] != "Closed" else "No change"
            elif live == "Client to verify":
                change = "No change" if item["prior_live"] in ("Client to verify", "With Dexter") else "Moved to Client to verify"
            else:
                change = "No change"
            action = next_action(live, assignee, result)
        built.append({
            "gid": gid, "name": item["name"], "live": live, "assignee": assignee,
            "change": change, "result": result, "ticket": ticket, "asana": item["asana"],
            "codigo": item["codigo"], "preprod": item["preprod"], "result_cell": result_cell,
            "evidence": evidence, "action": action,
        })
        live_counts[live] += 1
        result_counts[result] += 1
        assignee_counts[(live, assignee)] += 1

    for task in current:
        gid = task["gid"]
        if gid in existing:
            continue
        live, assignee, name = live_state(gid)
        if not name:
            name = task.get("name") or gid
        check = CHECKS.get(gid)
        if check:
            result = check["result"]
            change = "Added to Client to verify" if live != "Closed" else "No change"
            action = "None; closed." if live == "Closed" else check["action"]
            ticket_small = ticket_label(result)
            result_cell = badge_for(result)
            evidence = check["evidence"]
        else:
            result = "Not yet checked"
            change = "Added to Client to verify"
            action = next_action("Client to verify", assignee, result)
            ticket_small = "Not yet checked"
            result_cell = '<span class="badge review">Not yet checked</span>'
            evidence = "No automated check yet; added from the live Client to verify queue."
        paths = NEW_PATHS.get(gid, [])
        preprod = render_preprod_cell(" and ".join(paths)) if paths else '<span class="small">No frontend page</span>'
        built.append({
            "gid": gid, "name": name, "live": live, "assignee": assignee,
            "change": change, "result": result,
            "ticket": f'<div class="ticket-name">{html.escape(name)}</div><div class="small">{html.escape(ticket_small)}</div>',
            "asana": f'<a class="ticket-link" href="https://app.asana.com/1/1610754927873/project/1212423157941626/task/{gid}" target="_blank" rel="noopener noreferrer">Open ticket</a><div class="small">{gid}</div>',
            "codigo": latest_comment(gid),
            "preprod": preprod,
            "result_cell": result_cell,
            "evidence": evidence,
            "action": action,
        })
        live_counts[live] += 1
        result_counts[result] += 1
        assignee_counts[(live, assignee)] += 1

    live_order = {"Client to verify": 0, "Closed": 1}
    assignee_order = {"Brandon": 0, "Dexter": 1}
    built.sort(key=lambda r: (live_order.get(r["live"], 2), assignee_order.get(r["assignee"], 2), r["name"].lower()))

    rows = []
    for r in built:
        live_class = {"Closed": "pass", "Client to verify": "review"}.get(r["live"], "fail" if r["live"].startswith("Fail") else "review")
        change_class = {"Closed since last run": "closed", "Added to Client to verify": "added", "No change": "none"}.get(r["change"], "none")
        rows.append(
            "<tr data-live=\"{live}\" data-assignee=\"{assignee}\" data-change=\"{change}\" data-result=\"{result}\">"
            "<td>{ticket}</td><td>{asana}</td>"
            "<td><span class=\"badge {live_class}\">{live_text}</span></td>"
            "<td>{assignee_text}</td>"
            "<td><span class=\"change {change_class}\">{change_text}</span></td>"
            "<td>{codigo}</td><td>{preprod}</td><td>{result_cell}</td><td>{evidence}</td>"
            "<td><div class=\"evidence\">{action}</div></td></tr>".format(
                live=html.escape(r["live"], quote=True),
                assignee=html.escape(r["assignee"], quote=True),
                change=html.escape(r["change"], quote=True),
                result=html.escape(r["result"], quote=True),
                ticket=r["ticket"], asana=r["asana"],
                live_class=live_class, live_text=html.escape(r["live"]),
                assignee_text=html.escape(r["assignee"]),
                change_class=change_class, change_text=html.escape(r["change"]),
                codigo=r["codigo"], preprod=r["preprod"],
                result_cell=r["result_cell"], evidence=r["evidence"],
                action=html.escape(r["action"]),
            )
        )

    live_options = "".join(
        f'<option value="{html.escape(v, quote=True)}">{html.escape(v)}</option>'
        for v in ["Client to verify", "Closed"] + [v for v in live_counts if v not in ("Client to verify", "Closed")]
        if live_counts.get(v)
    )
    assignee_options = "".join(
        f'<option value="{html.escape(v, quote=True)}">{html.escape(v)}</option>'
        for v in ["Brandon", "Dexter"] if any(k[1] == v for k in assignee_counts)
    )
    change_options = "".join(
        f'<option value="{html.escape(v, quote=True)}">{html.escape(v)}</option>'
        for v in ["Closed since last run", "Added to Client to verify", "No change"]
        if any(r["change"] == v for r in built)
    )
    result_options = "".join(
        f'<option value="{html.escape(v, quote=True)}">{html.escape(v)}</option>'
        for v in ["Pass", "Fail", "Needs manual review", "Content action", "Not yet checked"] if result_counts.get(v)
    )

    cb = assignee_counts.get(("Client to verify", "Brandon"), 0)
    cd = assignee_counts.get(("Client to verify", "Dexter"), 0)
    added_count = sum(1 for r in built if r["change"] == "Added to Client to verify")
    unchecked = result_counts.get("Not yet checked", 0)
    now = datetime.now(SGT)
    extra_cards = "".join(
        f'<div class="card"><div class="num">{count}</div><div class="label">{html.escape(live)}</div></div>'
        for live, count in live_counts.items()
        if live not in ("Client to verify", "Closed") and count
    )
    cards = f"""<div class="card"><div class="num">{len(built)}</div><div class="label">Total</div></div>
<div class="card"><div class="num">{live_counts.get("Closed",0)}</div><div class="label">Closed</div></div>
<div class="card"><div class="num">{cb}</div><div class="label">Client to verify — Brandon</div></div>
<div class="card"><div class="num">{cd}</div><div class="label">Client to verify — Dexter</div></div>{extra_cards}"""
    added_line = (
        f"Added this run: {added_count} added, {unchecked} not yet checked."
        if unchecked
        else f"Added this run: {added_count} checked."
    )
    summary_line = (
        f'<p class="small">Last automated pass: Pass {result_counts.get("Pass",0)} · '
        f'Fail {result_counts.get("Fail",0)} · '
        f'Needs manual review {result_counts.get("Needs manual review",0)} · '
        f'Content action {result_counts.get("Content action",0)}. '
        f'{added_line}</p>'
    )
    if unchecked:
        note = (
            f"Live status refreshed from Asana on {now.strftime('%d %b %Y, %I:%M %p')} SGT. "
            f"{added_count} Client to verify tickets were added; {unchecked} are not yet checked. "
            "No Asana data was changed."
        )
    else:
        note = (
            f"Live status refreshed from Asana on {now.strftime('%d %b %Y, %I:%M %p')} SGT. "
            f"Automated pre-checks completed for the {added_count} added rows; items marked Needs manual review still need a human check. "
            "No Asana data was changed."
        )

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Client verification — Client to verify</title>
<meta name="report-title" content="Client verification — Client to verify">
<meta name="report-date" content="{now.strftime('%Y-%m-%dT%H:%M:%S+08:00')}">
<meta name="report-summary" content="{len(built)} tickets: {live_counts.get('Closed',0)} closed, {cb} client to verify (Brandon), {cd} client to verify (Dexter).">
<style>{style_text}</style>
</head>
<body>
<div class="page">
<header class="top">
  <div>
    <div class="brand">KMSPKS UAT</div>
    <h1>Client verification</h1>
    <div class="meta">Client to verify · {live_counts.get("Client to verify",0)} in queue ({cb} Brandon, {cd} Dexter) · status refreshed {now.strftime('%d %b %Y, %I:%M %p')} SGT</div>
  </div>
  <nav class="nav">
    <a class="btn" href="/reports/">Reports</a>
    <a class="btn" href="/reports/cms-managed.html">CMS</a>
    <a class="btn" href="/">Backups</a>
    <a class="btn" href="/logout">Logout</a>
  </nav>
</header>

<div class="note">{note}</div>

<div class="cards">{cards}</div>
{summary_line}

<div class="filters">
  <input id="search" type="search" placeholder="Search ticket, comment or evidence..." oninput="applyFilters()">
  <select id="liveFilter" onchange="applyFilters()"><option value="">All live statuses</option>{live_options}</select>
  <select id="assigneeFilter" onchange="applyFilters()"><option value="">All assignees</option>{assignee_options}</select>
  <select id="changeFilter" onchange="applyFilters()"><option value="">All changes</option>{change_options}</select>
  <select id="resultFilter" onchange="applyFilters()"><option value="">All automated results</option>{result_options}</select>
  <button class="btn" type="button" onclick="window.print()">Print</button>
</div>

<div class="table-wrap">
<table id="verifyTable">
<thead><tr><th>Ticket</th><th>Asana</th><th>Live status</th><th>Assignee</th><th>Change</th><th>Codigo update</th><th>Pre-prod page</th><th>Last automated result</th><th>Evidence</th><th>Next action</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</div>

<footer>Live status refresh from Asana. Review before closing any ticket.</footer>
</div>
<script>
function applyFilters(){{
  const q=(document.getElementById('search').value||'').toLowerCase();
  const live=document.getElementById('liveFilter').value;
  const assignee=document.getElementById('assigneeFilter').value;
  const change=document.getElementById('changeFilter').value;
  const result=document.getElementById('resultFilter').value;
  document.querySelectorAll('#verifyTable tbody tr').forEach(function(tr){{
    const text=(tr.innerText||'').toLowerCase();
    const ok=(!q||text.indexOf(q)!==-1)
      &&(!live||tr.getAttribute('data-live')===live)
      &&(!assignee||tr.getAttribute('data-assignee')===assignee)
      &&(!change||tr.getAttribute('data-change')===change)
      &&(!result||tr.getAttribute('data-result')===result);
    tr.style.display=ok?'':'none';
  }});
}}
</script>
</body>
</html>
"""
    PAGE.write_text(document, encoding="utf-8")
    print(PAGE)
    print("TOTAL", len(built), "LIVE", dict(live_counts), "ASSIGNEE", {f"{k[0]}/{k[1]}": v for k, v in assignee_counts.items()}, "RESULT", dict(result_counts))


if __name__ == "__main__":
    main()
