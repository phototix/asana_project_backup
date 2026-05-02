# asana_project_backup

Back up all Asana projects accessible by your token into one ZIP per project, including tasks, descriptions, comments, and attachments.

## What it exports

- Tasks (JSON metadata)
- Description content (`notes`, `html_notes`)
- Comments (`stories` with comment subtype)
- Task attachments and inline assets
- Project sections metadata for board ordering
- Manifests and global backup index JSON

## Setup

1. Copy `.env.example` to `.env` and fill your values.
2. Run:

```bash
python3 backup_asana.py
```

## Scheduling example (every Monday 3:00 AM)

```cron
0 3 * * 1 root /usr/bin/python3 /opt/asana_project_backup/backup_asana.py >> /var/log/asana-backup.log 2>&1
```
