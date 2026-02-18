#!/usr/bin/env bash
set -euo pipefail

APP_NAME="driving-exam-statistic"
VERSION="${1:-0.1.0}"
MAINTAINER="${MAINTAINER:-izan}"

BIN="dist/$APP_NAME"
if [[ ! -f "$BIN" ]]; then
  echo "ERROR: Falta $BIN. Ejecuta antes ./packaging/build_linux_exe.sh." >&2
  exit 1
fi

ARCH="$(dpkg --print-architecture 2>/dev/null || echo amd64)"
STAGE="build/debroot"
OUT_DIR="dist-deb"
OUT_DEB="$OUT_DIR/${APP_NAME}_${VERSION}_${ARCH}.deb"

rm -rf "$STAGE" "$OUT_DIR"
install -d "$STAGE/DEBIAN" "$STAGE/opt/$APP_NAME" "$STAGE/usr/bin" "$STAGE/usr/share/applications" "$STAGE/usr/share/icons/hicolor/256x256/apps"

cat >"$STAGE/DEBIAN/control" <<CTRL
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: $MAINTAINER
Description: Driving Exam Statistic (PyQt6) - aplicacion de analisis de examenes DGT
CTRL

install -m 0755 "$BIN" "$STAGE/opt/$APP_NAME/$APP_NAME"
cat >"$STAGE/usr/bin/$APP_NAME" <<SH
#!/usr/bin/env sh
exec /opt/$APP_NAME/$APP_NAME "\$@"
SH
chmod 0755 "$STAGE/usr/bin/$APP_NAME"

install -m 0644 "packaging/deb/driving-exam-statistic.desktop" "$STAGE/usr/share/applications/driving-exam-statistic.desktop"
install -m 0644 "driving_exams/ui/icon/icon.png" "$STAGE/usr/share/icons/hicolor/256x256/apps/driving-exam-statistic.png"

install -d "$OUT_DIR"
dpkg-deb --build "$STAGE" "$OUT_DEB" >/dev/null

echo "OK: generado $OUT_DEB"
