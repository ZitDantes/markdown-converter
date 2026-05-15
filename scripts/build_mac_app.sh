#!/usr/bin/env bash
# Construit l’application macOS (.app) avec PyInstaller et produit une archive ZIP
# pour distribution (inclut un LISEZMOI).
#
# Usage :
#   ./scripts/build_mac_app.sh              # archive horodatée (build interne, partage rapide)
#   ./scripts/build_mac_app.sh v0.1.0       # archive nommée pour une GitHub Release
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Erreur : le dossier .venv est absent. Créez-le puis installez les dépendances (voir README)." >&2
  exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate

python3 -m pip install -q -r requirements.txt -r requirements-qt.txt pyinstaller
rm -rf build dist
python3 -m PyInstaller --noconfirm MarkdownConverter.spec

APP_NAME="Markdown Converter.app"
if [[ ! -d "dist/${APP_NAME}" ]]; then
  echo "Erreur : dist/${APP_NAME} introuvable après PyInstaller." >&2
  exit 1
fi

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

cp -R "dist/${APP_NAME}" "$STAGE/"
cp docs/LISEZMOI_COLLEGUES.txt "$STAGE/LISEZMOI.txt"

VERSION="${1:-$(date +%Y%m%d-%H%M)}"
ZIP_NAME="MarkdownConverter-mac-${VERSION}.zip"
( cd "$STAGE" && zip -rq "$ROOT/$ZIP_NAME" . )

echo "OK — archive prête pour distribution :"
echo "  $ROOT/$ZIP_NAME"
