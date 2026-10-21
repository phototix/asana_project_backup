#!/usr/bin/env python3
"""Generate a standalone HTML report from a Markdown report.

The generated HTML is written to reports-data/ and is served by index.php
behind the existing login. Ticket GIDs and Asana URLs are converted to links.
"""

import argparse
import html
import re
import shutil
from datetime import datetime
from pathlib import Path

TASK_URL = "https://app.asana.com/1/1610754927873/project/1212423157941626/task/{gid}"

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="report-title" content="{title_attr}">
<meta name="report-date" content="{date_iso}">
<meta name="report-summary" content="{summary_attr}">
<style>
:root{{--bg:#f7f4ee;--panel:#fffdf8;--ink:#1f1a12;--muted:#6d5f4e;--line:#ddd2bf;--accent:#7d2b1f;--accent2:#652116;--pass:#24522a;--passbg:#f0f7ee;--fail:#8c261a;--failbg:#fff0ee;--review:#6a4319;--reviewbg:#fff6e8;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:Georgia,"Times New Roman",serif;line-height:1.55}}
.page{{max-width:1120px;margin:0 auto;padding:1.25rem 1.25rem 2rem}}
.top{{display:flex;align-items:center;justify-content:space-between;gap:1rem;border-bottom:1px solid var(--line);padding-bottom:.75rem;margin-bottom:.9rem}}
.brand{{font-size:1.05rem;letter-spacing:.02em}}
.back{{color:var(--accent);text-decoration:none;font-size:.95rem}}
.back:hover{{text-decoration:underline}}
.meta{{color:var(--muted);font-size:.9rem;margin:0 0 1.2rem}}
.content h1{{font-size:1.65rem;line-height:1.25;margin:0 0 .7rem}}
.content h2{{font-size:1.2rem;margin:1.7rem 0 .55rem;border-bottom:1px solid var(--line);padding-bottom:.28rem}}
.content h3{{font-size:1.02rem;margin:1.2rem 0 .4rem}}
.content p{{margin:.55rem 0}}
.content a{{color:var(--accent);overflow-wrap:anywhere}}
.content strong{{font-weight:700}}
.content code{{background:#f0e6d7;border-radius:4px;padding:.1rem .25rem;font-size:.9em}}
.content hr{{border:0;border-top:1px solid var(--line);margin:1.2rem 0}}
.content ul,.content ol{{margin:.45rem 0 .75rem 1.35rem;padding:0}}
.content li{{margin:.25rem 0}}
.table-wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:8px;margin:.8rem 0 1rem;background:var(--panel)}}
table{{width:100%;border-collapse:collapse;font-size:.92rem}}
th,td{{border-bottom:1px solid #eee2cf;padding:.55rem .6rem;text-align:left;vertical-align:top}}
th{{background:#f0e4d2;font-family:Arial,Helvetica,sans-serif;font-size:.78rem;text-transform:uppercase;letter-spacing:.04em}}
tr:last-child td{{border-bottom:none}}
.badge{{display:inline-block;border-radius:999px;padding:.12rem .48rem;font-family:Arial,Helvetica,sans-serif;font-size:.78rem;font-weight:700;white-space:nowrap}}
.badge.pass{{background:var(--passbg);color:var(--pass);border:1px solid #bdd9b8}}
.badge.fail{{background:var(--failbg);color:var(--fail);border:1px solid #e2b8b0}}
.badge.review{{background:var(--reviewbg);color:var(--review);border:1px solid #e1c89f}}
footer{{margin-top:2rem;border-top:1px solid var(--line);padding-top:.8rem;color:var(--muted);font-size:.85rem}}
@media print{{body{{background:#fff}}.top,.back,footer{{display:none}}.page{{max-width:none;padding:0}}.table-wrap{{overflow:visible;border:0}}th{{background:#eee}}tr{{break-inside:avoid}}a{{color:inherit;text-decoration:none}}}}
</style>
</head>
<body>
<div class="page">
<header class="top">
<div class="brand">KMSPKS UAT Reports</div>
<a class="back" href="/reports">&larr; All reports</a>
</header>
<div class="meta">Generated {generated} SGT</div>
<article class="content">
{content}
</article>
<footer>KMSPKS UAT reporting portal. This report is available only to signed-in users.</footer>
</div>
</body>
</html>
"""


def protect_links(text):
    links = []

    def markdown_link(match):
        links.append(("md", match.group(1), match.group(2)))
        return f"\x00L{len(links) - 1}\x00"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", markdown_link, text)

    def bare_url(match):
        url = match.group(0)
        trailing = ""
        while url and url[-1] in ".,;:":
            trailing = url[-1] + trailing
            url = url[:-1]
        links.append(("url", url, url))
        return f"\x00L{len(links) - 1}\x00{trailing}"

    text = re.sub(r'https?://[^\s<>"]+', bare_url, text)
    return text, links


def render_inline(text):
    protected, links = protect_links(text)
    out = html.escape(protected, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(
        r"\b(121\d{13})\b",
        lambda m: f'<a href="{TASK_URL.format(gid=m.group(1))}" target="_blank" rel="noopener noreferrer">{m.group(1)}</a>',
        out,
    )

    def restore(match):
        _, label, target = links[int(match.group(1))]
        attrs = ' target="_blank" rel="noopener noreferrer"' if target.startswith("https://app.asana.com/") else ""
        return f'<a href="{html.escape(target, quote=True)}"{attrs}>{html.escape(label, quote=False)}</a>'

    return re.sub(r"\x00L(\d+)\x00", restore, out)


def split_row(line):
    value = line.strip()
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [cell.strip() for cell in value.split("|")]


def is_table_separator(line):
    return re.match(r"^\s*\|?\s*:?-{3,}", line) is not None


def render_cell(cell):
    value = cell.strip()
    low = value.lower()
    if low in ("pass", "closed"):
        return f'<span class="badge pass">{render_inline(value)}</span>'
    if low in ("fail", "failed") or low.startswith("fail ("):
        return f'<span class="badge fail">{render_inline(value)}</span>'
    if (
        low.startswith("needs review")
        or low.startswith("needs manual")
        or low.startswith("pending verification")
        or low == "client to verify"
    ):
        return f'<span class="badge review">{render_inline(value)}</span>'
    return render_inline(value)


def convert_markdown(markdown):
    lines = markdown.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        if line.strip().startswith("```"):
            i += 1
            block = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            out.append("<pre><code>" + html.escape("\n".join(block)) + "</code></pre>")
            continue

        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading:
            level = len(heading.group(1))
            out.append(f"<h{level}>{render_inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        if re.match(r"^\s*(\*\s*){3,}$", line) or re.match(r"^\s*-{3,}\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        if (
            i + 1 < len(lines)
            and line.strip().startswith("|")
            and is_table_separator(lines[i + 1])
        ):
            header = split_row(line)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            table = ['<div class="table-wrap"><table><thead><tr>']
            for cell in header:
                table.append(f"<th>{render_inline(cell)}</th>")
            table.append("</tr></thead><tbody>")
            for row in rows:
                table.append("<tr>")
                for cell in row:
                    table.append(f"<td>{render_cell(cell)}</td>")
                table.append("</tr>")
            table.append("</tbody></table></div>")
            out.append("".join(table))
            continue

        list_match = re.match(r"^\s*([-*]|\d+\.)\s+(.*)$", line)
        if list_match:
            ordered = list_match.group(1).endswith(".")
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines):
                item_match = re.match(r"^\s*([-*]|\d+\.)\s+(.*)$", lines[i])
                if not item_match:
                    break
                items.append(f"<li>{render_inline(item_match.group(2))}</li>")
                i += 1
            out.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue

        paragraph = [line.strip()]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if not nxt.strip():
                break
            if nxt.startswith("#") or nxt.strip().startswith("|"):
                break
            if re.match(r"^\s*([-*]|\d+\.)\s+", nxt):
                break
            if nxt.strip().startswith("```"):
                break
            paragraph.append(nxt.strip())
            i += 1
        out.append(f"<p>{render_inline(' '.join(paragraph))}</p>")

    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Generate an HTML UAT report.")
    parser.add_argument("--input", required=True, help="Markdown report path")
    parser.add_argument("--slug", required=True, help="Short kebab-case summary slug")
    parser.add_argument("--title", required=True, help="Human-readable report title")
    parser.add_argument("--datetime", default=datetime.now().strftime("%Y-%m-%d %H:%M"), help="Report date/time, e.g. 2026-10-21 21:00")
    parser.add_argument("--summary", default="", help="Short summary for the reports index")
    parser.add_argument("--output-dir", default=str(Path(__file__).resolve().parent / "reports-data"))
    args = parser.parse_args()

    try:
        when = datetime.strptime(args.datetime, "%Y-%m-%d %H:%M")
    except ValueError:
        when = datetime.fromisoformat(args.datetime)

    source = Path(args.input)
    markdown = source.read_text(encoding="utf-8")
    base = f"{when.strftime('%Y-%m-%d-%H%M')}-{args.slug}"

    output_dir = Path(args.output_dir)
    source_dir = output_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)

    document = PAGE.format(
        title=html.escape(args.title, quote=False),
        title_attr=html.escape(args.title, quote=True),
        date_iso=when.strftime("%Y-%m-%dT%H:%M:00+08:00"),
        summary_attr=html.escape(args.summary, quote=True),
        generated=when.strftime("%d %b %Y, %I:%M %p"),
        content=convert_markdown(markdown),
    )

    output_path = output_dir / f"{base}.html"
    output_path.write_text(document, encoding="utf-8")
    source_copy = source_dir / f"{base}.md"
    if source.resolve() != source_copy.resolve():
        shutil.copyfile(source, source_copy)
    print(output_path)


if __name__ == "__main__":
    main()
