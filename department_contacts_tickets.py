#!/usr/bin/env python3
"""Build the Contact Us department-contacts ticket from the Marcomm update.

Chang Xiu Mei supplied the confirmed departmental contact information and asked
Codigo to ensure every department and field can be edited in the CMS. The data
is kept inline so the ticket is self-contained for the delivery team.
"""

REQUESTER = "Chang Xiu Mei (Marcomm)"
LOCATION = "Contact Us \u2014 Department Contacts (/contact-us, /zh/contact-us)"
TITLE = "[Web & CMS] Contact Us - Department contacts completeness & CMS editability"

# (name_en, name_cn, service_en, service_cn, tel, whatsapp, email, fax)
DEPARTMENTS = [
    (
        "Reception",
        "\u63a5\u5f85\u5904",
        "General enquiries",
        "\u4e00\u822c\u54a8\u8be2",
        "6849 5300",
        "",
        "reception@kmspks.org",
        "",
    ),
    (
        "Marketing Communications",
        "\u6587\u5ba3\u4e0e\u4f20\u64ad",
        "Media enquiries and requests, public relations and feedback or suggestions "
        "for the Monastery",
        "\u5a92\u4f53\u6d3d\u8be2\u3001\u516c\u5171\u5173\u7cfb\u53ca\u5bfa\u9662\u76f8\u5173\u5efa\u8bae",
        "6849 5357",
        "",
        "publicaffairs@kmspks.org",
        "",
    ),
    (
        "Awaken Publishing",
        "\u666e\u89c9\u51fa\u7248\u793e",
        "Buddhist publications, book sponsorship and complimentary distribution",
        "\u4f5b\u6559\u51fa\u7248\u3001\u4f5b\u5b66\u4e66\u7c4d\u8d5e\u52a9\u4e0e\u7ed3\u7f18",
        "6849 5342",
        "",
        "publication@kmspks.org",
        "",
    ),
    (
        "Bright Youth",
        "\u5149\u660e\u9752\u5e74",
        "Programmes and activities for youths",
        "\u9752\u5e74\u8bfe\u7a0b\u4e0e\u6d3b\u52a8",
        "6849 5341",
        "9839 6476",
        "youth@kmspks.org",
        "",
    ),
    (
        "Crematorium",
        "\u706b\u5316\u573a",
        "Cremation and Ji Ling services",
        "\u706b\u5316\u4e0e\u5bc4\u7075\u670d\u52a1",
        "6849 5343",
        "",
        "crematorium@kmspks.org",
        "",
    ),
    (
        "Community Engagement",
        "\u793e\u7fa4\u53c2\u4e0e\u53ca\u63a8\u5e7f",
        "Community programmes, outreach and activities",
        "\u793e\u533a\u63a8\u5e7f\u3001\u8bfe\u7a0b\u4e0e\u6d3b\u52a8",
        "6849 5359",
        "",
        "community@kmspks.org",
        "",
    ),
    (
        "Dharma Education",
        "\u4f5b\u5b66\u6559\u80b2",
        "Adult Dharma classes",
        "\u6210\u4eba\u4f5b\u5b66\u73ed",
        "6849 5345",
        "",
        "ded@kmspks.org",
        "",
    ),
    (
        "Dharma School",
        "\u5c11\u513f\u4f5b\u5b66\u73ed",
        "Children\u2019s Dharma classes",
        "\u5c11\u513f\u4f5b\u5b66\u73ed",
        "6849 5329",
        "",
        "dharmaschool@kmspks.org",
        "",
    ),
    (
        "Front Office",
        "\u5bfa\u52a1\u5904",
        "Private prayer services, columbarium niche and memorial tablet applications, "
        "and donations",
        "\u796d\u62dc\u670d\u52a1\u3001\u9aa8\u7070\u4f4d\u53ca\u724c\u4f4d\u7533\u8bf7\uff0c\u4ee5\u53ca\u6350\u6b3e\u54a8\u8be2",
        "6849 5333",
        "",
        "g_fo@kmspks.org",
        "+65 6456 2151",
    ),
    (
        "Joyous Heart",
        "\u5fc3\u60a6\u5eb7\u9f84",
        "Programmes and activities for seniors",
        "\u4e50\u9f84\u8bfe\u7a0b\u4e0e\u6d3b\u52a8",
        "6849 5339",
        "8121 1736",
        "joyousheart@kmspks.org",
        "",
    ),
    (
        "Prajna Meditation Hall",
        "\u822c\u82e5\u7985\u5802",
        "Meditation programmes and retreats",
        "\u7985\u4fee\u6d3b\u52a8",
        "6849 5346",
        "",
        "meditationhall@kmspks.org",
        "",
    ),
    (
        "Special Projects",
        "\u7279\u522b\u9879\u76ee",
        "Monastic ordination and temple stays",
        "\u51fa\u5bb6\u53d7\u6212\u53ca\u5bfa\u9662\u751f\u6d3b\u9759\u4fee",
        "6849 5325",
        "",
        "templestay@kmspks.org",
        "",
    ),
    (
        "Spiritual Events",
        "\u5f18\u6cd5\u6d3b\u52a8",
        "Dharma events and Buddhist ceremonies",
        "\u6cd5\u4f1a\u6d3b\u52a8",
        "6849 5326",
        "",
        "sed@kmspks.org",
        "",
    ),
    (
        "Volunteer",
        "\u4e49\u5de5",
        "Volunteer opportunities",
        "\u4e49\u5de5\u670d\u52a1",
        "6849 5318",
        "",
        "volunteer@kmspks.org",
        "",
    ),
]


def render_departments() -> str:
    lines = []
    for index, dept in enumerate(DEPARTMENTS, start=1):
        name_en, name_cn, service_en, service_cn, tel, whatsapp, email, fax = dept
        lines.append(f"{index}. {name_en} / {name_cn}")
        lines.append(f"   Service (EN): {service_en}")
        lines.append(f"   Service (CN): {service_cn}")
        lines.append(f"   Tel: {tel}")
        if whatsapp:
            lines.append(f"   WhatsApp: {whatsapp}")
        lines.append(f"   Email: {email}")
        if fax:
            lines.append(f"   Fax: {fax}")
        lines.append("")
    return "\n".join(lines).rstrip()


def build_notes() -> str:
    return (
        f"Requester: {REQUESTER}\n\n"
        f"Location: {LOCATION}\n\n"
        "Issue / Observation:\n"
        "Marcomm has supplied the confirmed departmental contact information. "
        "The Department Contacts content is incomplete and must be fully editable "
        "in the CMS by non-technical users.\n\n"
        "Expected:\n"
        "- All 14 departments below are displayed in English and Chinese.\n"
        "- Each department supports the EN/CN name, EN/CN service description, "
        "telephone, WhatsApp (where applicable), email and fax (where applicable).\n"
        "- Department entries and every field can be added, edited, removed and "
        "reordered in the CMS without code changes.\n\n"
        "Acceptance criteria:\n"
        "1. All 14 departments appear on /contact-us and /zh/contact-us.\n"
        "2. Contact details match the confirmed list exactly.\n"
        "3. Any department can be added, edited, removed or reordered in the CMS.\n"
        "4. CMS changes appear on pre-prod without a code change.\n"
        "5. Layout renders correctly on desktop and mobile.\n\n"
        "Confirmed department information:\n\n"
        f"{render_departments()}\n"
    )


def build_tickets():
    return [
        {
            "id": "department-contacts",
            "title": TITLE,
            "notes": build_notes(),
        }
    ]


if __name__ == "__main__":
    for ticket in build_tickets():
        print(ticket["title"])
        print(ticket["notes"])
