#!/usr/bin/env python3
import fcntl
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ENV_PATH = Path("/opt/asana-backup/.env")
WEB_ROOT = Path("/var/www/codigo.brandon.my")
FILES_ROOT = WEB_ROOT / "files"
DATA_ROOT = WEB_ROOT / "data"
TMP_ROOT = WEB_ROOT / "tmp"
LOCK_PATH = Path("/var/lock/asana-backup.lock")
API_BASE = "https://app.asana.com/api/1.0"


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


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return value or "project"


def safe_name(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value).strip()
    return value[:180] or "file"


def request_json(token: str, url: str, params=None, retries: int = 5):
    if params:
        q = urllib.parse.urlencode(params)
        joiner = "&" if "?" in url else "?"
        url = f"{url}{joiner}{q}"

    for attempt in range(retries):
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                wait = int(exc.headers.get("Retry-After", "5"))
                time.sleep(wait)
                continue
            if 500 <= exc.code < 600 and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            body = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP {exc.code} for {url}: {body[:500]}")
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise


def paginate(token: str, endpoint: str, params=None):
    params = dict(params or {})
    items = []
    offset = None
    while True:
        req_params = dict(params)
        req_params.setdefault("limit", 100)
        if offset:
            req_params["offset"] = offset
        payload = request_json(token, f"{API_BASE}{endpoint}", req_params)
        data = payload.get("data", [])
        items.extend(data)
        next_page = payload.get("next_page")
        if not next_page or not next_page.get("offset"):
            break
        offset = next_page["offset"]
    return items


def download_binary(token: str, url: str, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    headers = {"Authorization": f"Bearer {token}"}
    for use_auth in (True, False):
        try:
            req = urllib.request.Request(url, headers=headers if use_auth else {})
            with urllib.request.urlopen(req, timeout=180) as resp, target.open("wb") as out:
                shutil.copyfileobj(resp, out)
            return True
        except Exception:
            continue
    return False


def extract_urls(html: str):
    if not html:
        return []
    urls = set()
    for pat in (r'src=["\']([^"\']+)["\']', r'href=["\']([^"\']+)["\']'):
        for m in re.findall(pat, html, flags=re.IGNORECASE):
            if m.startswith("http://") or m.startswith("https://"):
                urls.add(m)
    return sorted(urls)


def backup_project(token: str, project: dict, run_stamp: str, now_iso: str):
    project_gid = str(project["gid"])
    project_name = project.get("name") or f"project-{project_gid}"
    project_slug = f"{slugify(project_name)}-{project_gid}"

    project_tmp = TMP_ROOT / run_stamp / project_slug
    tasks_dir = project_tmp / "tasks"
    comments_dir = project_tmp / "comments"
    attachment_dir = project_tmp / "attachments"
    inline_dir = project_tmp / "inline-assets"
    for d in (tasks_dir, comments_dir, attachment_dir, inline_dir):
        d.mkdir(parents=True, exist_ok=True)

    sections = paginate(
        token,
        f"/projects/{project_gid}/sections",
        {"opt_fields": "gid,name"},
    )
    (project_tmp / "sections.json").write_text(
        json.dumps(sections, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    task_stubs = paginate(
        token,
        f"/projects/{project_gid}/tasks",
        {
            "completed_since": "1970-01-01T00:00:00Z",
            "opt_fields": "gid,name,modified_at",
        },
    )

    task_count = 0
    comment_count = 0
    attachment_count = 0
    inline_count = 0

    for task_stub in task_stubs:
        task_gid = str(task_stub["gid"])
        task = request_json(
            token,
            f"{API_BASE}/tasks/{task_gid}",
            {
                "opt_fields": (
                    "gid,name,notes,html_notes,resource_subtype,created_at,created_by.gid,created_by.name,created_by.email,modified_at,modified_by.gid,modified_by.name,modified_by.email,last_modified_by.gid,last_modified_by.name,last_modified_by.email,"
                    "completed,completed_at,due_on,due_at,start_on,start_at,permalink_url,"
                    "assignee.gid,assignee.name,parent.gid,parent.name,"
                    "memberships.section.gid,memberships.section.name,"
                    "followers.gid,followers.name,tags.gid,tags.name,"
                    "custom_fields.gid,custom_fields.name,custom_fields.display_value"
                )
            },
        ).get("data", {})

        task_file = tasks_dir / f"{task_gid}.json"
        task_file.write_text(json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8")
        task_count += 1

        stories = paginate(
            token,
            f"/tasks/{task_gid}/stories",
            {"opt_fields": "gid,type,resource_subtype,text,html_text,created_at,created_by.gid,created_by.name"},
        )
        comments = [
            s
            for s in stories
            if s.get("resource_subtype") == "comment_added" or s.get("type") == "comment"
        ]
        comment_count += len(comments)
        (comments_dir / f"{task_gid}.json").write_text(
            json.dumps(comments, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        attachments = paginate(
            token,
            f"/tasks/{task_gid}/attachments",
            {"opt_fields": "gid,name,download_url,view_url,permanent_url,resource_subtype,created_at,host,size"},
        )

        att_meta = []
        for idx, att in enumerate(attachments, start=1):
            src = att.get("download_url") or att.get("view_url") or att.get("permanent_url")
            att_name = safe_name(att.get("name") or f"attachment-{idx}")
            target = attachment_dir / task_gid / f"{idx:03d}-{att_name}"
            downloaded = bool(src) and download_binary(token, src, target)
            if downloaded:
                attachment_count += 1
            att_meta.append({
                "task_gid": task_gid,
                "downloaded": downloaded,
                "saved_as": str(target.relative_to(project_tmp)) if downloaded else None,
                **att,
            })

        (attachment_dir / task_gid / "_meta.json").parent.mkdir(parents=True, exist_ok=True)
        (attachment_dir / task_gid / "_meta.json").write_text(
            json.dumps(att_meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        inline_urls = set(extract_urls(task.get("html_notes", "")))
        for c in comments:
            inline_urls.update(extract_urls(c.get("html_text", "")))
        inline_meta = []
        for idx, url in enumerate(sorted(inline_urls), start=1):
            parsed = urllib.parse.urlparse(url)
            basename = safe_name(os.path.basename(parsed.path) or f"asset-{idx}")
            target = inline_dir / task_gid / f"{idx:03d}-{basename}"
            downloaded = download_binary(token, url, target)
            if downloaded:
                inline_count += 1
            inline_meta.append(
                {
                    "task_gid": task_gid,
                    "url": url,
                    "downloaded": downloaded,
                    "saved_as": str(target.relative_to(project_tmp)) if downloaded else None,
                }
            )
        (inline_dir / task_gid / "_meta.json").parent.mkdir(parents=True, exist_ok=True)
        (inline_dir / task_gid / "_meta.json").write_text(
            json.dumps(inline_meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    manifest = {
        "generated_at": now_iso,
        "project": {
            "gid": project_gid,
            "name": project_name,
            "slug": project_slug,
            "workspace": project.get("workspace"),
        },
        "counts": {
            "tasks": task_count,
            "comments": comment_count,
            "attachments_downloaded": attachment_count,
            "inline_assets_downloaded": inline_count,
            "sections": len(sections),
        },
        "sections": sections,
    }
    (project_tmp / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    project_file_dir = FILES_ROOT / project_slug
    project_file_dir.mkdir(parents=True, exist_ok=True)
    zip_name = f"asana-backup-{project_slug}-{run_stamp}.zip"
    zip_path = project_file_dir / zip_name
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in project_tmp.rglob("*"):
            if item.is_file():
                zf.write(item, arcname=str(item.relative_to(project_tmp)))

    project_data_dir = DATA_ROOT / project_slug
    project_data_dir.mkdir(parents=True, exist_ok=True)
    (project_data_dir / f"manifest-{run_stamp}.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return {
        "project_gid": project_gid,
        "project_name": project_name,
        "project_slug": project_slug,
        "zip_file": zip_name,
        "zip_size": zip_path.stat().st_size,
        "run_stamp": run_stamp,
        "generated_at": now_iso,
        "counts": manifest["counts"],
    }


def _read_json_file(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _parse_run_stamp(zip_name: str):
    m = re.search(r"-(\d{8}-\d{6})\.zip$", zip_name)
    return m.group(1) if m else ""


def build_global_index(records):
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    FILES_ROOT.mkdir(parents=True, exist_ok=True)

    current_by_zip = {
        (str(rec.get("project_slug", "")), str(rec.get("zip_file", ""))): rec
        for rec in records
        if rec.get("project_slug") and rec.get("zip_file")
    }

    project_meta = {}
    for rec in records:
        slug = str(rec.get("project_slug", ""))
        if not slug:
            continue
        project_meta[slug] = {
            "project_name": str(rec.get("project_name", slug)),
            "project_gid": str(rec.get("project_gid", "")),
        }

    existing_index_path = DATA_ROOT / "backups.json"
    if existing_index_path.exists():
        existing_index = _read_json_file(existing_index_path)
        for project in existing_index.get("projects", []):
            slug = str(project.get("project_slug", ""))
            if not slug or slug in project_meta:
                continue
            project_meta[slug] = {
                "project_name": str(project.get("project_name", slug)),
                "project_gid": str(project.get("project_gid", "")),
            }

    grouped = {}
    for project_dir in sorted(FILES_ROOT.iterdir()) if FILES_ROOT.exists() else []:
        if not project_dir.is_dir():
            continue
        slug = project_dir.name

        manifest_map = {}
        project_manifest_dir = DATA_ROOT / slug
        if project_manifest_dir.exists():
            for manifest_path in project_manifest_dir.glob("manifest-*.json"):
                stamp = manifest_path.stem.replace("manifest-", "", 1)
                manifest = _read_json_file(manifest_path)
                if not isinstance(manifest, dict):
                    continue
                manifest_map[stamp] = manifest

                project_obj = manifest.get("project", {}) if isinstance(manifest.get("project"), dict) else {}
                if slug not in project_meta and project_obj:
                    project_meta[slug] = {
                        "project_name": str(project_obj.get("name", slug)),
                        "project_gid": str(project_obj.get("gid", "")),
                    }

        backups = []
        for zip_path in sorted(project_dir.glob("*.zip"), key=lambda p: p.name, reverse=True):
            zip_file = zip_path.name
            key = (slug, zip_file)
            rec = current_by_zip.get(key, {})

            run_stamp = str(rec.get("run_stamp") or _parse_run_stamp(zip_file))
            manifest = manifest_map.get(run_stamp, {}) if run_stamp else {}
            counts = rec.get("counts") or manifest.get("counts") or {}
            generated_at = str(rec.get("generated_at") or manifest.get("generated_at") or "")

            meta = project_meta.get(slug, {})
            project_name = str(rec.get("project_name") or meta.get("project_name") or slug)
            project_gid = str(rec.get("project_gid") or meta.get("project_gid") or "")

            backups.append(
                {
                    "project_gid": project_gid,
                    "project_name": project_name,
                    "project_slug": slug,
                    "zip_file": zip_file,
                    "zip_size": zip_path.stat().st_size,
                    "run_stamp": run_stamp,
                    "generated_at": generated_at,
                    "counts": counts if isinstance(counts, dict) else {},
                }
            )

        grouped[slug] = backups

    for rec in records:
        slug = str(rec.get("project_slug", ""))
        zip_file = str(rec.get("zip_file", ""))
        if not slug or not zip_file:
            continue
        grouped.setdefault(slug, [])
        if any(b.get("zip_file") == zip_file for b in grouped[slug]):
            continue
        grouped[slug].append(rec)

    projects = []
    for slug in sorted(grouped.keys()):
        backups = grouped[slug]
        backups = sorted(backups, key=lambda x: str(x.get("run_stamp", "")), reverse=True)
        if not backups:
            continue
        meta = project_meta.get(slug, {})
        project_name = str(meta.get("project_name") or backups[0].get("project_name") or slug)
        project_gid = str(meta.get("project_gid") or backups[0].get("project_gid") or "")

        for backup in backups:
            backup["project_slug"] = slug
            backup["project_name"] = str(backup.get("project_name") or project_name)
            backup["project_gid"] = str(backup.get("project_gid") or project_gid)

        projects.append(
            {
                "project_slug": slug,
                "project_name": project_name,
                "project_gid": project_gid,
                "backups": backups,
            }
        )

    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "projects": projects,
    }
    (DATA_ROOT / "backups.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


def discover_projects(token: str):
    workspaces = paginate(token, "/workspaces", {"opt_fields": "gid,name"})
    projects_by_gid = {}
    for ws in workspaces:
        ws_gid = str(ws["gid"])
        projects = paginate(
            token,
            f"/workspaces/{ws_gid}/projects",
            {"opt_fields": "gid,name,archived,workspace.gid,workspace.name", "archived": "false"},
        )
        for p in projects:
            projects_by_gid[str(p["gid"])] = p
    return list(projects_by_gid.values())


def main():
    if not ENV_PATH.exists():
        print(f"Missing env file: {ENV_PATH}", file=sys.stderr)
        return 1

    env = load_env(ENV_PATH)
    token = env.get("ASANA_TOKEN", "").strip()
    if not token:
        print("ASANA_TOKEN is required in .env", file=sys.stderr)
        return 1

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lockf = LOCK_PATH.open("w")
    try:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("Another backup is running; exiting.")
        return 0

    now = datetime.now(timezone.utc)
    run_stamp = now.strftime("%Y%m%d-%H%M%S")
    now_iso = now.isoformat()
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    FILES_ROOT.mkdir(parents=True, exist_ok=True)
    DATA_ROOT.mkdir(parents=True, exist_ok=True)

    records = []
    failures = []
    projects = discover_projects(token)
    for project in projects:
        try:
            rec = backup_project(token, project, run_stamp, now_iso)
            records.append(rec)
            print(f"OK {rec['project_slug']}: {rec['zip_file']}")
        except Exception as exc:
            gid = str(project.get("gid", "unknown"))
            name = project.get("name", gid)
            failures.append({"project_gid": gid, "project_name": name, "error": str(exc)})
            print(f"FAILED {name} ({gid}): {exc}", file=sys.stderr)

    build_global_index(records)
    status = {
        "generated_at": now_iso,
        "run_stamp": run_stamp,
        "success_count": len(records),
        "failure_count": len(failures),
        "failures": failures,
    }
    (DATA_ROOT / "last-run.json").write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

    run_tmp = TMP_ROOT / run_stamp
    if run_tmp.exists():
        shutil.rmtree(run_tmp, ignore_errors=True)

    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
