#!/usr/bin/env bash
set -euo pipefail

APP_NAME="driving-exam-statistic"
ENTRYPOINT="driving_exams/main.py"

python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt pyinstaller >/dev/null

pyinstaller \
  --noconfirm \
  --clean \
  --name "$APP_NAME" \
  --onefile \
  --windowed \
  --collect-all matplotlib \
  --add-data "driving_exams/ui/icon/icon.png:driving_exams/ui/icon" \
  "$ENTRYPOINT"

echo "OK: generado dist/$APP_NAME"
