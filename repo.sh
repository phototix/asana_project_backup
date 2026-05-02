#!/usr/bin/env bash
set -euo pipefail

msg="${*:-update}"

git add .
git commit -m "$msg"
git push
