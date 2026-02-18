#!/usr/bin/env bash
set -euo pipefail

# Uso:
#   ./packaging/deb/sign_and_verify_deb.sh dist-deb/driving-exam-statistic_0.1.0_amd64.deb
#
# Genera:
#   - <deb>.sig
#   - <deb>.tampered

if [[ $# -ne 1 ]]; then
  echo "Uso: $0 <paquete.deb>" >&2
  exit 1
fi

DEB="$1"
if [[ ! -f "$DEB" ]]; then
  echo "ERROR: no existe el paquete: $DEB" >&2
  exit 1
fi

if ! gpg --list-secret-keys >/dev/null 2>&1; then
  echo "ERROR: no hay clave secreta GPG disponible." >&2
  exit 1
fi

SIG="${DEB}.sig"
TAMPERED="${DEB}.tampered"

echo "[1/4] Firmando paquete DEB..."
gpg --output "$SIG" --detach-sign "$DEB"

echo "[2/4] Verificando firma del DEB original..."
gpg --verify "$SIG" "$DEB"

echo "[3/4] Creando copia manipulada..."
cp "$DEB" "$TAMPERED"
printf '\x00' | dd of="$TAMPERED" bs=1 seek=128 count=1 conv=notrunc status=none

echo "[4/4] Verificando DEB manipulado (debe FALLAR)..."
if gpg --verify "$SIG" "$TAMPERED"; then
  echo "ERROR: la verificación no falló para el fichero manipulado." >&2
  exit 2
else
  echo "OK: la verificación del fichero manipulado ha fallado (esperado)."
fi

echo "Listo."
