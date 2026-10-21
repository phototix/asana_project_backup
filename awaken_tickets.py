#!/usr/bin/env python3
"""Build [Awaken Online] UAT ticket definitions from the client Excel workbook.

The workbook has one sheet per Awaken Online module (About Us, Publication,
Awaken Magazine, Articles, Digital) with columns Section | Current | Edits |
Remarks, plus embedded screenshots anchored next to each row.

Tickets are grouped by module + section. This module downloads/parses the
workbook, extracts the embedded images, and returns ticket dicts consumed by
create_uat_tickets.py.
"""
import io
import os
import re
import urllib.request
import zipfile
from collections import OrderedDict
from pathlib import Path
import xml.etree.ElementTree as ET


SOURCE_URL = "https://cloud.webbypage.com/index.php/s/NzpzQNt6r5sRY2m/download"
WORKBOOK_NAME = "Website edits - Awaken Online.xlsx"
SHEETS = ["About Us", "Publication", "Awaken Magazine", "Articles", "Digital"]
SECTION_TITLE_FIX = {
    "Rocommended for You": "Recommended for You",
    '"Ends On" Fenction': '"Ends On" Function',
}
COLUMNS = {1: "Section", 2: "Current", 3: "Edits", 4: "Remarks"}


def download(work_dir: Path) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    path = work_dir / WORKBOOK_NAME
    if not path.exists() or path.stat().st_size == 0:
        req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=600) as resp, path.open("wb") as out:
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                out.write(chunk)
    return path


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _col_idx(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref or "")
    if not letters:
        return 0
    n = 0
    for ch in letters.group(0):
        n = n * 26 + (ord(ch) - 64)
    return n


def _shared_strings(z: zipfile.ZipFile):
    strings = []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    for si in list(root):
        strings.append("".join(t.text or "" for t in si.iter() if _local(t.tag) == "t"))
    return strings


def _sheet_targets(z: zipfile.ZipFile):
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid_target = {
        r.get("Id"): r.get("Target")
        for r in list(rels)
        if r.get("Id") and r.get("Target")
    }
    targets = {}
    for sh in wb.iter():
        if _local(sh.tag) != "sheet":
            continue
        rid = next((v for k, v in sh.attrib.items() if k.endswith("}id")), None)
        target = rid_target.get(rid, "")
        if target and not target.startswith("xl/"):
            target = "xl/" + target.lstrip("/")
        targets[sh.get("name")] = target
    return targets


def _rows(z: zipfile.ZipFile, sheet_target: str, strings):
    root = ET.fromstring(z.read(sheet_target))
    out = []
    for row in root.iter():
        if _local(row.tag) != "row":
            continue
        rownum = int(row.get("r"))
        cells = {}
        for c in list(row):
            if _local(c.tag) != "c":
                continue
            ref = c.get("r") or ""
            ctype = c.get("t")
            value = None
            for ch in c.iter():
                if _local(ch.tag) == "v":
                    value = ch.text
            if value is None:
                continue
            if ctype == "s":
                try:
                    value = strings[int(value)]
                except (ValueError, IndexError):
                    pass
            cells[_col_idx(ref)] = value
        if cells:
            out.append((rownum, cells))
    return out


def _images(z: zipfile.ZipFile, sheet_target: str):
    base = os.path.basename(sheet_target)
    rel_path = f"xl/worksheets/_rels/{base}.rels"
    drawing_target = None
    if rel_path in z.namelist():
        rels = ET.fromstring(z.read(rel_path))
        for rel in list(rels):
            if rel.get("Type", "").endswith("/drawing"):
                drawing_target = rel.get("Target")
    if not drawing_target:
        return {}
    drawing_path = "xl/" + drawing_target.replace("../", "")
    drawing_rels = "xl/drawings/_rels/" + os.path.basename(drawing_path) + ".rels"
    rid_media = {}
    if drawing_rels in z.namelist():
        rels = ET.fromstring(z.read(drawing_rels))
        for rel in list(rels):
            if rel.get("Id") and rel.get("Target"):
                rid_media[rel.get("Id")] = os.path.basename(rel.get("Target"))
    drawing = ET.fromstring(z.read(drawing_path))
    by_row = {}
    for anchor in drawing.iter():
        if not _local(anchor.tag).endswith("Anchor"):
            continue
        rownum = colnum = None
        for child in list(anchor):
            if _local(child.tag) == "from":
                for ch in list(child):
                    if _local(ch.tag) == "row":
                        rownum = int(ch.text)
                    if _local(ch.tag) == "col":
                        colnum = int(ch.text)
        embed = None
        for blip in anchor.iter():
            if _local(blip.tag) == "blip":
                embed = next((v for k, v in blip.attrib.items() if k.endswith("}embed")), None)
        media = rid_media.get(embed)
        if rownum is not None and media:
            by_row.setdefault(rownum + 1, []).append((colnum, media))
    return by_row


def _clean(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if re.fullmatch(r"#\w+[!?]?", text):
        return ""
    return text


def _safe(name: str) -> str:
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name).strip()
    return name[:180] or "image"


def _normalize_image(src: Path, dst: Path):
    """Re-encode to a clean standard file, stripping Apple iDOT/iCCP/eXIf chunks.

    Excel stores many of these screenshots as macOS-optimized PNGs whose
    non-standard iDOT chunk makes viewers render them scrambled. Re-encoding
    with Pillow produces a plain PNG/JPEG that displays correctly everywhere.
    """
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


def render_notes(module: str, section: str, group) -> str:
    blocks = []
    for _, cells in group:
        for column in (2, 3, 4):  # Current, Edits, Remarks
            text = _clean(cells.get(column))
            if text:
                blocks.append(text)
    return "\n\n".join(blocks).rstrip() + "\n"


def build_tickets(work_dir: Path):
    path = download(work_dir)
    with zipfile.ZipFile(io.BytesIO(path.read_bytes())) as z:
        strings = _shared_strings(z)
        targets = _sheet_targets(z)
        raw_dir = work_dir / "media"
        clean_dir = work_dir / "media_clean"
        raw_dir.mkdir(parents=True, exist_ok=True)
        clean_dir.mkdir(parents=True, exist_ok=True)
        media_paths = {}
        for name in z.namelist():
            if name.startswith("xl/media/"):
                base = os.path.basename(name)
                raw = raw_dir / base
                if not raw.exists():
                    raw.write_bytes(z.read(name))
                clean = clean_dir / base
                if not clean.exists():
                    try:
                        _normalize_image(raw, clean)
                    except Exception:
                        clean.write_bytes(raw.read_bytes())
                media_paths[base] = clean
        tickets = []
        for sheet in SHEETS:
            target = targets.get(sheet)
            if not target:
                continue
            rows = _rows(z, target, strings)
            images = _images(z, target)
            groups = OrderedDict()
            for rownum, cells in rows:
                if rownum == 1:
                    continue
                section = (cells.get(1) or "").strip() or "Footer CTAs"
                groups.setdefault(section, []).append((rownum, cells))
            for section, group in groups.items():
                display = SECTION_TITLE_FIX.get(section, section)
                attachments = []
                for rownum, _ in group:
                    for idx, (_, media) in enumerate(images.get(rownum, []), start=1):
                        if media in media_paths:
                            attachments.append(
                                {
                                    "path": str(media_paths[media]),
                                    "name": _safe(f"{sheet} - {display} (r{rownum}) {idx} {media}"),
                                }
                            )
                tickets.append(
                    {
                        "id": f"{sheet}-{section}",
                        "title": f"[Web] Awaken Online - {sheet} - {display}",
                        "module": sheet,
                        "section": display,
                        "notes": render_notes(sheet, display, group),
                        "attachments": attachments,
                    }
                )
    return tickets


if __name__ == "__main__":
    import sys

    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/opencode/awaken")
    for t in build_tickets(out_dir):
        print(f"{t['title']}  [images={len(t['attachments'])}]")
