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

EXPECTED_CURRENT = {
    "1219477239250114",
    "1219566240500914",
    "1219575486874259",
    "1219575656937178",
    "1219584776062295",
    "1219729871681039",
    "1219729884657529",
    "1219729885998686",
    "1219730041124358",
    "1219730152343193",
    "1219730156544417",
    "1219730157051326",
    "1219730157523754",
    "1219730214602139",
    "1219730214723788",
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


def main():
    results = {}
    check_career(results)
    check_bright_youth(results)
    check_digital(results)
    check_contact_us(results)
    check_home(results)
    check_bright_youth_labels(results)
    check_career_labels(results)
    check_joyous_heart(results)
    check_volunteer(results)
    check_cms(results)
    check_estore(results)
    check_dharma(results)
    manual_checks(results)

    results = {gid: result for gid, result in results.items() if gid in EXPECTED_CURRENT}
    missing = EXPECTED_CURRENT - set(results)
    extra = set(results) - EXPECTED_CURRENT
    if missing or extra:
        raise RuntimeError(f"check coverage mismatch; missing={sorted(missing)} extra={sorted(extra)}")

    payload = {
        "generated_at": datetime.now(SGT).isoformat(timespec="seconds"),
        "source": "pre-prod staging API and __NEXT_DATA__ labels",
        "results": results,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)
    for gid, result in results.items():
        print(gid, "|", result["result"], "|", result["evidence"][:150])


if __name__ == "__main__":
    main()
