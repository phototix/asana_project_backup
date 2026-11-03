#!/usr/bin/env python3
"""Capture pre-prod screenshots for current Pass tickets and post them inline.

Usage:
  PRE_USER=... PRE_PASS=... /tmp/opencode/uat-evidence-venv/bin/python \
    capture_pass_evidence.py --capture-only [--only GID]
  PRE_USER=... PRE_PASS=... /tmp/opencode/uat-evidence-venv/bin/python \
    capture_pass_evidence.py --post [--only GID] [--force]
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_uat_tickets import load_env, api_request, upload_attachment, ENV_PATH

BASE = "https://pre-prod.d2x7klqewcc6th.amplifyapp.com"
OUT_ROOT = Path("/tmp/opencode/uat-pass-evidence")
STATE_PATH = Path("/tmp/opencode/uat-pass-evidence-state.json")
PRE_USER = os.environ.get("PRE_USER")
PRE_PASS = os.environ.get("PRE_PASS")
if not PRE_USER or not PRE_PASS:
    sys.exit("PRE_USER and PRE_PASS are required")

TOKEN = load_env(ENV_PATH)["ASANA_TOKEN"]

EVIDENCE = {
    "1219730158203178": {
        "slug": "career_walkin",
        "shots": [
            {"lang": "EN", "path": "/join-us/career", "text": "Walk-In Interview", "kind": "text", "container": "xpath=.."},
            {"lang": "CN", "path": "/zh/join-us/career", "text": "现场面试", "kind": "text", "container": "xpath=.."},
        ],
    },
    "1219729872643659": {
        "slug": "bright_youth_four_pillars",
        "shots": [
            {"lang": "EN", "path": "/join-us/bright-youth", "text": "The Four Pillars of Bright Youth", "kind": "text", "container": "xpath=ancestor::section[1]"},
            {"lang": "CN", "path": "/zh/join-us/bright-youth", "text": "光明青年的四大支柱", "kind": "text", "container": "xpath=ancestor::section[1]"},
        ],
    },
    "1219575481392590": {
        "slug": "digital_category",
        "shots": [
            {"lang": "EN", "path": "/awaken-online/digital", "text": "Digital Content", "kind": "heading", "container": "xpath=ancestor::div[contains(@class,'sticky')][1]", "pad": 8},
            {"lang": "CN", "path": "/zh/awaken-online/digital", "text": "数位资源", "kind": "heading", "container": "xpath=ancestor::div[contains(@class,'sticky')][1]", "pad": 8},
        ],
    },
    "1219729966737873": {
        "slug": "home_mailing_copy",
        "shots": [
            {"lang": "EN", "path": "/", "text": "Join our mailing list to receive the latest news and updates.", "kind": "text", "container": "xpath=..", "pad": 16},
            {"lang": "CN", "path": "/zh/", "text": "订阅本寺电子报，了解最新法务与活动资讯。", "kind": "text", "container": "xpath=..", "pad": 16},
        ],
    },
    "1219573589963215": {
        "slug": "home_mailing_button",
        "shots": [
            {"lang": "EN", "path": "/", "text": "Subscribe", "kind": "button", "container": "xpath=ancestor::div[2]"},
            {"lang": "CN", "path": "/zh/", "text": "订阅", "kind": "button", "container": "xpath=ancestor::div[2]"},
        ],
    },
    "1219730038770916": {
        "slug": "home_latest_happenings",
        "shots": [
            {"lang": "EN", "path": "/", "text": "Latest Happenings & Activities", "kind": "text", "container": "xpath=ancestor::section[1]"},
            {"lang": "CN", "path": "/zh/", "text": "近期动态与活动", "kind": "text", "container": "xpath=ancestor::section[1]"},
        ],
    },
    "1219730214000918": {
        "slug": "bright_youth_membership",
        "shots": [
            {"lang": "EN", "path": "/join-us/bright-youth", "text": "Becoming a Bright Youth Member", "kind": "text", "container": "xpath=..", "pad": 16},
            {"lang": "CN", "path": "/zh/join-us/bright-youth", "text": "加入光明青年", "kind": "text", "container": "xpath=..", "pad": 16},
        ],
    },
    "1219729885362231": {
        "slug": "bright_youth_empty_state",
        "shots": [
            {"lang": "EN", "path": "/join-us/bright-youth", "text": "No upcoming activities", "kind": "text", "container": "xpath=ancestor::section[1]"},
            {"lang": "CN", "path": "/zh/join-us/bright-youth", "text": "暂无活动", "kind": "text", "container": "xpath=ancestor::section[1]"},
        ],
    },
    "1219730214327943": {
        "slug": "joyous_heart_gallery",
        "shots": [
            {"lang": "EN", "path": "/join-us/joyous-heart", "text": "Gallery", "kind": "text", "container": "xpath=ancestor::section[1]"},
            {"lang": "CN", "path": "/zh/join-us/joyous-heart", "text": "活动相册", "kind": "text", "container": "xpath=ancestor::section[1]"},
        ],
    },
}


def pick_visible(locator):
    count = locator.count()
    for i in range(count):
        item = locator.nth(i)
        try:
            if item.is_visible():
                return item
        except Exception:
            continue
    return None


def locate(page, shot):
    if shot["kind"] == "link":
        loc = page.get_by_role("link", name=shot["text"], exact=True)
    elif shot["kind"] == "button":
        loc = page.get_by_role("button", name=shot["text"], exact=True)
    elif shot["kind"] == "heading":
        loc = page.get_by_role("heading", name=shot["text"], exact=True)
        for i in range(loc.count()):
            item = loc.nth(i)
            try:
                if item.is_visible() and item.locator("xpath=ancestor::div[contains(@class,'sticky')]").count():
                    return item
            except Exception:
                continue
    else:
        loc = page.get_by_text(shot["text"], exact=True)
    return pick_visible(loc)


def capture_one(page, gid, spec):
    out_dir = OUT_ROOT / gid
    out_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for shot in spec["shots"]:
        page.goto(BASE + shot["path"], wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        target = locate(page, shot)
        if target is None:
            raise RuntimeError(f"{gid} {shot['lang']}: target not found: {shot['text']}")
        target.scroll_into_view_if_needed()
        target.wait_for(state="visible", timeout=15000)
        target.evaluate(
            "e => { e.style.boxShadow = 'inset 0 0 0 4px #dc2626'; e.style.borderRadius = '4px'; }"
        )
        page.wait_for_timeout(400)
        container = target.locator(shot["container"])
        if container.count() == 0:
            container = target
        container.wait_for(state="visible", timeout=10000)
        if shot.get("pad"):
            pad = int(shot["pad"])
            container.evaluate(
                "(e, p) => { e.style.padding = p + 'px'; e.style.boxSizing = 'border-box'; }",
                pad,
            )
        path = out_dir / f"{shot['lang'].lower()}_{spec['slug']}.png"
        container.screenshot(path=str(path), animations="disabled")
        files.append({"path": str(path), "lang": shot["lang"], "url": BASE + shot["path"]})
        print("SHOT", gid, shot["lang"], path)
    return files


def current_user():
    return api_request(TOKEN, "GET", "/users/me", params={"opt_fields": "gid,name"}).get("data", {})


def stories(gid):
    return api_request(
        TOKEN,
        "GET",
        f"/tasks/{gid}/stories",
        params={
            "limit": 100,
            "opt_fields": "gid,created_at,resource_subtype,created_by.gid,text,html_text",
        },
    ).get("data", [])


def has_checked_comment(gid, me_gid):
    for story in stories(gid):
        if story.get("resource_subtype") != "comment_added":
            continue
        if (story.get("created_by") or {}).get("gid") != me_gid:
            continue
        text = (story.get("text") or "").strip()
        html = story.get("html_text") or ""
        if text.startswith("Checked") and "data-asana-gid" in html:
            return story
    return None


def post_one(gid, spec, files, me_gid, force=False):
    existing = has_checked_comment(gid, me_gid)
    if existing and not force:
        print("SKIP existing Checked comment", gid, existing.get("gid"))
        return existing.get("gid")

    before = {s.get("gid") for s in stories(gid)}
    uploaded = []
    for item in files:
        name = f"{gid}_{item['lang'].lower()}_{spec['slug']}.png"
        data = upload_attachment(TOKEN, gid, item["path"], name)
        uploaded.append(data["gid"])
        print("UPLOAD", gid, name, data["gid"])

    imgs = " ".join(f'<img data-asana-gid="{attachment_gid}"/>' for attachment_gid in uploaded)
    html = f"<body>Checked {imgs}</body>"
    result = api_request(
        TOKEN,
        "POST",
        f"/tasks/{gid}/stories",
        body={"data": {"html_text": html}},
        params={"opt_fields": "gid,text,html_text"},
    )
    story_gid = (result.get("data") or {}).get("gid")
    print("COMMENT", gid, story_gid, html)

    # Remove the separate attachment_added stories created by this upload.
    created = [s for s in stories(gid) if s.get("gid") not in before]
    for story in created:
        if story.get("resource_subtype") != "attachment_added":
            continue
        if (story.get("created_by") or {}).get("gid") != me_gid:
            continue
        text = story.get("text") or ""
        if any(f"{gid}_{item['lang'].lower()}_{spec['slug']}.png" in text for item in files):
            try:
                api_request(TOKEN, "DELETE", f"/stories/{story['gid']}")
                print("DELETE attachment story", story["gid"])
            except Exception as exc:
                print("WARN delete attachment story failed", story["gid"], exc)

    return story_gid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-only", action="store_true")
    parser.add_argument("--post", action="store_true")
    parser.add_argument("--only")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not args.capture_only and not args.post:
        parser.error("choose --capture-only or --post")

    gids = [args.only] if args.only else list(EVIDENCE)
    for gid in gids:
        if gid not in EVIDENCE:
            raise SystemExit(f"unknown gid {gid}")

    me_gid = current_user().get("gid")
    state = {}
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            http_credentials={"username": PRE_USER, "password": PRE_PASS},
            viewport={"width": 1440, "height": 1000},
            device_scale_factor=2,
        )
        page = context.new_page()
        for gid in gids:
            spec = EVIDENCE[gid]
            print("\n===", gid, spec["slug"])
            files = capture_one(page, gid, spec)
            if args.post:
                story_gid = post_one(gid, spec, files, me_gid, force=args.force)
                state[gid] = {"story_gid": story_gid, "files": files, "posted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
                STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        browser.close()


if __name__ == "__main__":
    main()
