#!/usr/bin/env python3
"""Build [Web] Contact Us split tickets from KMS-1162.

KMS-1162 ([Web] Contact Us) bundled several distinct feedback items. This
module returns one ticket per item, carrying over the relevant screenshot(s)
from the original ticket as inline attachments.
"""
import os
import urllib.request
from pathlib import Path

from create_uat_tickets import API_BASE, api_request


SOURCE_TASK_GID = "1219570452486130"  # [Web] Contact Us (KMS-1162)
SPLIT_NOTE = "Split from KMS-1162 ([Web] Contact Us)."

# (internal id, title summary, issue, action, screenshot attachment gid)
ITEMS = [
    (
        "send-a-message-heading",
        '"Send A Message" heading capitalisation',
        'Typo: The heading "Send A Message" uses an uppercase "A".',
        'Change to "Send a Message".',
        "1219570452486133",
    ),
    (
        "subject-dropdown-labels",
        "Subject dropdown internal labels",
        'The Subject dropdown displays internal labels such as "Contact Us Email ENG", '
        '"Support Email ENG" and "FAQ Email ENG".',
        "Replace the internal labels with clear enquiry categories.",
        "1219570452486135",
    ),
    (
        "verify-human-placeholder",
        '"TODO: Verify Human" placeholder',
        'The placeholder "TODO: Verify Human" is visible.',
        "Remove the placeholder and complete the verification integration.",
        "1219570452486137",
    ),
    (
        "rename-helpdesk",
        'Rename "Helpdesk" to "Department Contacts"',
        'The heading "Helpdesk" may suggest technical support and does not clearly '
        "describe the departmental contact directory.",
        'Rename the heading to "Department Contacts".',
        None,
    ),
    (
        "department-contact-details",
        "Incomplete department contact details",
        "The Helpdesk content is incomplete. Several departments listed on the existing "
        "website are missing, and telephone numbers and email addresses are not displayed.",
        "Restore the complete departmental contact including name, service description, "
        "telephone number and email address.",
        None,
    ),
    (
        "submission-confirmation-privacy",
        "Submission confirmation & privacy notice",
        "Please confirm whether a success message is displayed after submission. No "
        "explanation of personal data use or privacy policy link is visible.",
        "Display a confirmation message only after successful submission. Add a brief "
        "explanation of personal data use and a privacy policy link.",
        None,
    ),
    (
        "form-validation-testing",
        "Form validation testing",
        "Blank-field validation and invalid email handling have not been tested.",
        "Test an empty submission, an invalid email, an unselected subject and valid input.",
        None,
    ),
    (
        "submission-delivery-verification",
        "Submission delivery verification",
        "The success message, backend receipt and delivery to the designated mailbox have "
        "not been verified.",
        "Test and check the success message and receiving mailbox.",
        None,
    ),
    (
        "preserve-input-failed-submission",
        "Preserve input on failed submission",
        "It has not been verified whether entered information is preserved when "
        "submission fails.",
        "Do a submission failure test.",
        None,
    ),
]


def _normalize_image(src: Path, dst: Path):
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


def _fetch_image(token: str, download_url: str, target: Path):
    req = urllib.request.Request(download_url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=120) as resp, target.open("wb") as out:
        out.write(resp.read())


def build_tickets(work_dir: Path, token: str):
    images_dir = work_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    attachments = api_request(
        token,
        "GET",
        f"/tasks/{SOURCE_TASK_GID}/attachments",
        params={"limit": 100, "opt_fields": "gid,name,download_url"},
    ).get("data", [])
    by_gid = {str(a.get("gid")): a for a in attachments}

    tickets = []
    for item_id, summary, issue, action, image_gid in ITEMS:
        body = f"{SPLIT_NOTE}\n\n{issue}\n\n{action}"
        ticket = {
            "id": f"Contact-{item_id}",
            "title": f"[Web] Contact Us - {summary}",
            "notes": body + "\n",
            "attachments": [],
        }
        if image_gid and image_gid in by_gid:
            raw = images_dir / f"{image_gid}.png"
            if not raw.exists():
                _fetch_image(token, by_gid[image_gid]["download_url"], raw)
            clean = images_dir / f"{image_gid}-clean.png"
            if not clean.exists():
                try:
                    _normalize_image(raw, clean)
                except Exception:
                    clean.write_bytes(raw.read_bytes())
            ticket["attachments"].append(
                {"path": str(clean), "name": f"Contact Us - {summary}.png"}
            )
        tickets.append(ticket)
    return tickets


if __name__ == "__main__":
    import sys
    from create_uat_tickets import load_env, ENV_PATH

    tok = load_env(ENV_PATH)["ASANA_TOKEN"]
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/var/www/codigo.brandon.my/tmp/contact")
    for t in build_tickets(out, tok):
        print(f"{t['title']}  [images={len(t['attachments'])}]")
