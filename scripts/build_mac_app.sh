#!/usr/bin/env bash
# Construit l’application macOS (.app) avec PyInstaller et produit une archive ZIP datée
# pour distribution aux collègues (inclut un LISEZMOI).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Erreur : le dossier .venv est absent. Créez-le puis installez les dépendances (voir README)." >&2
  exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate

python3 -m pip install -q pyinstaller
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

VERSION="$(date +%Y%m%d-%H%M)"
ZIP_NAME="MarkdownConverter-mac-${VERSION}.zip"
( cd "$STAGE" && zip -rq "$ROOT/$ZIP_NAME" . )

echo "OK — archive prête pour distribution :"
echo "  $ROOT/$ZIP_NAME"
