# Asana Project Backup

This project creates restorable, browsable backups for every non-archived Asana project your API token can access.
Each run exports project data to ZIP files and updates a small PHP viewer so you can inspect backups in a browser.

## What it does

- Discovers accessible workspaces and projects through the Asana API.
- Exports full task JSON, including notes, HTML notes, metadata, memberships, followers, tags, and selected custom fields.
- Exports task comments (`stories`) and stores them per task.
- Downloads task attachments and inline assets referenced in task/comment HTML when possible.
- Generates per-project manifests plus a global index used by the web UI.
- Builds one ZIP per project per run, with timestamped file names.

## Tech stack

- `backup_asana.py`: Python 3 backup runner (no third-party packages required).
- `index.php`: PHP viewer for browsing backups, opening task details, and downloading ZIPs.

## Requirements

- Python 3.8+
- PHP 8+ with `ZipArchive` enabled (for the viewer)
- An Asana personal access token (`ASANA_TOKEN`)
- Write access to these directories:
  - `/var/www/codigo.brandon.my/files`
  - `/var/www/codigo.brandon.my/data`
  - `/var/www/codigo.brandon.my/tmp`
  - `/var/lock` (for lock file)

## Configuration

The script reads environment variables from:

- `/opt/asana-backup/.env`

Use this format:

```env
ASANA_TOKEN="your-asana-token-here"
```

You can copy from `.env.example`, but place the final file at `/opt/asana-backup/.env` (or update `ENV_PATH` in `backup_asana.py`).

## Run a backup

```bash
python3 backup_asana.py
```

Behavior:

- Uses a non-blocking lock at `/var/lock/asana-backup.lock` to prevent overlapping runs.
- Prints `OK ...` per successful project and `FAILED ...` per failed project.
- Returns exit code `0` if all projects succeed, `2` if any project fails.

## Output layout

- `files/<project-slug>/asana-backup-<project-slug>-<YYYYMMDD-HHMMSS>.zip`
- `data/<project-slug>/manifest-<YYYYMMDD-HHMMSS>.json`
- `data/backups.json` (global index consumed by the viewer)
- `data/last-run.json` (latest run status + failures)

Each ZIP contains:

- `tasks/<task_gid>.json`
- `comments/<task_gid>.json`
- `attachments/<task_gid>/...` and `attachments/<task_gid>/_meta.json`
- `inline-assets/<task_gid>/...` and `inline-assets/<task_gid>/_meta.json`
- `sections.json`
- `manifest.json`

## Web viewer

`index.php` provides:

- Project list and backup history
- Board-style task view grouped by section
- Task detail view with description, comments, and attachment gallery
- Secure download/preview routes for files stored inside ZIP backups

Common routes:

- `/` - project overview
- `/project/<project-slug>` - backups for one project
- `/view/<project-slug>/<zip-file>` - board view for a backup
- `/download/<project-slug>/<zip-file>` - download backup ZIP

## Scheduling (cron)

Example: every Monday at 3:00 AM

```cron
0 3 * * 1 /usr/bin/python3 /var/www/codigo.brandon.my/backup_asana.py >> /var/log/asana-backup.log 2>&1
```

## Notes

- Only non-archived projects are discovered.
- Attachment/inline asset downloads may fail for some URLs; metadata still records whether each item was downloaded.
- Existing backup ZIPs and manifests are preserved; global index is rebuilt from available files.
