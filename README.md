# Asana Backup + Web Viewer

This project exports Asana projects into timestamped ZIP archives and serves a built-in PHP viewer so backups can be explored in a browser.

## Overview

- `backup_asana.py` discovers non-archived projects, exports project/task/comment data, downloads assets, and writes backup artifacts.
- `index.php` reads generated indexes and renders a browsable UI with project history, board view, task detail pages, and ZIP download routes.
- Backups are append-only: older ZIP files and manifests are kept, while `data/backups.json` is rebuilt from what exists on disk.

## What gets backed up

For each accessible non-archived Asana project:

- Project sections (`sections.json`)
- Full task payloads (`tasks/<task_gid>.json`)
- Task comments/stories (`comments/<task_gid>.json`)
- Attachments plus download metadata (`attachments/<task_gid>/...`, `_meta.json`)
- Inline assets referenced in HTML notes/comments plus metadata (`inline-assets/<task_gid>/...`, `_meta.json`)
- Run manifest (`manifest.json`)

Each run produces one ZIP per project:

- `files/<project-slug>/asana-backup-<project-slug>-<YYYYMMDD-HHMMSS>.zip`

And updates:

- `data/<project-slug>/manifest-<YYYYMMDD-HHMMSS>.json`
- `data/backups.json`
- `data/last-run.json`

## Requirements

- Python 3.8+
- PHP 8+ with `ZipArchive`
- Asana Personal Access Token (`ASANA_TOKEN`)
- Write permissions for:
  - `/var/www/codigo.brandon.my/files`
  - `/var/www/codigo.brandon.my/data`
  - `/var/www/codigo.brandon.my/tmp`
  - `/var/lock`

## Configuration

There are two env file locations used by this project.

### 1) Backup script env (`backup_asana.py`)

Default path: `/opt/asana-backup/.env`

Required key:

```env
ASANA_TOKEN="your-asana-token-here"
```

If needed, change the path by editing `ENV_PATH` in `backup_asana.py`.

### 2) Web viewer auth env (`index.php`)

Path: `.env` at project root (`/var/www/codigo.brandon.my/.env`)

Optional keys:

```env
APP_USERNAME="your-login-username"
APP_PASSWORD="your-login-password"
```

If both are set, viewer login is enabled. If either is missing, viewer routes are open.

`.env.example` includes all three keys for convenience.

## Usage

Run a backup manually:

```bash
python3 backup_asana.py
```

Runtime behavior:

- Uses lock file `/var/lock/asana-backup.lock` with non-blocking lock to prevent overlapping runs.
- Prints one `OK ...` line per successful project and `FAILED ...` lines for errors.
- Exit codes:
  - `0`: all projects succeeded
  - `2`: one or more projects failed
  - `1`: configuration/startup error (for example, missing env/token)

## Web routes

- `/` - project index and latest run status
- `/project/<project-slug>` - backup history for a project
- `/view/<project-slug>/<zip-file>` - board view for one backup
- `/view/<project-slug>/<zip-file>/task/<task_gid>` - task details
- `/download/<project-slug>/<zip-file>` - download ZIP
- `/login`, `/logout` - viewer authentication endpoints

## Task Manager reporting

`/reporting` now builds its XLSX from the vendor Task Manager (`taskmanager.codigo.co`) instead of the Asana API.

### Session and configuration

State lives outside the web root in `/opt/taskmanager-session`:

| File | Purpose | Permissions |
|---|---|---|
| `.env` | `TM_BASE_URL`, `TM_EMAIL`, `TM_PASSWORD`, `TM_PROJECT_ID`, `TM_PROJECT_NAME` | `0640 root:www-data` |
| `session.json` | stored cookies, `expires_at`, `user_email` | `0660 root:www-data` |
| `people.json` | comment-author name to email map | `0640 root:www-data` |
| `status.json` | last session check result | `0660 root:www-data` |

The normal export reuses `session.json`, so no OTP is requested. A new OTP is only needed when the session expires (currently seven days).

### Reconnecting

- Web: open `/reporting/connect` (behind the normal viewer login). The server reads the stored credentials and sends the email code; enter the code on that page. The page shows the code deadline (about ten minutes). Use the newest email. "Send a new code" starts a fresh sign-in challenge and resets the window.
- CLI: run `php taskmanager_login.php` on the server and enter the emailed code when prompted. Use this if the web auth route is unavailable.
- The vendor's 2FA cookie is short-lived. If the email arrives late, restart the challenge from the web page rather than entering an old code.

Credentials are never sent to the browser. Rotate the Task Manager password in `/opt/taskmanager-session/.env` if it changes.

### Keepalive

`/etc/cron.d/taskmanager-keepalive` runs `taskmanager_keepalive.php` daily at 07:30 server time. It calls `/api/auth/get-session`. When better-auth asks for a refresh, it POSTs to `get-session` and saves the new cookie, which can extend the seven-day window. Expiry is logged to `status.json` and `/var/log/taskmanager-keepalive.log`.

### Notes

- The Task Manager has no documented public API; this uses the same internal endpoints as the web app. If the vendor changes them, the reporting page will show the error and the reconnect page can be used to re-authenticate.
- `/reporting` includes top-level tickets only; nested subtasks are intentionally excluded.
- The XLSX columns and generated-file history are unchanged.

## Scheduling example

Run every Monday at 03:00:

```cron
0 3 * * 1 /usr/bin/python3 /var/www/codigo.brandon.my/backup_asana.py >> /var/log/asana-backup.log 2>&1
```

## Operational notes

- Project discovery is workspace-based and excludes archived projects.
- Some attachments/inline URLs may be inaccessible; metadata still records download success/failure per item.
- Timestamps are generated in UTC for artifact naming; the viewer displays dates in SGT.

## User manual and automated checks

- Published page: `/reports/KMSPKS-Codigo-User-Manual.html` with PDF and editable DOCX downloads.
- Manual content: `manual-tools/manual_content.py`; route inventories: `manual-tools/*-routes.txt`.
- Screenshots are stored outside the web root under `/home/webbycms/reports/kmspks-codigo/manual/shots`.
- Run the read-only checks with a Python environment that has `requests`, `pillow`, `pypdf`, `pymupdf` and `python-docx`:

```bash
PRE_USER=... PRE_PASS=... /tmp/opencode/manual-venv/bin/python manual_checks.py
```

- Results: `reports-data/manual-checks.json` and `reports-data/KMSPKS-Codigo-User-Manual-checks.html`.
- Credentials are read from the environment and are never written to the report.
