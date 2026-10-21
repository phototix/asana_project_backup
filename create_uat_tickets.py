#!/usr/bin/env python3
"""Create [KMS] Client UAT tickets in Asana from ticket sets.

Ticket sets:
  footer  - [Web] footer issues (collaborators: Ivan Ling + Chang Xiu Mei)
  awaken  - [Awaken Online] issues built from the client Excel workbook
            (collaborators: Ivan Ling + Rui Ying)

One Asana task is created per ticket. The script is idempotent: a ticket whose
title already exists in the project is skipped.

Usage:
    python3 create_uat_tickets.py --dry-run
    python3 create_uat_tickets.py --set awaken --dry-run
    python3 create_uat_tickets.py --set awaken
    python3 create_uat_tickets.py --only Footer-001
    python3 create_uat_tickets.py --sync-meta --only Footer-001 --only Footer-002
"""
import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


ENV_PATH = Path("/opt/asana-backup/.env")
API_BASE = "https://app.asana.com/api/1.0"
PROJECT_GID = "1212423157941626"
SECTION_GID = "1212423157941627"  # Open Tickets
PLATFORM_FIELD_GID = "1212440848488965"
PLATFORM_OPTION_GIDS = ["1218808894274450", "1218808894274451"]  # Website Desktop/Mobile Pre Prod
IVAN_GID = "1212427501742258"
XIU_MEI_GID = "1212427501814924"
RUI_YING_GID = "1214065465776719"
COLLABORATORS_BY_SET = {
    "footer": [IVAN_GID, XIU_MEI_GID],
    "awaken": [IVAN_GID, RUI_YING_GID],
    "contact": [IVAN_GID, XIU_MEI_GID],
}
AWAKEN_WORK_DIR = Path("/var/www/codigo.brandon.my/tmp/awaken")
CONTACT_WORK_DIR = Path("/var/www/codigo.brandon.my/tmp/contact")


def load_env(path: Path) -> dict:
    env = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        env[key] = value
    return env


def api_request(token: str, method: str, path: str, body=None, params=None, retries: int = 5):
    url = f"{API_BASE}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    data = json.dumps(body).encode("utf-8") if body is not None else None

    for attempt in range(retries):
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                time.sleep(int(exc.headers.get("Retry-After", "5")))
                continue
            if 500 <= exc.code < 600 and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP {exc.code} on {method} {path}: {detail[:500]}")
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"Exhausted retries on {method} {path}")


def build_notes(location: str, issue: str, action: str) -> str:
    return (
        f"Location: {location}\n\n"
        f"Issue / Observation:\n{issue}\n\n"
        f"Action Required:\n{action}"
    )


TICKETS = [
    {
        "id": "Footer-001",
        "title": "[Web] Affiliates title misspelling",
        "location": "Affiliates \u2014 Title",
        "issue": "\u201cAffiliates\u201d is misspelled as \u201cAffilates\u201d.",
        "action": "Change to \u201cAffiliates\u201d.",
    },
    {
        "id": "Footer-002",
        "title": "[Web] Contact Us heading capitalisation",
        "location": "Contact Us \u2014 Title",
        "issue": "The heading \u201cContact us\u201d uses inconsistent capitalisation.",
        "action": "Change to \u201cContact Us\u201d.",
    },
    {
        "id": "Footer-003",
        "title": "[Web] Remove Quick Links section",
        "location": "Quick Links",
        "issue": (
            "Several links duplicate the main navigation. Replacing them with visitor "
            "information would also overlap with the existing Visit section."
        ),
        "action": "Remove the Quick Links section.",
    },
    {
        "id": "Footer-004",
        "title": "[Web] Mailing list description wording",
        "location": "Mailing list \u2014 Description",
        "issue": "The phrase \u201cnews and events on KMSPKS\u201d is unnatural.",
        "action": (
            "Replace with \u201cJoin our mailing list for the latest news and upcoming "
            "events at KMSPKS.\u201d"
        ),
    },
    {
        "id": "Footer-005",
        "title": "[Web] Mailing list button label",
        "location": "Mailing list \u2014 Button",
        "issue": "The label \u201cJoin\u201d does not explicitly indicate email subscription.",
        "action": "Change to \u201cSubscribe\u201d.",
    },
    {
        "id": "Footer-006",
        "title": "[Web] Mailing list subscription feedback",
        "location": "Mailing list \u2014 Subscription feedback",
        "issue": "Subscription success and failure messages have not been verified.",
        "action": (
            "Test valid, invalid and duplicate email submissions. Display clear "
            "confirmation or error messages based on the actual result."
        ),
    },
    {
        "id": "Footer-007",
        "title": "[Web] Contact Us address formatting",
        "location": "Contact Us \u2014 Address",
        "issue": (
            "The address lacks punctuation separating the street address from Singapore "
            "and the postal code."
        ),
        "action": "Change to \u201c88 Bright Hill Road, Singapore 574117\u201d.",
    },
    {
        "id": "Footer-008",
        "title": "[Web] See all Gates button",
        "location": "Contact Us \u2014 See all Gates button",
        "issue": (
            "\u201cSee all Gates\u201d uses inconsistent capitalisation, and its intended "
            "destination is unclear."
        ),
        "action": "Change to \u201cGetting Here\u201d and link it to that page.",
    },
    {
        "id": "Footer-009",
        "title": "[Web] Awareness Place link",
        "location": "Affiliates \u2014 Awareness Place link",
        "issue": "The Awareness Place links to an incorrect URL.",
        "action": "Update the link to https://awarenessplace.com/",
    },
    {
        "id": "Footer-010",
        "title": "[Web] Remove Singapore Buddhist Free Clinic",
        "location": "Affiliates \u2014 Singapore Buddhist Free Clinic",
        "issue": "Singapore Buddhist Free Clinic should not be included in the Affiliates list.",
        "action": (
            "Remove the Singapore Buddhist Free Clinic entry and its link from the "
            "footer in both English and Chinese versions."
        ),
    },
    {
        "id": "Footer-011",
        "title": "[Web] Follow Us social media icon links",
        "location": "Follow Us \u2014 Social media icons",
        "issue": (
            "The LinkedIn, WhatsApp and Xiaohongshu icons link to incorrect destinations."
        ),
        "action": (
            "Update the links to the correct URLs:\n"
            "- LinkedIn Page: https://sg.linkedin.com/company/kmspks\n"
            "- WhatsApp: https://www.whatsapp.com/channel/0029VaeDmIm1SWsuTiVMGW3F\n"
            "- Xiaohongshu: https://www.rednote.com/user/profile/66a0a870000000000d026ec1"
        ),
    },
]


def existing_tasks(token: str):
    tasks = {}
    offset = None
    while True:
        params = {"limit": 100, "opt_fields": "gid,name"}
        if offset:
            params["offset"] = offset
        payload = api_request(token, "GET", f"/projects/{PROJECT_GID}/tasks", params=params)
        for task in payload.get("data", []):
            name = (task.get("name") or "").strip()
            if name:
                tasks[name] = str(task.get("gid", ""))
        next_page = payload.get("next_page")
        if not next_page or not next_page.get("offset"):
            break
        offset = next_page["offset"]
    return tasks


def existing_titles(token: str):
    return set(existing_tasks(token).keys())


def notes_for(ticket: dict) -> str:
    if ticket.get("notes"):
        return ticket["notes"]
    return build_notes(ticket["location"], ticket["issue"], ticket["action"])


def apply_metadata(token: str, task_gid: str, collaborators):
    api_request(
        token,
        "POST",
        f"/tasks/{task_gid}/addFollowers",
        body={"data": {"followers": collaborators}},
    )
    api_request(
        token,
        "PUT",
        f"/tasks/{task_gid}",
        body={"data": {"custom_fields": {PLATFORM_FIELD_GID: PLATFORM_OPTION_GIDS}}},
    )


def upload_attachment(token: str, task_gid: str, path: str, name: str = None):
    import requests

    filename = name or os.path.basename(path)
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as handle:
        files = {"file": (filename, handle, content_type)}
        resp = requests.post(
            f"{API_BASE}/tasks/{task_gid}/attachments",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            timeout=300,
        )
    if resp.status_code >= 300:
        raise RuntimeError(f"attachment upload failed {resp.status_code}: {resp.text[:300]}")
    return resp.json().get("data", {})


def build_html_notes(text: str, attachment_gids) -> str:
    body = xml_escape(text.strip())
    for gid in attachment_gids:
        body += f'\n\n<img data-asana-gid="{gid}"/>'
    return f"<body>{body}</body>"


def set_inline_notes(token: str, task_gid: str, text: str, attachment_gids, attempts: int = 6):
    html = build_html_notes(text, attachment_gids)
    latest = ""
    for attempt in range(attempts):
        resp = api_request(
            token,
            "PUT",
            f"/tasks/{task_gid}",
            body={"data": {"html_notes": html}},
            params={"opt_fields": "html_notes"},
        )
        latest = resp.get("data", {}).get("html_notes", "")
        if latest and 'data-src-width="0"' not in latest:
            return latest
        time.sleep(2)
    return latest


def sync_metadata(token: str, tickets: list, collaborators, dry_run: bool = False):
    tasks = existing_tasks(token)
    synced = 0
    missing = 0
    for ticket in tickets:
        title = ticket["title"].strip()
        task_gid = tasks.get(title)
        if not task_gid:
            print(f"MISSING {ticket['id']}: not found in project")
            missing += 1
            continue
        if dry_run:
            print(f"DRY-RUN {ticket['id']}: would add followers {collaborators} and "
                  f"Platform {PLATFORM_OPTION_GIDS} to {task_gid}")
            continue
        apply_metadata(token, task_gid, collaborators)
        synced += 1
        print(f"SYNCED  {ticket['id']}: {title} ({task_gid})")
    if not dry_run:
        print(f"\nDone. synced={synced} missing={missing}")
    return 0


def create_ticket(token: str, ticket: dict, collaborators):
    notes = notes_for(ticket)
    attachments = ticket.get("attachments", [])
    data = {
        "name": ticket["title"],
        "projects": [PROJECT_GID],
        "custom_fields": {PLATFORM_FIELD_GID: PLATFORM_OPTION_GIDS},
    }
    if not attachments:
        data["notes"] = notes
    payload = api_request(
        token,
        "POST",
        "/tasks",
        body={"data": data},
        params={"opt_fields": "gid,name,permalink_url"},
    )
    task = payload.get("data", {})
    task_gid = str(task.get("gid", ""))
    if not task_gid:
        return task
    api_request(token, "POST", f"/sections/{SECTION_GID}/addTask", body={"data": {"task": task_gid}})
    apply_metadata(token, task_gid, collaborators)
    if attachments:
        gids = []
        for attachment in attachments:
            uploaded = upload_attachment(token, task_gid, attachment["path"], attachment.get("name"))
            if uploaded.get("gid"):
                gids.append(str(uploaded["gid"]))
        if gids:
            set_inline_notes(token, task_gid, notes, gids)
    return task


def main():
    parser = argparse.ArgumentParser(description="Create [KMS] Client UAT tickets in Asana.")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without calling Asana.")
    parser.add_argument("--set", choices=["footer", "awaken", "contact"], default="footer", help="Ticket set to process.")
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="ISSUE_ID",
        help="Only process specific issue id(s), e.g. --only Footer-001 --only Footer-002.",
    )
    parser.add_argument(
        "--sync-meta",
        action="store_true",
        help="Apply collaborators and Platform tags to existing tickets instead of creating.",
    )
    args = parser.parse_args()

    if not ENV_PATH.exists():
        print(f"Missing env file: {ENV_PATH}", file=sys.stderr)
        return 1
    token = load_env(ENV_PATH).get("ASANA_TOKEN", "").strip()
    if not token:
        print("ASANA_TOKEN is required in .env", file=sys.stderr)
        return 1

    collaborators = COLLABORATORS_BY_SET[args.set]

    if args.set == "awaken":
        import awaken_tickets

        all_tickets = awaken_tickets.build_tickets(AWAKEN_WORK_DIR)
    elif args.set == "contact":
        import contact_tickets

        all_tickets = contact_tickets.build_tickets(CONTACT_WORK_DIR, token)
    else:
        all_tickets = TICKETS

    if args.only:
        wanted = {o.lower() for o in args.only}
        tickets = [t for t in all_tickets if t["id"].lower() in wanted]
        missing_ids = wanted - {t["id"].lower() for t in tickets}
        if missing_ids:
            print(f"No ticket matching --only {', '.join(sorted(missing_ids))}", file=sys.stderr)
            return 1
    else:
        tickets = all_tickets

    if args.sync_meta:
        return sync_metadata(token, tickets, collaborators, dry_run=args.dry_run)

    seen = () if args.dry_run else existing_titles(token)

    created = 0
    skipped = 0
    for ticket in tickets:
        if ticket["title"].strip() in seen:
            print(f"SKIP    {ticket['id']}: already exists")
            skipped += 1
            continue
        if args.dry_run:
            print(f"DRY-RUN {ticket['id']}: {ticket['title']}  [images={len(ticket.get('attachments', []))}]")
            print(notes_for(ticket))
            print("-" * 60)
            continue
        task = create_ticket(token, ticket, collaborators)
        created += 1
        print(f"CREATED {ticket['id']}: {task.get('name')} -> {task.get('permalink_url')}")

    print(f"\nDone. created={created} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
