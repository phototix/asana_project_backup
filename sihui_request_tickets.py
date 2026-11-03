#!/usr/bin/env python3
"""Build and create Si Hui's 2026-10-27 Marcomm request tickets.

The source is a Google Doc with six distinct questions across Online Pledge and
3 Refuge and 5 Precepts. One Asana task is created per question. Descriptions use
paragraphs only (no ordered or unordered lists) and place the source screenshots
inline via html_notes.
"""
import argparse
import html
import io
import mimetypes
import re
import sys
import time
import urllib.request
from pathlib import Path

from create_uat_tickets import (
    PLATFORM_FIELD_GID,
    PLATFORM_OPTION_GIDS,
    PROJECT_GID,
    SECTION_GID,
    api_request,
    existing_titles,
    load_env,
    ENV_PATH,
)
import requests

DOC_ID = "12Ohvthtlout6ZZRO6H6lQQCSPU5R3uIkH8Jr7a3GLv0"
DOC_URL = f"https://docs.google.com/document/d/{DOC_ID}/edit"
DOC_HTML_URL = f"https://docs.google.com/document/d/{DOC_ID}/mobilebasic"
REQUESTER = "Si Hui (Marcomm)"
SI_HUI_GID = "1212427501814921"
WORK_DIR = Path("/var/www/codigo.brandon.my/tmp/sihui")
API_BASE = "https://app.asana.com/api/1.0"


TICKETS = [
    {
        "id": "online-pledge-how-to-submit",
        "title": '[Web & CMS] Online Pledge - Port "How to submit the pledge" content within word limit',
        "blocks": [
            ("p", f"Requester: {REQUESTER}"),
            ("p", f"Source: {DOC_URL}"),
            (
                "p",
                'Context: The current Online Pledge page has a "How to participate" section '
                'with detailed submission steps and the Medicine Buddha prayer (\u7948\u613f\u6587). '
                "Si Hui tried to port this content to the future site but the word count limit "
                "prevented it.",
            ),
            ("img", 1, "Online Pledge - How to submit the pledge.png"),
            (
                "p",
                "Issue: The English copy is much longer than the Chinese copy. As Dharma text it "
                "cannot be shortened without risking mistranslation, so the existing word limit "
                "is blocking the full content.",
            ),
            (
                "p",
                "Action required: Advise and implement a workaround so the full English and "
                "Chinese steps and the \u7948\u613f\u6587 can be published in the CMS without "
                "truncation. Confirm whether the limit can be extended or a flexible content "
                "block used.",
            ),
            (
                "p",
                "Acceptance: The complete section displays on the new Online Pledge page in "
                "English and Chinese, is editable in the CMS, and is not truncated.",
            ),
        ],
    },
    {
        "id": "online-pledge-prayer",
        "title": "[Web & CMS] Online Pledge - Confirm Prayer selection field",
        "blocks": [
            ("p", f"Requester: {REQUESTER}"),
            ("p", f"Source: {DOC_URL}"),
            (
                "p",
                'Context: The current Online Pledge form includes a "Prayer" option that lets '
                "the submitter choose the prayer their pledge is dedicated to.",
            ),
            ("img", 2, "Online Pledge - Prayer selection field.png"),
            (
                "p",
                "Issue: It is unclear how this option should be replicated on the future site, "
                "and whether SED requested its removal.",
            ),
            (
                "p",
                "Action required: Confirm with SED and Codigo whether the Prayer selection is "
                "still required. If required, configure the field in the CMS and show it on the "
                "form. If removed, record the decision and confirm the final form flow.",
            ),
            (
                "p",
                "Acceptance: The final form either includes a CMS-managed Prayer selection or the "
                "removal is confirmed and documented.",
            ),
        ],
    },
    {
        "id": "online-pledge-transference",
        "title": "[Web & CMS] Online Pledge - Transference of Merit section placement",
        "blocks": [
            ("p", f"Requester: {REQUESTER}"),
            ("p", f"Source: {DOC_URL}"),
            (
                "p",
                "Context: The current Online Pledge page includes a Transference of Merit "
                "section that forms part of the pledge instructions.",
            ),
            ("img", 3, "Online Pledge - Transference of Merit.png"),
            (
                "p",
                "Issue: There is no clear place for this section on the future site because of "
                "the word limits and the current form setup.",
            ),
            (
                "p",
                "Action required: Propose and implement a placement for the Transference of "
                "Merit content, such as a CMS-managed content section after the pledge "
                "submission confirmation. Confirm the final placement with Marcomm.",
            ),
            (
                "p",
                "Acceptance: The Transference of Merit text appears in the agreed location in "
                "English and Chinese, is editable in the CMS, and is not truncated.",
            ),
        ],
    },
    {
        "id": "online-pledge-count-choice",
        "title": "[Web & CMS] Online Pledge - Count choice entry and user preview",
        "blocks": [
            ("p", f"Requester: {REQUESTER}"),
            ("p", f"Source: {DOC_URL}"),
            (
                "p",
                "Context: The future site requires the chant count choice to be keyed in one "
                "by one.",
            ),
            ("img", 4, "Online Pledge - Count choice.png"),
            (
                "p",
                "Issue: It is unclear how the count selection will appear to the user, and "
                "there is no way to preview it before launch.",
            ),
            (
                "p",
                "Action required: Confirm the intended user experience for selecting 108, 540 "
                "or 1080 counts, provide a preview on pre-prod, and verify that the chosen "
                "value is submitted and stored correctly.",
            ),
            (
                "p",
                "Acceptance: The user can select a count, preview the flow on pre-prod, and the "
                "submitted value is recorded correctly.",
            ),
        ],
    },
    {
        "id": "refuge-phone-input",
        "title": "[Web & CMS] 3 Refuge and 5 Precepts - Phone input rejects 6-prefix and multiple lines",
        "blocks": [
            ("p", f"Requester: {REQUESTER}"),
            ("p", f"Source: {DOC_URL}"),
            (
                "p",
                "Context: This affects the 3 Refuge and 5 Precepts activity registration form "
                "during upload testing.",
            ),
            ("img", 5, "3 Refuge and 5 Precepts - Phone input.png"),
            (
                "p",
                "Issue: The input field does not accept phone numbers that start with 6, and it "
                "does not accept multiple phone lines. Some departments have two lines and "
                "sometimes include Reception's number as an alternative.",
            ),
            (
                "p",
                "Action required: Update the validation so all valid Singapore numbers, "
                "including numbers starting with 6, are accepted, and allow multiple or "
                "alternative phone lines where required.",
            ),
            (
                "p",
                "Acceptance: A number starting with 6 can be entered, multiple numbers can be "
                "captured, and the saved values display correctly.",
            ),
        ],
    },
    {
        "id": "refuge-event-time",
        "title": "[Web & CMS] 3 Refuge and 5 Precepts - Multi-day event time layout and validation",
        "blocks": [
            ("p", f"Requester: {REQUESTER}"),
            ("p", f"Source: {DOC_URL}"),
            (
                "p",
                "Context: This affects the Event Detail > Event Time layout for multi-day "
                "events in the 3 Refuge and 5 Precepts activity.",
            ),
            ("img", 6, "3 Refuge and 5 Precepts - Event time layout.png"),
            (
                "p",
                "Issue: The layout does not account for different start and end times on each "
                "day of the event. The system also rejects an end time that is earlier than the "
                "start time even when it falls on a later day.",
            ),
            ("img", 7, "3 Refuge and 5 Precepts - Multi-day event example.png"),
            (
                "p",
                "Action required: Support per-day start and end times for multi-day events and "
                "validate each day independently. Allow a later day's end time to be earlier "
                "than the first day's start time when the dates are different.",
            ),
            (
                "p",
                "Acceptance: Multi-day events can be entered with different daily times, and "
                "the example with a 2pm start on day one and a 12pm end on the last day saves "
                "and displays correctly.",
            ),
        ],
    },
]


def fetch_doc_html() -> str:
    req = urllib.request.Request(DOC_HTML_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", "ignore")


def extract_image_urls(document_html: str):
    urls = re.findall(r'<img[^>]+src="([^"]+)"', document_html)
    return [html.unescape(url) for url in urls]


def normalize_image(src: Path, dst: Path):
    from PIL import Image, ImageOps

    image = Image.open(src)
    image = ImageOps.exif_transpose(image)
    if dst.suffix.lower() in (".jpg", ".jpeg"):
        image.convert("RGB").save(dst, "JPEG", quality=90, optimize=True)
        return
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    else:
        image = image.convert("RGB")
    image.save(dst, "PNG", optimize=True)


def prepare_images(work_dir: Path = WORK_DIR):
    work_dir.mkdir(parents=True, exist_ok=True)
    document_html = fetch_doc_html()
    urls = extract_image_urls(document_html)
    if len(urls) < 7:
        raise RuntimeError(f"Expected at least 7 images in the document, found {len(urls)}")
    paths = {}
    for index, url in enumerate(urls, start=1):
        raw = work_dir / f"image-{index}-raw.png"
        clean = work_dir / f"image-{index}.png"
        if not clean.exists():
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw.write_bytes(resp.read())
            try:
                normalize_image(raw, clean)
            except Exception:
                clean.write_bytes(raw.read_bytes())
        paths[index] = clean
    return paths


def upload_attachment(token: str, task_gid: str, path: Path, name: str):
    filename = name or path.name
    content_type = mimetypes.guess_type(filename)[0] or "image/png"
    with path.open("rb") as handle:
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


def build_html_notes(blocks, attachment_gids):
    body = []
    for block in blocks:
        if block[0] == "p":
            body.append(html.escape(block[1]))
        elif block[0] == "img":
            gid = attachment_gids.get(block[1])
            if gid:
                body.append(f'<img data-asana-gid="{gid}"/>')
    return "<body>" + "\n\n".join(body) + "</body>"


def set_html_notes(token: str, task_gid: str, blocks, attachment_gids, attempts: int = 6):
    payload = build_html_notes(blocks, attachment_gids)
    latest = ""
    for attempt in range(attempts):
        resp = api_request(
            token,
            "PUT",
            f"/tasks/{task_gid}",
            body={"data": {"html_notes": payload}},
            params={"opt_fields": "html_notes"},
        )
        latest = resp.get("data", {}).get("html_notes", "")
        if latest and 'data-src-width="0"' not in latest:
            return latest
        time.sleep(2)
    return latest


def create_ticket(token: str, ticket: dict, images: dict):
    title = ticket["title"].strip()
    if title in existing_titles(token):
        print(f"SKIP    {ticket['id']}: already exists")
        return None

    payload = api_request(
        token,
        "POST",
        "/tasks",
        body={
            "data": {
                "name": title,
                "projects": [PROJECT_GID],
                "custom_fields": {PLATFORM_FIELD_GID: PLATFORM_OPTION_GIDS},
            }
        },
        params={"opt_fields": "gid,name,permalink_url"},
    )
    task = payload.get("data", {})
    task_gid = str(task.get("gid", ""))
    if not task_gid:
        raise RuntimeError(f"Task creation returned no gid: {task}")

    api_request(token, "POST", f"/sections/{SECTION_GID}/addTask", body={"data": {"task": task_gid}})
    api_request(
        token,
        "POST",
        f"/tasks/{task_gid}/addFollowers",
        body={"data": {"followers": [SI_HUI_GID]}},
    )

    attachment_gids = {}
    for block in ticket["blocks"]:
        if block[0] != "img":
            continue
        index, name = block[1], block[2]
        path = images[index]
        uploaded = upload_attachment(token, task_gid, path, name)
        gid = str(uploaded.get("gid", ""))
        if not gid:
            raise RuntimeError(f"Attachment upload returned no gid for image {index}")
        attachment_gids[index] = gid

    set_html_notes(token, task_gid, ticket["blocks"], attachment_gids)
    print(f"CREATED {ticket['id']}: {title} -> {task.get('permalink_url')}")
    return task_gid


def main():
    parser = argparse.ArgumentParser(description="Create Si Hui request tickets one at a time.")
    parser.add_argument("--only", action="append", default=[], metavar="ID", help="Only process these ticket ids.")
    parser.add_argument("--dry-run", action="store_true", help="Print ticket titles and image mapping only.")
    parser.add_argument("--delay-after", type=int, default=0, metavar="SECONDS", help="Wait after each ticket.")
    parser.add_argument("--list", action="store_true", help="List ticket ids and titles.")
    args = parser.parse_args()

    if args.list:
        for ticket in TICKETS:
            print(f"{ticket['id']}: {ticket['title']}")
        return 0

    if not ENV_PATH.exists():
        print(f"Missing env file: {ENV_PATH}", file=sys.stderr)
        return 1
    token = load_env(ENV_PATH).get("ASANA_TOKEN", "").strip()
    if not token:
        print("ASANA_TOKEN is required", file=sys.stderr)
        return 1

    tickets = TICKETS
    if args.only:
        wanted = {value.lower() for value in args.only}
        tickets = [t for t in TICKETS if t["id"].lower() in wanted]
        missing = wanted - {t["id"].lower() for t in tickets}
        if missing:
            print(f"No ticket matching --only {', '.join(sorted(missing))}", file=sys.stderr)
            return 1

    images = prepare_images()
    for position, ticket in enumerate(tickets):
        if args.dry_run:
            titles = [block[2] for block in ticket["blocks"] if block[0] == "img"]
            print(f"DRY-RUN {ticket['id']}: {ticket['title']} [images={len(titles)}]")
            continue
        create_ticket(token, ticket, images)
        if args.delay_after and position < len(tickets) - 1:
            time.sleep(args.delay_after)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
