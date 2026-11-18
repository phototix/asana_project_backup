#!/usr/bin/env python3
"""Read-only pre-prod checks for the Client to verify queue.

Uses the staging API that the pre-prod Next.js app already calls, plus page
labels from __NEXT_DATA__. Writes reports-data/check-results.json.

No Asana writes. No form submissions. Credentials are never written to the
report; the API Basic auth is read from the public front-end bundle or from
PREPROD_API_AUTH.
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_uat_tickets import load_env, api_request, ENV_PATH

PREPROD_BASE = "https://pre-prod.d2x7klqewcc6th.amplifyapp.com"
API_BASE = "https://api-staging.kmspks.org:83/kms-web-api/v1/"
OUT = Path(__file__).resolve().parent / "reports-data" / "check-results.json"
SGT = timezone(timedelta(hours=8))

PRE_USER = os.environ.get("PRE_USER")
PRE_PASS = os.environ.get("PRE_PASS")
if not PRE_USER or not PRE_PASS:
    sys.exit("PRE_USER and PRE_PASS are required")

SESSION = requests.Session()
SESSION.auth = (PRE_USER, PRE_PASS)
APP_JS = None

MANUAL_ACTION = "Brandon to check manually; update Dexter only if a defect is found."

ACTIVE_SECTIONS = {
    "1212426681919491": "Client to verify",
    "1212440848489031": "Fix In Progress",
    "1212440848489029": "Fail (To fix again)",
    "1212440848489033": "QA to verify",
}

EXPECTED_DEPARTMENTS = [
    ("Reception", "接待处", "6849 5300", "reception@kmspks.org"),
    ("Marketing Communications", "文宣与传播", "6849 5357", "publicaffairs@kmspks.org"),
    ("Awaken Publishing", "普觉出版社", "6849 5342", "publication@kmspks.org"),
    ("Bright Youth", "光明青年", "6849 5341", "youth@kmspks.org"),
    ("Crematorium", "火化场", "6849 5343", "crematorium@kmspks.org"),
    ("Community Engagement", "社群参与及推广", "6849 5359", "community@kmspks.org"),
    ("Dharma Education", "佛学教育", "6849 5345", "ded@kmspks.org"),
    ("Dharma School", "少儿佛学班", "6849 5329", "dharmaschool@kmspks.org"),
    ("Front Office", "寺务处", "6849 5333", "g_fo@kmspks.org"),
    ("Joyous Heart", "心悦康龄", "6849 5339", "joyousheart@kmspks.org"),
    ("Prajna Meditation Hall", "般若禅堂", "6849 5346", "meditationhall@kmspks.org"),
    ("Special Projects", "特别项目", "6849 5325", "templestay@kmspks.org"),
    ("Spiritual Events", "弘法活动", "6849 5326", "sed@kmspks.org"),
    ("Volunteer", "义工", "6849 5318", "volunteer@kmspks.org"),
]

EXPECTED_SOCIALS = {
    "facebookUrl": "https://www.facebook.com/kmspks",
    "instagramUrl": "https://www.instagram.com/kmspks_monastery",
    "youtubeUrl": "https://www.youtube.com/@kmspksmedia",
    "linkedInUrl": "https://sg.linkedin.com/company/kmspks",
    "whatsappUrl": "https://www.whatsapp.com/channel/0029VaeDmIm1SWsuTiVMGW3F",
    "xiaohongshuUrl": "https://www.rednote.com/user/profile/66a0a870000000000d026ec1",
}


def page(path):
    response = SESSION.get(PREPROD_BASE + path, timeout=30)
    response.raise_for_status()
    return response.text


def page_messages(path):
    html = page(path)
    match = re.search(
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S
    )
    if not match:
        raise RuntimeError(f"No __NEXT_DATA__ on {path}")
    data = json.loads(match.group(1))
    return data.get("props", {}).get("pageProps", {}).get("messages", {})


def app_js():
    global APP_JS
    if APP_JS is None:
        html = page("/")
        sources = re.findall(r'<script[^>]+src="([^"]+)"', html)
        app = next((src for src in sources if "/pages/_app-" in src), None)
        if not app:
            raise RuntimeError("Cannot find the _app bundle")
        APP_JS = SESSION.get(PREPROD_BASE + app, timeout=30).text
    return APP_JS


def api_auth():
    configured = os.environ.get("PREPROD_API_AUTH")
    if configured:
        return configured
    match = re.search(r'Basic "\.concat\("([^"]+)"\)', app_js())
    if not match:
        raise RuntimeError("Cannot find the API Basic auth in the _app bundle")
    return "Basic " + match.group(1)


API_AUTH = api_auth()


def api_get(path):
    response = requests.get(
        API_BASE + path,
        headers={"Authorization": API_AUTH},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["data"]


def strip_html(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()


def normalize_url(value):
    parts = urlsplit(value or "")
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", "")
    )


def active_gids():
    token = load_env(ENV_PATH)["ASANA_TOKEN"]
    found = {}
    for section_gid, section_name in ACTIVE_SECTIONS.items():
        offset = None
        while True:
            params = {"limit": 100, "opt_fields": "name"}
            if offset:
                params["offset"] = offset
            payload = api_request(token, "GET", f"/sections/{section_gid}/tasks", params=params)
            for task in payload.get("data", []):
                if (task.get("name") or "").strip():
                    found[task["gid"]] = section_name
            offset = (payload.get("next_page") or {}).get("offset")
            if not offset:
                break
    return found


def add(results, gid, result, evidence, action, label=None):
    results[gid] = {
        "result": result,
        "label": label or ("Automated check" if result in ("Pass", "Fail") else result),
        "evidence": evidence,
        "action": action,
    }


def check_career(results):
    data = api_get("careers/content")
    hours = strip_html(data["openingHours"].get("descriptionEng"))
    hours_cn = strip_html(data["openingHours"].get("descriptionCn"))
    location = strip_html(data["location"].get("descriptionEng"))
    location_cn = strip_html(data["location"].get("descriptionCn"))
    hours_ok = (
        "Monday to Friday" in hours
        and "9 to 11am, 2pm to 4pm" in hours
        and "星期一至星期五" in hours_cn
        and "上午9时至11时，下午2时至4时" in hours_cn
    )
    location_ok = (
        "Venerable Hong Choon Memorial Hall, Level 3, Human Resource Office" in location
        and "宏船老和尚纪念堂，3楼，人力资源办公室" in location_cn
    )
    en = page_messages("/join-us/career")
    zh = page_messages("/zh/join-us/career")
    label_ok = (
        en.get("careerOpeningHoursSectionHeader") == "Walk-In Interview"
        and zh.get("careerOpeningHoursSectionHeader") == "现场面试"
    )
    if hours_ok and location_ok and label_ok:
        add(
            results,
            "1219730158203178",
            "Pass",
            "Walk-In Interview label, hours and location are present in EN/CN.",
            "Pass; Brandon to confirm on pre-prod and close.",
        )
    elif hours_ok and location_ok:
        add(
            results,
            "1219730158203178",
            "Needs manual review",
            "Hours and location are present in the CMS API, but the page label is not yet “Walk-In Interview” / “现场面试”.",
            MANUAL_ACTION,
        )
    else:
        add(
            results,
            "1219730158203178",
            "Content action",
            "The CMS API does not yet contain the full Walk-In Interview hours and location in EN/CN.",
            "Update the Walk-In Interview content in the CMS and verify.",
        )


def check_bright_youth(results):
    data = api_get("bright-youth/content")
    pillars = data.get("pillars", {})
    intro_en = (
        "Get involved, discover your potential and make a difference through four "
        "dynamic pillars of Bright Youth. From community service and music to Dharma "
        "learning and sports, explore new interests, build connections and grow "
        "through meaningful experiences."
    )
    intro_cn = (
        "投入参与，贡献所长，携手成长！透过光明青年的四大支柱，探索多元参与方式，"
        "发挥潜能，为社区带来正向影响。从社区服务、梵音妙乐，到佛法修学与体育活动，"
        "发掘兴趣、广结善缘，在实践中学习与成长。"
    )
    intro_ok = intro_en in strip_html(pillars.get("descriptionEng")) and intro_cn in strip_html(
        pillars.get("descriptionCn")
    )
    pillar_ok = all(
        data.get(key, {}).get("titleEng")
        and data.get(key, {}).get("titleCn")
        and data.get(key, {}).get("descriptionEng")
        and data.get(key, {}).get("descriptionCn")
        for key in ("volunteer", "music", "dharma", "sports")
    )
    en = page_messages("/join-us/bright-youth")
    zh = page_messages("/zh/join-us/bright-youth")
    header_ok = (
        en.get("fourPillarsTitle") == "The Four Pillars of Bright Youth"
        and zh.get("fourPillarsTitle") == "光明青年的四大支柱"
    )
    if intro_ok and pillar_ok and header_ok:
        add(
            results,
            "1219729872643659",
            "Pass",
            "The Four Pillars header, intro and four pillar descriptions are present in EN/CN.",
            "Pass; Brandon to confirm on pre-prod and close.",
        )
    elif intro_ok and pillar_ok:
        add(
            results,
            "1219729872643659",
            "Needs manual review",
            "Approved intro and four pillar descriptions are present, but the page header is not the approved EN/CN text.",
            MANUAL_ACTION,
        )
    else:
        add(
            results,
            "1219729872643659",
            "Content action",
            "The CMS API is missing the approved Four Pillars intro and/or one or more pillar descriptions in EN/CN.",
            "Update the Four Pillars content in the CMS and verify.",
        )


def check_digital(results):
    en = page_messages("/awaken-online/digital")
    zh = page_messages("/zh/awaken-online/digital")
    category_ok = (
        en.get("menuAwakenOnlineDigital") == "Digital Content"
        and zh.get("menuAwakenOnlineDigital") == "数位资源"
    )
    if category_ok:
        add(
            results,
            "1219575481392590",
            "Pass",
            "“Digital Content” and “数位资源” are present in the Digital page labels.",
            "Pass; Dexter to confirm and close.",
        )
    else:
        add(
            results,
            "1219575481392590",
            "Fail",
            "The Digital page labels are not “Digital Content” / “数位资源”.",
            "Dexter to update the category label and verify.",
        )

    recommended_ok = (
        en.get("featuredDigitalTitle") == "Featured"
        and zh.get("featuredDigitalTitle") == "精选"
    )
    if recommended_ok:
        add(
            results,
            "1219575486816225",
            "Pass",
            "The Digital recommended label is “Featured” / “精选”.",
            "Pass; owner to confirm and close.",
        )
    else:
        add(
            results,
            "1219575486816225",
            "Fail",
            "The Digital label is still “Digital Recommended for You” (EN) / “数位资源” (CN); expected “Featured” / “精选”.",
            "Dexter or Kaung to update the label and verify.",
        )


def check_contact_us(results):
    data = api_get("contents/contact-us")
    sections = data.get("helpDeskSections", []) or []
    missing = []
    mismatched = []
    for title_en, title_cn, phone, email in EXPECTED_DEPARTMENTS:
        found = next(
            (section for section in sections if section.get("titleEng") == title_en),
            None,
        )
        if not found:
            missing.append(f"{title_en} / {title_cn}")
            continue
        found_phone = re.sub(r"\D", "", str(found.get("phone") or ""))
        expected_phone = re.sub(r"\D", "", phone)
        found_email = str(found.get("email") or "").strip().lower()
        if (
            found.get("titleCn") != title_cn
            or found_phone != expected_phone
            or found_email != email
        ):
            mismatched.append(f"{title_en} / {title_cn}")

    gaps = missing + mismatched
    by = next((section for section in sections if section.get("titleEng") == "Bright Youth"), {})
    jh = next((section for section in sections if section.get("titleEng") == "Joyous Heart"), {})
    by_note = str(by.get("noteEng") or "") + " " + str(by.get("noteCn") or "")
    jh_note = str(jh.get("noteEng") or "") + " " + str(jh.get("noteCn") or "")
    whatsapp_ok = "9839 6476" in by_note and "8121 1736" in jh_note
    if not gaps and whatsapp_ok:
        add(
            results,
            "1219920563795319",
            "Needs manual review",
            (
                "All 14 confirmed departments are present. WhatsApp numbers for Bright Youth "
                "and Joyous Heart are in the note area, but a dedicated WhatsApp field is still missing."
            ),
            "Dexter to add a dedicated WhatsApp field and verify.",
        )
    else:
        gap_text = (
            "All 14 confirmed departments are missing or mismatched."
            if len(gaps) == len(EXPECTED_DEPARTMENTS)
            else f"{len(gaps)} of the 14 confirmed departments are missing or mismatched."
        )
        add(
            results,
            "1219920563795319",
            "Content action",
            (
                f"The CMS API returns {len(sections)} helpdesk sections. {gap_text} "
                f"First gaps: {', '.join(gaps[:4])}. WhatsApp notes present: {whatsapp_ok}."
            ),
            "Update the 14 departments and WhatsApp notes in CMS > Contact Us > Helpdesk and verify.",
        )

    socials = {key: data.get(key, "") for key in EXPECTED_SOCIALS}
    mismatches = [
        key
        for key, expected in EXPECTED_SOCIALS.items()
        if normalize_url(socials[key]) != normalize_url(expected)
    ]
    if mismatches:
        detail = "; ".join(
            f"{key} is {socials[key]} (expected {EXPECTED_SOCIALS[key]})"
            for key in mismatches
        )
        add(
            results,
            "1219573809552366",
            "Needs manual review",
            f"{6 - len(mismatches)} of 6 social URLs match. {detail}. Brandon to review.",
            "Brandon to review the ticket; update Dexter if the YouTube URL should change.",
        )
    else:
        add(
            results,
            "1219573809552366",
            "Needs manual review",
            "All six social URLs match the confirmed links; CMS add/remove still needs a manual check.",
            "Brandon to review the ticket and check CMS add/remove.",
        )

    subjects = [
        str(subject.get("nameEng") or "")
        for subject in data.get("subjects", [])
        if subject.get("nameEng")
    ]
    has_internal = any("ENG" in subject for subject in subjects)
    add(
        results,
        "1219584601884997",
        "Needs manual review",
        (
            f"API subject labels: {', '.join(subjects)}; "
            + (
                "internal “ENG” labels are still present."
                if has_internal
                else "no “ENG” suffix, but the categories still need confirmation."
            )
        ),
        MANUAL_ACTION,
    )


def check_home(results):
    en = page_messages("/")
    zh = page_messages("/zh/")
    app = app_js()

    copy_ok = (
        en.get("labelFooterJoinMailingList")
        == "Join our mailing list to receive the latest news and updates."
        and zh.get("labelFooterJoinMailingList")
        == "订阅本寺电子报，了解最新法务与活动资讯。"
    )
    if copy_ok:
        add(
            results,
            "1219729966737873",
            "Pass",
            "Mailing-list copy matches the approved EN/CN text.",
            "Pass; Brandon to confirm on pre-prod and close.",
        )
    else:
        add(
            results,
            "1219729966737873",
            "Content action",
            "The mailing-list EN/CN copy does not match the approved text.",
            "Update the mailing-list copy in the CMS and verify.",
        )

    button_ok = (
        en.get("btnSubscribe") == "Subscribe"
        and zh.get("btnSubscribe") == "订阅"
        and bool(re.search(r'joinMailingList:\{[^}]*btnJoin:e\("btnSubscribe"\)', app))
    )
    if button_ok:
        add(
            results,
            "1219573589963215",
            "Pass",
            "The footer mailing-list component uses “Subscribe” / “订阅”.",
            "Pass; Brandon to confirm on pre-prod and close.",
        )
    else:
        add(
            results,
            "1219573589963215",
            "Fail",
            "The mailing-list button still resolves to “Join” / “加入” or is not wired to the Subscribe label.",
            "Dexter to update the mailing-list button label and verify.",
        )

    latest_ok = (
        en.get("homeLatestHappeningsTitle") == "Latest Happenings & Activities"
        and zh.get("homeLatestHappeningsTitle") == "近期动态与活动"
        and en.get("btnSeeAllArticles") == "See More"
        and zh.get("btnSeeAllArticles") == "了解更多"
    )
    if latest_ok:
        add(
            results,
            "1219730038770916",
            "Pass",
            "Latest Happenings title and See More link match the approved EN/CN text.",
            "Pass; Brandon to confirm on pre-prod and close.",
        )
    else:
        add(
            results,
            "1219730038770916",
            "Content action",
            "The Latest Happenings title or See More link does not match the approved EN/CN text.",
            "Update the Home Page labels and verify.",
        )

    upcoming_cn = zh.get("upcomingActivitiesTitle")
    if upcoming_cn == "近期活动":
        add(
            results,
            "1219729871681039",
            "Pass",
            "The Home Upcoming Activities section uses “近期活动”.",
            "Pass; Brandon to confirm on pre-prod and close.",
        )
    else:
        add(
            results,
            "1219729871681039",
            "Fail",
            f"The Home section label is “{upcoming_cn}”; expected “近期活动”.",
            "Dexter to update the Home Upcoming Activities Chinese label and verify.",
        )


def check_bright_youth_labels(results):
    en = page_messages("/join-us/bright-youth")
    zh = page_messages("/zh/join-us/bright-youth")

    membership_ok = (
        en.get("membershipRequirementsTitle") == "Becoming a Bright Youth Member"
        and zh.get("membershipRequirementsTitle") == "加入光明青年"
    )
    if membership_ok:
        add(
            results,
            "1219730214000918",
            "Pass",
            "Membership heading matches “Becoming a Bright Youth Member” / “加入光明青年”.",
            "Pass; Brandon to confirm on pre-prod and close.",
        )
    else:
        add(
            results,
            "1219730214000918",
            "Content action",
            "The Bright Youth membership heading does not match the approved EN/CN text.",
            "Update the membership heading and verify.",
        )

    empty_ok = zh.get("emptyNoUpcomingActivities") == "暂无活动"
    if empty_ok:
        add(
            results,
            "1219729885362231",
            "Pass",
            "The Bright Youth empty state uses “暂无活动”.",
            "Pass; Brandon to confirm on pre-prod and close.",
        )
    else:
        add(
            results,
            "1219729885362231",
            "Content action",
            "The Bright Youth empty state Chinese label is missing.",
            "Add “暂无活动” to the empty state and verify.",
        )

    add(
        results,
        "1219729872441193",
        "Needs manual review",
        "Section order (Intro, Four Pillars, Membership, Upcoming Activities) requires a visual check.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219730157051326",
        "Needs manual review",
        "The Bright Youth top banner image requires a visual check.",
        MANUAL_ACTION,
    )


def check_career_labels(results):
    add(
        results,
        "1219730041124358",
        "Needs manual review",
        "Both “btnApply” (CN 确定) and “btnCareerApply” (CN 申请) exist; confirm which button is rendered.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219730152343193",
        "Needs manual review",
        "Chinese text visibility on the Career page requires a visual/interaction check.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219729885998686",
        "Needs manual review",
        "Removal of the Career divider image requires a visual check.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219730214723788",
        "Needs manual review",
        "Banner text is Careers / 招聘; the updated banner image requires a visual check.",
        MANUAL_ACTION,
    )


def check_joyous_heart(results):
    en = page_messages("/join-us/joyous-heart")
    zh = page_messages("/zh/join-us/joyous-heart")
    gallery_ok = en.get("galleryTitle") == "Gallery" and zh.get("galleryTitle") == "活动相册"
    if gallery_ok:
        add(
            results,
            "1219730214327943",
            "Pass",
            "The Gallery section uses “Gallery” / “活动相册”.",
            "Pass; Brandon to confirm on pre-prod and close.",
        )
    else:
        add(
            results,
            "1219730214327943",
            "Content action",
            "The Gallery section Chinese label is missing.",
            "Add “活动相册” to the Gallery section and verify.",
        )

    data = api_get("joyous-heart/content")
    divider_note = (
        "API pageBreakImage is null; confirm visually that the redundant divider is gone."
        if data.get("pageBreakImage") is None
        else "API still returns a pageBreakImage; the divider may still be rendered."
    )
    add(
        results,
        "1219730214602139",
        "Needs manual review",
        divider_note,
        MANUAL_ACTION,
    )
    add(
        results,
        "1219730040037065",
        "Needs manual review",
        "The Joyous Heart top banner image requires a visual check.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219730157523754",
        "Needs manual review",
        "Gallery and Upcoming Activities order requires a visual check.",
        MANUAL_ACTION,
    )


def check_volunteer(results):
    data = api_get("volunteers/content")
    intro_en = (
        "Be part of a community dedicated to spreading joy and compassion through "
        "action — whether through service, work or community engagement."
    )
    intro_cn = (
        "无论是参与义工服务、加入工作团队，或投入社群活动，都欢迎您与我们同行，"
        "以行动传递温暖与慈悲。"
    )
    intro_ok = intro_en in strip_html(data.get("introDescEng")) and intro_cn in strip_html(
        data.get("introDescCn")
    )
    en = page_messages("/join-us/be-a-volunteer")
    zh = page_messages("/zh/join-us/be-a-volunteer")
    btn_en = en.get("btnJoinNow")
    btn_cn = zh.get("btnJoinNow")
    button_ok = btn_en == "Volunteer" and btn_cn == "护法义工"
    if intro_ok and button_ok:
        add(
            results,
            "1219729884657529",
            "Pass",
            "The Volunteer intro copy and button label match the approved EN/CN text.",
            "Pass; owner to confirm on pre-prod and close.",
        )
    elif intro_ok:
        add(
            results,
            "1219729884657529",
            "Needs manual review",
            (
                f"The new intro copy is live, but the intro button still reads “{btn_en}” / “{btn_cn}” "
                "instead of “Volunteer” / “护法义工”; the label is not controlled by the CMS."
            ),
            "Assign an owner to change the intro button label; it is not controlled by the CMS.",
        )
    else:
        add(
            results,
            "1219729884657529",
            "Content action",
            "The CMS API intro is still the old copy.",
            "Update the Volunteer intro copy in the CMS and verify.",
        )

    add(
        results,
        "1219729885418308",
        "Needs manual review",
        "The Join Us image replacement requires a visual check.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219730156544417",
        "Needs manual review",
        "Banner title/subtitle and image require a visual check.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219746446656349",
        "Needs manual review",
        "Section title is updated; moving Volunteer Events & Activities to the bottom requires a visual check.",
        MANUAL_ACTION,
    )


def check_cms(results):
    add(
        results,
        "1219387971268301",
        "Needs manual review",
        "CMS permalink save behaviour requires a manual CMS test.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219566240500914",
        "Needs manual review",
        "Deleting the test records requires a manual CMS test.",
        MANUAL_ACTION,
    )


def check_estore(results):
    add(
        results,
        "1219692039810792",
        "Needs manual review",
        "The specific E-Store product Chinese name requires a manual product check.",
        MANUAL_ACTION,
    )


def check_dharma(results):
    add(
        results,
        "1213988637581792",
        "Needs manual review",
        "Banner images and landing-page description require a manual/visual check.",
        MANUAL_ACTION,
    )


def manual_checks(results):
    add(
        results,
        "1219477239250114",
        "Needs manual review",
        "CMS UI check required; the edit icon is not testable from the pre-prod front end.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219575656532229",
        "Needs manual review",
        "Paragraph breaks entered in the CMS must be checked on a specific rendered article; no stable article target was found for automation.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219575604575951",
        "Needs manual review",
        "The credits description limit and fixed “Credits” title require a manual CMS check.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219575656937178",
        "Needs manual review",
        "Audio player and YouTube-link playback require a manual check on a digital post.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219575486874259",
        "Needs manual review",
        "Multiple-track upload and playback require a manual CMS check.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219584776062295",
        "Needs manual review",
        "Submission-failure handling requires a controlled manual test; do not submit the live form.",
        MANUAL_ACTION,
    )
    add(
        results,
        "1219584909565579",
        "Needs manual review",
        "The success message and mailbox delivery require a controlled test; do not submit the live form.",
        MANUAL_ACTION,
    )


def check_active_manual(results):
    add(results, "1219875631714216", "Needs manual review", "Image dimensions, aspect ratios, cropping and CMS integration for Major Events and Activities need confirmation.", "Confirm the dimensions and cropping behaviour, then verify the CMS posting workflow.")
    add(results, "1219729871505000", "Needs manual review", "The Home Page top banner and upcoming activities layout require a visual check.", "Review the banner and activities separation on pre-prod.")
    add(results, "1219729886373019", "Needs manual review", "The approved Career intro copy and replacement photo require content and visual confirmation.", "Verify the Career intro copy and photo on pre-prod.")
    add(results, "1220102256145249", "Needs manual review", "The acknowledgement email sender display name should be KMSPKS instead of KMS.", "Verify the sender display name on a pre-prod acknowledgement email.")
    add(results, "1220102726401766", "Needs manual review", "The acknowledgement email subject contains the internal [KMS-PRE-PROD] prefix; confirm it is test-only and removed for public emails.", "Verify the acknowledgement email subject and remove the internal prefix before production.")
    add(results, "1219575604730061", "Needs manual review", "Vendor reports both audio and video downloads work on pre-prod; KMS to verify the download interaction.", "Verify both download buttons and close if pass.")
    add(results, "1219477239416627", "Needs manual review", "Content field decision required: title optional and description at 500 characters.", "Confirm the field decision with Marcomm.")
    add(results, "1219636982479482", "Needs manual review", "Deletion policy required for OPEN and CLOSED courses and their related records.", "Confirm no deletion of ongoing courses; allow test or draft deletion or archive.")
    add(results, "1219584612769805", "Needs manual review", "Vendor reports the privacy notice is correct, but the floating toast still overlaps content and still says shortly; expected confirmation above the form, only after success.", "Vendor to fix the toast wording and placement; retest.")
    add(results, "1220102386894700", "Needs manual review", "Vendor is updating the acknowledgement email wording and template; verify the approved copy after deployment.", "Verify the acknowledgement email wording on pre-prod and close if pass.")
    add(results, "1220102510328267", "Needs manual review", "Vendor says the Chinese acknowledgement is done; verify the Chinese email content and reference details on pre-prod.", "Verify the Chinese acknowledgement and close if pass.")
    add(results, "1219570452486142", "Needs manual review", "Vendor verified the Contact Us banner on pre-prod; KMS or Marcomm should confirm the banner and close if pass.", "Review the banner and close if pass.")
    add(results, "1219804537175138", "Needs manual review", "Dharma School course page not found; vendor asked for the fix to be updated to pre-prod.", "Verify the course page after deployment.")
    add(results, "1219573938599764", "Needs manual review", "Vendor confirms the submitted email is stored in the database; valid, invalid and duplicate feedback still need verification.", "Verify the staging feedback and confirm before UAT.")
    add(results, "1219566240500919", "Needs manual review", "Vendor quoted 5 mandays for the Master Audit Trail change.", "Reject the CR and ask vendor to proceed within the agreed delivery.")
    add(results, "1220457628953032", "Needs manual review", "Offering Listing Stock page error has no vendor comment yet.", "Ask vendor for an update and verify the Stock page.")
    add(results, "1219961002989323", "Needs manual review", "Vendor explains the shared phone component only accepts numbers starting with 8 or 9.", "Ask for a workaround within the agreed scope for 6-prefix and multiple numbers.")
    add(results, "1219526058649071", "Needs manual review", "Vendor called Contents not loading a CR; KMS rejected the CR framing.", "Follow up and confirm the content update within the agreed scope.")
    add(results, "1219961049118002", "Needs manual review", "Vendor asks to increase Text plus Image and Text Area limits to 2000.", "Confirm the 2000-character limit decision with Marcomm.")
    add(results, "1219961154288257", "Needs manual review", "Vendor verified the Online Pledge count and preview on staging and asks for pre-prod deployment.", "Approve pre-prod deployment and verify the count and preview.")


def page_script_texts(path):
    html = page(path)
    sources = re.findall(r'<script[^>]+src="([^"]+)"', html)
    texts = []
    for src in sources:
        if src.startswith("http"):
            continue
        try:
            texts.append(SESSION.get(PREPROD_BASE + src, timeout=30).text)
        except requests.RequestException:
            continue
    return texts


def visible_first(locator):
    for i in range(locator.count()):
        item = locator.nth(i)
        try:
            if item.is_visible():
                return item
        except Exception:
            continue
    return None


def check_home_label(results, active):
    gid = "1219729871681039"
    if gid not in active:
        return
    en = page_messages("/")
    zh = page_messages("/zh/")
    en_label = en.get("upcomingActivitiesTitle")
    zh_label = zh.get("upcomingActivitiesTitle")
    if en_label == "Upcoming Activities" and zh_label == "近期活动":
        add(
            results,
            gid,
            "Pass",
            "The Home Upcoming Activities section uses “Upcoming Activities” and “近期活动”.",
            "Pass; Brandon to confirm on pre-prod and close.",
        )
    else:
        add(
            results,
            gid,
            "Fail",
            f"Home label is “{en_label}” / “{zh_label}”; expected “Upcoming Activities” / “近期活动”.",
            "Vendor to correct the Home Upcoming Activities Chinese label and retest.",
        )


def check_course_target(results, active):
    gid = "1219804537175138"
    if gid not in active:
        return
    data = api_get("dharma/content")
    course_id = data.get("courseId")
    if not course_id:
        add(
            results,
            gid,
            "Needs manual review",
            "The public dharma content API returns courseId: null, so no course page target is available. CMS course data was not checked because CMS/OTP access was skipped.",
            "Re-run the course check from the CMS/account flow when CMS access is available.",
        )
        return
    status = SESSION.get(
        PREPROD_BASE + f"/dharma-education/school/course/{course_id}",
        timeout=30,
    ).status_code
    if status == 200:
        add(
            results,
            gid,
            "Pass",
            f"Course page /dharma-education/school/course/{course_id} returns HTTP 200.",
            "Pass; KMS QA to confirm and close.",
        )
    else:
        add(
            results,
            gid,
            "Fail",
            f"Course page /dharma-education/school/course/{course_id} returns HTTP {status}.",
            "Vendor to fix the course page and retest.",
        )


def check_download_ui(page, results, active):
    gid = "1219575604730061"
    if gid not in active:
        return
    outcomes = []
    targets = [
        ("/awaken-online/digital/-3", ["Download Audio", "Download Video"]),
        ("/zh/awaken-online/digital/-3", ["下载音频", "下载视频"]),
    ]
    for path, labels in targets:
        try:
            page.goto(PREPROD_BASE + path, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
        except Exception as exc:
            outcomes.append(f"{path}: navigation failed ({exc.__class__.__name__})")
            continue
        for label in labels:
            loc = page.get_by_role("button", name=label, exact=True)
            target = visible_first(loc)
            if target is None:
                outcomes.append(f"{path} {label}: button not found")
                continue
            try:
                with page.expect_download(timeout=15000) as download_info:
                    target.click()
                download = download_info.value
                failure = download.failure()
                size = 0
                try:
                    downloaded_path = download.path()
                    size = Path(downloaded_path).stat().st_size if downloaded_path else 0
                except Exception:
                    pass
                proxy_status = None
                try:
                    probe = SESSION.get(
                        download.url,
                        timeout=30,
                        stream=True,
                        allow_redirects=False,
                    )
                    proxy_status = probe.status_code
                except Exception:
                    pass
                outcomes.append(
                    f"{path} {label}: download={download.suggested_filename or 'unnamed'}, "
                    f"size={size}, failure={failure or 'none'}, proxy_http={proxy_status}"
                )
                try:
                    download.delete()
                except Exception:
                    pass
            except Exception as exc:
                outcomes.append(f"{path} {label}: no download event ({exc.__class__.__name__})")
    passed = bool(outcomes) and all(
        "download=" in item and "failure=none" in item and "proxy_http=200" in item
        for item in outcomes
    )
    if passed:
        add(
            results,
            gid,
            "Pass",
            "Playwright download events fired for audio and video. " + " | ".join(outcomes),
            "Pass; Brandon to confirm in the browser and close.",
        )
    else:
        add(
            results,
            gid,
            "Fail",
            "Download behaviour did not pass. " + " | ".join(outcomes),
            "Vendor to fix the download behaviour and retest.",
        )


def has_link(page, text, href_part):
    links = page.locator("a")
    for i in range(links.count()):
        try:
            link = links.nth(i)
            if text in (link.inner_text() or "") and href_part in (link.get_attribute("href") or ""):
                return True
        except Exception:
            continue
    return False


def check_contact_ui(page, results, active):
    gid = "1219584612769805"
    if gid not in active:
        return
    details = []
    privacy_ok = True
    for path in ("/contact-us", "/zh/contact-us"):
        page.goto(PREPROD_BASE + path, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        body = page.locator("body").inner_text()
        if path.startswith("/zh/"):
            text_ok = "个人资料" in body and "隐私政策" in body
            link_ok = has_link(page, "隐私政策", "/zh/privacy-policy")
        else:
            text_ok = "personal data you provide" in body and "Privacy Policy" in body
            link_ok = has_link(page, "Privacy Policy", "/privacy-policy")
        details.append(f"{path}: notice={text_ok}, link={link_ok}")
        privacy_ok = privacy_ok and text_ok and link_ok

    scripts = page_script_texts("/contact-us")
    old_toast = any("shortly" in js and "successfully submitted" in js for js in scripts)
    expected_en = any(
        "Thank you! Your message has been submitted successfully." in js for js in scripts
    )
    expected_cn = any("您的信息已成功提交" in js for js in scripts)
    if privacy_ok and not old_toast and expected_en and expected_cn:
        add(
            results,
            gid,
            "Pass",
            "Privacy notice is present in EN/CN and the confirmation wording matches the approved copy. "
            + " | ".join(details),
            "Pass; KMS QA to confirm and close.",
        )
    else:
        add(
            results,
            gid,
            "Fail",
            "Privacy notice check: "
            + " | ".join(details)
            + f". Old toast still present: {old_toast}; expected EN copy present: {expected_en}; "
            f"expected CN copy present: {expected_cn}. The old toast still includes “shortly”.",
            "Vendor to replace the floating toast with the approved confirmation above the form and retest.",
        )


def check_location_ui(page, results, active):
    gid = "1219526058649071"
    if gid not in active:
        return
    details = []
    all_ok = True
    for path in ("/dharma-education/school/location", "/zh/dharma-education/school/location"):
        page.goto(PREPROD_BASE + path, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        images = page.locator("img")
        total = images.count()
        bad = 0
        for i in range(total):
            try:
                loaded = images.nth(i).evaluate("e => e.complete && e.naturalWidth > 0")
                if not loaded:
                    bad += 1
            except Exception:
                bad += 1
        details.append(f"{path}: {total - bad}/{total} images loaded")
        all_ok = all_ok and total > 0 and bad == 0
    if all_ok:
        add(
            results,
            gid,
            "Needs manual review",
            "Public Location images load on EN/CN. "
            + " | ".join(details)
            + ". CMS Location fields were not checked because CMS/OTP access was skipped.",
            "Re-run the CMS editability check when CMS access is available; then verify and close.",
        )
    else:
        add(
            results,
            gid,
            "Fail",
            "One or more Location images did not load. " + " | ".join(details),
            "Vendor to fix the missing Location images and retest.",
        )


def check_online_pledge_ui(page, results, active):
    count_gid = "1219961154288257"
    refuge_gid = "1219961002989323"
    content_gid = "1219961049118002"

    if count_gid in active:
        page.goto(PREPROD_BASE + "/activities/online-pledged", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        link = visible_first(page.get_by_role("link", name="Register Now", exact=True))
        if link is None:
            link = visible_first(page.get_by_role("link", name="立即报名", exact=True))
        if link is None:
            add(
                results,
                count_gid,
                "Fail",
                "The Online Pledge page has no visible Register Now link.",
                "Vendor to restore the registration entry point and retest.",
            )
        else:
            href = link.get_attribute("href") or ""
            absolute = href if href.startswith("http") else PREPROD_BASE + href
            response = SESSION.get(absolute, timeout=30)
            status = response.status_code
            page_not_found = "Page not found" in response.text or "页面未找到" in response.text
            if status == 404 or page_not_found:
                add(
                    results,
                    count_gid,
                    "Fail",
                    f"Register Now points to {href}, which returns HTTP {status}"
                    + (" with a page-not-found body" if page_not_found else "")
                    + ". The count selection and preview cannot be verified.",
                    "Vendor to restore the registration route, expose the 108/540/1080 options and preview, then retest.",
                )
            else:
                add(
                    results,
                    count_gid,
                    "Needs manual review",
                    f"Register Now points to {href} and returns HTTP {status}; count options and preview still need a functional check.",
                    "Verify the 108/540/1080 selection and preview, then close if pass.",
                )

    if refuge_gid in active:
        page.goto(
            PREPROD_BASE + "/activities/online-pledged/3-refuge-5-precepts",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(2500)
        phone = page.locator(
            'input[name*="phone" i], input[id*="phone" i], '
            'input[placeholder*="phone" i], input[aria-label*="phone" i]'
        )
        if phone.count() == 0:
            add(
                results,
                refuge_gid,
                "Needs manual review",
                "No phone input was found on the 3 Refuge and 5 Precepts page; the registration route returns a page-not-found body. The 6-prefix and multiple-line behaviour cannot be tested from this page.",
                "Vendor to confirm where the phone field is rendered and retest after the registration route is restored.",
            )
        else:
            add(
                results,
                refuge_gid,
                "Needs manual review",
                f"Found {phone.count()} phone input(s); the 6-prefix and multiple-line test needs controlled form data.",
                "Run a controlled phone-input test, then verify and close if pass.",
            )

    if content_gid in active:
        page.goto(PREPROD_BASE + "/activities/online-pledged", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        body = page.locator("body").inner_text()
        has_content = any(term in body for term in ("How to submit", "如何提交", "祈愿文"))
        add(
            results,
            content_gid,
            "Needs manual review",
            f"Public Online Pledge page loads; How-to-submit/prayer content present: {has_content}. "
            "The CMS Text + Image and Text Area limits were not checked because CMS/OTP access was skipped.",
            "Re-run the CMS field-limit check when CMS access is available; then verify and close.",
        )


def check_mailing_ui(page, results, active):
    gid = "1219573938599764"
    if gid not in active:
        return
    page.goto(PREPROD_BASE + "/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)
    email_inputs = page.locator('input[type="email"]')
    add(
        results,
        gid,
        "Needs manual review",
        f"Mailing-list form present with {email_inputs.count()} email input(s). "
        "Valid, invalid and duplicate feedback and the export fields require a controlled submission/CMS check; skipped.",
        "Run a controlled mailing-list test or verify the feedback and export fields manually.",
    )


def check_web_ui(results, active):
    ui_gids = {
        "1219575604730061",
        "1219584612769805",
        "1219526058649071",
        "1219961154288257",
        "1219961002989323",
        "1219961049118002",
        "1219573938599764",
    }
    if not (ui_gids & set(active)):
        return
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            http_credentials={"username": PRE_USER, "password": PRE_PASS},
            viewport={"width": 1440, "height": 1000},
            accept_downloads=True,
        )
        page_obj = context.new_page()
        try:
            for ui_check in (
                check_download_ui,
                check_contact_ui,
                check_location_ui,
                check_online_pledge_ui,
                check_mailing_ui,
            ):
                try:
                    ui_check(page_obj, results, active)
                except Exception as exc:
                    print(
                        f"WARN {ui_check.__name__}: {exc.__class__.__name__}: {exc}",
                        file=sys.stderr,
                    )
        finally:
            browser.close()


def check_cms_pending(results, active):
    pending = {
        "1220457628953032": (
            "Offering Listing Stock",
            "The CMS Offering Listing > Stock check was skipped because CMS/OTP access is unavailable.",
            "Re-run the CMS Stock check when CMS access is available.",
        ),
        "1219566240500919": (
            "Master Audit Trail cancellation reasons",
            "The CMS Master Audit Trail check was skipped because CMS/OTP access is unavailable.",
            "Re-run the audit-trail check when CMS access is available.",
        ),
        "1220102510328267": (
            "Chinese acknowledgement email",
            "The CMS/email template check was skipped because CMS/OTP access is unavailable.",
            "Re-run the Chinese acknowledgement check when CMS access is available.",
        ),
        "1220102256145249": (
            "Acknowledgement sender display name",
            "The CMS/email template check was skipped because CMS/OTP access is unavailable.",
            "Re-run the sender display name check when CMS access is available.",
        ),
        "1220102726401766": (
            "Acknowledgement email subject prefix",
            "The CMS/email template check was skipped because CMS/OTP access is unavailable.",
            "Re-run the subject prefix check when CMS access is available.",
        ),
        "1219636982479482": (
            "Dharma School test record deletion",
            "The CMS deletion check is destructive and was skipped; CMS/OTP access is also unavailable.",
            "Confirm the test-record removal with the vendor and verify without deleting live records.",
        ),
    }
    for gid, (title, evidence, action) in pending.items():
        if gid in active:
            add(results, gid, "Needs manual review", f"{title}: {evidence}", action)


def main():
    active = active_gids()
    results = {}
    checks = [
        check_home_label,
        check_course_target,
        check_web_ui,
        check_cms_pending,
    ]
    for check in checks:
        try:
            check(results, active)
        except Exception as exc:
            print(f"WARN {check.__name__}: {exc.__class__.__name__}: {exc}", file=sys.stderr)

    for gid in active:
        if gid not in results:
            add(
                results,
                gid,
                "Needs manual review",
                "No automated check completed for this ticket in this run.",
                MANUAL_ACTION,
            )

    results = {gid: result for gid, result in results.items() if gid in active}
    payload = {
        "generated_at": datetime.now(SGT).isoformat(timespec="seconds"),
        "source": "pre-prod staging API, __NEXT_DATA__ labels and Playwright; CMS checks skipped",
        "run_note": "CMS/OTP checks were skipped because the M365 service was unavailable.",
        "results": results,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)
    for gid in sorted(results):
        result = results[gid]
        print(gid, "|", result["result"], "|", result["evidence"][:180])


if __name__ == "__main__":
    main()
