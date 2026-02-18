#!/usr/bin/env bash
set -euo pipefail

PKGNAME="driving-exam-statistic"
VERSION="$(python - <<'PY'
import tomllib
from pathlib import Path
print(tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))['project']['version'])
PY
)"

OUT="packaging/arch/${PKGNAME}-${VERSION}.tar.gz"
mkdir -p packaging/arch

tar -czf "$OUT" \
  --transform "s,^\./,${PKGNAME}-${VERSION}/," \
  --exclude "./.git" \
  --exclude "./__pycache__" \
  --exclude "./.venv" \
  --exclude "./venv" \
  --exclude "./build" \
  --exclude "./dist" \
  --exclude "./dist-deb" \
  --exclude "./packaging/arch/pkg" \
  --exclude "./packaging/arch/src" \
  --exclude "./packaging/arch/*.tar.gz" \
  --exclude "./packaging/arch/*.pkg.tar.*" \
  .

echo "OK: created $OUT"
