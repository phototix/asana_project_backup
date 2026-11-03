#!/usr/bin/env python3
"""Create the new tickets from Xiu Mei's 30 October 2026 website review.

The workbook repeats many issues that are already in Asana. Only the genuinely
new issue IDs are defined here. Descriptions use paragraphs only, with the
source screenshots placed inline via html_notes.
"""
import argparse
import html
import io
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

from create_uat_tickets import (
    ENV_PATH,
    PLATFORM_FIELD_GID,
    PLATFORM_OPTION_GIDS,
    PROJECT_GID,
    SECTION_GID,
    api_request,
    existing_titles,
    load_env,
)
from sihui_request_tickets import set_html_notes, upload_attachment

WORKBOOK_URL = "https://cloud.webbypage.com/index.php/s/qeBgzaLaoMdJzxx/download"
WORK_DIR = Path("/var/www/codigo.brandon.my/tmp/xiumei")
REQUESTER = "Chang Xiu Mei (Marcomm)"
XIU_MEI_GID = "1212427501814924"
SOURCE = WORKBOOK_URL


def paragraph(text: str):
    return ("p", text)


def image(name: str, label: str):
    return ("img", name, label)


TICKETS = [
    {
        "id": "contact-us-012-email-wrapping",
        "title": "[Web] Contact Us - Department Contacts email addresses wrap mid-word",
        "blocks": [
            paragraph(f"Requester: {REQUESTER}"),
            paragraph(f"Source: {SOURCE}"),
            paragraph(
                "Context: On the Contact Us page, the Department Contacts email addresses "
                "wrap mid-word, with some letters appearing on a separate line."
            ),
            paragraph(
                "Issue: The broken wrapping makes the email addresses harder to read and copy."
            ),
            image("image6.png", "Contact Us - Department Contacts email wrapping.png"),
            paragraph(
                "Action required: Adjust the Department Contacts layout so each full email "
                "address displays on one line at desktop and mobile widths."
            ),
            paragraph(
                "Acceptance: Every email address in Department Contacts displays on a single "
                "line without mid-word wrapping."
            ),
        ],
    },
    {
        "id": "contact-us-013-confirmation",
        "title": "[Web] Contact Us - Submission confirmation wording and overlap",
        "blocks": [
            paragraph(f"Requester: {REQUESTER}"),
            paragraph(f"Source: {SOURCE}"),
            paragraph(
                "Context: The submission confirmation currently says \u201cWe\u2019ll get back "
                "to you shortly\u201d, which creates an expectation of a quick response, and "
                "the floating notification overlaps page content."
            ),
            paragraph(
                "Issue: The wording and placement do not meet the intended experience. The "
                "confirmation should appear only after a successful submission."
            ),
            image("image7.png", "Contact Us - Submission confirmation.png"),
            paragraph(
                "Action required: Change the English wording to \u201cThank you! Your message "
                "has been submitted successfully.\u201d and the Chinese wording to "
                "\u201c\u60a8\u7684\u4fe1\u606f\u5df2\u6210\u529f\u63d0\u4ea4\u3002\u201d "
                "Display the confirmation above the form without overlapping other content, "
                "and only after successful submission."
            ),
            paragraph(
                "Acceptance: The revised wording is shown above the form after a successful "
                "submission, does not overlap other content, and is not shown on failure."
            ),
        ],
    },
    {
        "id": "contact-us-014-subject-prefix",
        "title": "[Web] Contact Us - Acknowledgement email subject prefix",
        "blocks": [
            paragraph(f"Requester: {REQUESTER}"),
            paragraph(f"Source: {SOURCE}"),
            paragraph(
                "Context: The acknowledgement email subject includes \u201c[KMS-PRE-PROD]\u201d."
            ),
            paragraph(
                "Issue: This appears to be an internal environment label and should not be "
                "visible to the public."
            ),
            image("image8.png", "Contact Us - Acknowledgement email subject prefix.png"),
            paragraph(
                "Action required: Confirm whether the prefix is for testing only and ensure it "
                "is removed from public-facing emails when the website goes live."
            ),
            paragraph(
                "Acceptance: Production acknowledgement emails do not include the internal "
                "environment prefix."
            ),
        ],
    },
    {
        "id": "contact-us-015-sender-name",
        "title": "[Web] Contact Us - Acknowledgement email sender display name",
        "blocks": [
            paragraph(f"Requester: {REQUESTER}"),
            paragraph(f"Source: {SOURCE}"),
            paragraph("Context: The acknowledgement email sender name displays as \u201cKMS\u201d."),
            paragraph("Issue: This is inconsistent with the KMSPKS brand."),
            paragraph(
                "Action required: Change the sender display name to \u201cKMSPKS\u201d."
            ),
            paragraph(
                "Acceptance: Acknowledgement emails show the sender display name "
                "\u201cKMSPKS\u201d."
            ),
        ],
    },
    {
        "id": "contact-us-016-sender-address",
        "title": "[Web] Contact Us - Acknowledgement email sender address approval",
        "blocks": [
            paragraph(f"Requester: {REQUESTER}"),
            paragraph(f"Source: {SOURCE}"),
            paragraph(
                "Context: The acknowledgement email is sent from kmssupport@kmspks.org."
            ),
            paragraph(
                "Issue: It is unclear whether this sender address has been approved by IT."
            ),
            paragraph(
                "Action required: Confirm with IT whether kmssupport@kmspks.org is the "
                "approved sender address and record the confirmation."
            ),
            paragraph(
                "Acceptance: The sender address is confirmed as approved, or replaced with "
                "the approved address."
            ),
        ],
    },
    {
        "id": "contact-us-017-email-wording",
        "title": "[Web] Contact Us - Acknowledgement email wording",
        "blocks": [
            paragraph(f"Requester: {REQUESTER}"),
            paragraph(f"Source: {SOURCE}"),
            paragraph(
                "Context: The acknowledgement email promises a response within three days and "
                "uses \u201cinquiries\u201d instead of \u201cenquiries\u201d. The response "
                "promise may not reflect each department\u2019s processing time."
            ),
            paragraph("Issue: The wording and terminology need to be corrected."),
            image("image9.png", "Contact Us - Acknowledgement email wording.png"),
            paragraph(
                "Action required: Replace the email body with the approved copy. The greeting "
                "is \u201cDear [Name],\u201d followed by \u201cThank you for contacting Kong "
                "Meng San Phor Kark See Monastery. We have received your enquiry.\u201d"
            ),
            paragraph(
                "The enquiry details are \u201cReference Number: [Reference Number]\u201d, "
                "\u201cDate Submitted: [Date and Time]\u201d and \u201cSubject: [Subject]\u201d."
            ),
            paragraph(
                "The closing instruction is \u201cFor urgent enquiries, please contact the "
                "relevant department listed on our Contact Us page.\u201d"
            ),
            paragraph(
                "Acceptance: The acknowledgement email uses the approved wording and the term "
                "\u201cenquiries\u201d throughout."
            ),
        ],
    },
    {
        "id": "contact-us-018-email-chinese",
        "title": "[Web] Contact Us - Acknowledgement email Chinese version",
        "blocks": [
            paragraph(f"Requester: {REQUESTER}"),
            paragraph(f"Source: {SOURCE}"),
            paragraph(
                "Context: The acknowledgement email is currently in English only."
            ),
            paragraph(
                "Issue: Users submitting enquiries from the Chinese page should receive a "
                "Chinese acknowledgement."
            ),
            paragraph(
                "Action required: Send the Chinese version to users who submit from the "
                "Chinese page. The greeting is \u201c[\u59d3\u540d]\uff0c\u60a8\u597d\uff1a\u201d "
                "followed by \u201c\u60a8\u7684\u8be2\u95ee\u5df2\u6210\u529f\u63d0\u4ea4\u3002\u201d"
            ),
            paragraph(
                "The enquiry details are \u201c\u53c2\u8003\u7f16\u53f7\uff1a[\u7f16\u53f7]\u201d, "
                "\u201c\u63d0\u4ea4\u65f6\u95f4\uff1a[\u65e5\u671f\u53ca\u65f6\u95f4]\u201d and "
                "\u201c\u8be2\u95ee\u4e3b\u9898\uff1a[\u4e3b\u9898]\u201d."
            ),
            paragraph(
                "The closing instruction is \u201c\u5982\u6709\u7d27\u6025\u4e8b\u9879\uff0c"
                "\u8bf7\u524d\u5f80 \u8054\u7cfb\u6211\u4eec \u9875\u9762\uff0c\u8054\u7edc"
                "\u76f8\u5173\u90e8\u95e8\u3002\u201d and the signature is "
                "\u201c\u5149\u660e\u5c71\u666e\u89c9\u7985\u5bfa\u201d."
            ),
            paragraph(
                "Acceptance: Chinese-page submissions receive the Chinese acknowledgement with "
                "the correct reference number, date and time, subject and signature."
            ),
        ],
    },
    {
        "id": "contact-us-019-support-address",
        "title": "[Web] Contact Us - Acknowledgement email support address",
        "blocks": [
            paragraph(f"Requester: {REQUESTER}"),
            paragraph(f"Source: {SOURCE}"),
            paragraph(
                "Context: The email footer lists support@kmspks.org, while the sender address "
                "is kmssupport@kmspks.org."
            ),
            paragraph(
                "Issue: It is unclear which address is intended for public enquiries."
            ),
            paragraph(
                "Action required: Confirm the approved public-facing email address with IT and "
                "ensure the mailbox is monitored by the responsible team."
            ),
            paragraph(
                "Acceptance: One approved public address is used consistently and the mailbox "
                "is monitored."
            ),
        ],
    },
    {
        "id": "contact-us-020-contact-instructions",
        "title": "[Web] Contact Us - Acknowledgement email contact instructions",
        "blocks": [
            paragraph(f"Requester: {REQUESTER}"),
            paragraph(f"Source: {SOURCE}"),
            paragraph(
                "Context: The email body directs users to the Contact Us page, while the footer "
                "directs them to a support mailbox."
            ),
            paragraph(
                "Issue: The inconsistent instructions may confuse users."
            ),
            paragraph(
                "Action required: Use the Contact Us page consistently. Replace the footer "
                "instruction with \u201cFor further assistance, please visit our Contact Us "
                "page.\u201d and link to the correct page."
            ),
            paragraph(
                "Acceptance: The acknowledgement email consistently directs users to the "
                "Contact Us page, with a working link."
            ),
        ],
    },
    {
        "id": "contact-us-021-address-punctuation",
        "title": "[Web] Contact Us - Acknowledgement email address punctuation",
        "blocks": [
            paragraph(f"Requester: {REQUESTER}"),
            paragraph(f"Source: {SOURCE}"),
            paragraph(
                "Context: The acknowledgement email footer address is missing a comma between "
                "the street address and \u201cSingapore\u201d."
            ),
            paragraph(
                "Issue: The punctuation is inconsistent with the approved address format."
            ),
            paragraph(
                "Action required: Update the address to \u201c88 Bright Hill Road, Singapore "
                "574117\u201d."
            ),
            paragraph(
                "Acceptance: The acknowledgement email footer shows the approved address with "
                "the correct punctuation."
            ),
        ],
    },
    {
        "id": "contact-us-022-social-icons",
        "title": "[Web] Contact Us - Acknowledgement email social media icons",
        "blocks": [
            paragraph(f"Requester: {REQUESTER}"),
            paragraph(f"Source: {SOURCE}"),
            paragraph(
                "Context: The acknowledgement email footer displays only Facebook and YouTube "
                "icons."
            ),
            paragraph(
                "Issue: The full set of official social media channels is not represented."
            ),
            paragraph(
                "Action required: Include all social media icons listed on the website and "
                "ensure each links to the correct official account or destination."
            ),
            paragraph(
                "Acceptance: The acknowledgement email footer shows all official social media "
                "icons with correct links."
            ),
        ],
    },
    {
        "id": "cms-subject-reorder",
        "title": "[Web & CMS] Contact Us - Subject Master Data reordering",
        "blocks": [
            paragraph(f"Requester: {REQUESTER}"),
            paragraph(f"Source: {SOURCE}"),
            paragraph(
                "Context: The Contact Us subject dropdown options are managed under CMS > "
                "Contact Management > Contact Us > Subject Master Data."
            ),
            paragraph(
                "Issue: There is no visible option to reorder the subjects, but the options "
                "need to be arranged according to their priority."
            ),
            image("image10.png", "Contact Us - Subject Master Data reordering.png"),
            paragraph(
                "Action required: Add a reordering function and ensure the selected order is "
                "reflected in the website\u2019s subject dropdown."
            ),
            paragraph(
                "Acceptance: An administrator can reorder subjects in the CMS and the website "
                "dropdown displays the same order."
            ),
        ],
    },
]


def fetch_workbook() -> bytes:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    cached = WORK_DIR / "workbook.xlsx"
    if not cached.exists() or cached.stat().st_size == 0:
        req = urllib.request.Request(WORKBOOK_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=180) as resp:
            cached.write_bytes(resp.read())
    return cached.read_bytes()


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


def prepare_images():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(io.BytesIO(fetch_workbook()))
    wanted = ["image6.png", "image7.png", "image8.png", "image9.png", "image10.png"]
    paths = {}
    for name in wanted:
        raw = WORK_DIR / f"{name}.raw"
        clean = WORK_DIR / name
        if not clean.exists():
            raw.write_bytes(z.read(f"xl/media/{name}"))
            try:
                normalize_image(raw, clean)
            except Exception:
                clean.write_bytes(raw.read_bytes())
        paths[name] = clean
    return paths


def clean_text(text: str) -> str:
    for prefix in (
        "Context: ",
        "Issue: ",
        "Action required: ",
        "Acceptance: ",
        "Expected: ",
        "Observation: ",
    ):
        if text.startswith(prefix):
            return text[len(prefix):]
    return text


def clean_blocks(blocks):
    cleaned = []
    for block in blocks:
        if block[0] == "p":
            if block[1].startswith(("Requester:", "Source:")):
                continue
            cleaned.append(("p", clean_text(block[1])))
        else:
            cleaned.append(block)
    return cleaned


def create_ticket(token: str, ticket: dict, images: dict):
    title = ticket["title"].strip()
    blocks = clean_blocks(ticket["blocks"])
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
        body={"data": {"followers": [XIU_MEI_GID]}},
    )

    attachment_gids = {}
    for block in blocks:
        if block[0] != "img":
            continue
        name = block[1]
        uploaded = upload_attachment(token, task_gid, images[name], block[2])
        gid = str(uploaded.get("gid", ""))
        if not gid:
            raise RuntimeError(f"Attachment upload returned no gid for {name}")
        attachment_gids[name] = gid

    set_html_notes(token, task_gid, blocks, attachment_gids)
    print(f"CREATED {ticket['id']}: {title} -> {task.get('permalink_url')}")
    return task_gid


def main():
    parser = argparse.ArgumentParser(description="Create Xiu Mei review tickets one at a time.")
    parser.add_argument("--only", action="append", default=[], metavar="ID", help="Only process these ticket ids.")
    parser.add_argument("--dry-run", action="store_true", help="Print ticket titles and image mapping only.")
    parser.add_argument("--delay-after", type=int, default=0, metavar="SECONDS", help="Wait after each ticket.")
    parser.add_argument("--list", action="store_true", help="List ticket ids and titles.")
    args = parser.parse_args()

    if args.list:
        for ticket in TICKETS:
            images = [block[2] for block in ticket["blocks"] if block[0] == "img"]
            print(f"{ticket['id']}: {ticket['title']} [images={len(images)}]")
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
            count = sum(1 for block in ticket["blocks"] if block[0] == "img")
            print(f"DRY-RUN {ticket['id']}: {ticket['title']} [images={count}]")
            continue
        create_ticket(token, ticket, images)
        if args.delay_after and position < len(tickets) - 1:
            time.sleep(args.delay_after)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
