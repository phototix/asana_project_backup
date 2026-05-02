#!/usr/bin/env bash
set -euo pipefail

msg="${*:-update}"

git add -A

if git diff --cached --quiet; then
  echo "No staged changes to commit."
else
  git commit -m "$msg"
fi

git push
