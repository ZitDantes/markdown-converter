#!/usr/bin/env bash
# Construit l’application macOS (.app) avec PyInstaller et produit une archive ZIP
# pour distribution (inclut un LISEZMOI).
#
# Prérequis : .venv, Node.js 20+ (build front), PySide6 + WebEngine (requirements-qt.txt).
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

echo "== Build front (web/dist) =="
./scripts/build_web.sh

rm -rf build dist
echo "== PyInstaller (UI web + WebEngine) =="
python3 -m PyInstaller --noconfirm MarkdownConverter.spec

APP_NAME="Markdown Converter.app"
if [[ ! -d "dist/${APP_NAME}" ]]; then
  echo "Erreur : dist/${APP_NAME} introuvable après PyInstaller." >&2
  exit 1
fi

# PyInstaller laisse aussi un dossier onedir homonyme (~ même taille) : éviter la confusion.
if [[ -d "dist/Markdown Converter" && ! -L "dist/Markdown Converter" ]]; then
  rm -rf "dist/Markdown Converter"
fi

APP_SIZE="$(du -sh "dist/${APP_NAME}" | awk '{print $1}')"
echo "Taille du .app (décompressé) : ${APP_SIZE}"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

cp -R "dist/${APP_NAME}" "$STAGE/"
cp docs/LISEZMOI_COLLEGUES.txt "$STAGE/LISEZMOI.txt"

VERSION="${1:-$(date +%Y%m%d-%H%M)}"
ZIP_NAME="MarkdownConverter-mac-${VERSION}.zip"
( cd "$STAGE" && zip -rq "$ROOT/$ZIP_NAME" . )

ZIP_SIZE="$(du -sh "$ROOT/$ZIP_NAME" | awk '{print $1}')"
echo "OK — archive prête pour distribution :"
echo "  $ROOT/$ZIP_NAME"
echo "  Taille ZIP : ${ZIP_SIZE} (GitHub Release : max 2 Go par asset ; ne pas committer ce ZIP dans Git, max 100 Mo/fichier)"
# Avertissement grossier si la taille affichée par du contient « G » (ex. 1,1G) — rester sous 2 Go.
if [[ "${ZIP_SIZE}" == *G* ]]; then
  echo "Attention : archive volumineuse — vérifier qu’elle reste sous 2 Go avant upload GitHub Release." >&2
fi
