#!/usr/bin/env bash
# Construit l’application Linux (dossier onedir PyInstaller) avec UI web + WebEngine.
#
# Cible : Ubuntu 22.04+ (ou équivalent Debian) avec les libs Qt WebEngine du système.
# Voir spike/webengine/README.md (section dépendances Linux).
#
# Usage :
#   ./scripts/build_linux_app.sh
#   ./scripts/build_linux_app.sh v0.3.0   # archive .tar.gz nommée pour release
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "Erreur : ce script est prévu pour Linux (build natif ou CI Ubuntu)." >&2
  exit 1
fi

if [[ ! -d .venv ]]; then
  echo "Erreur : le dossier .venv est absent." >&2
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

DIR_NAME="Markdown Converter"
if [[ ! -d "dist/${DIR_NAME}" ]]; then
  echo "Erreur : dist/${DIR_NAME} introuvable après PyInstaller." >&2
  exit 1
fi

DIR_SIZE="$(du -sh "dist/${DIR_NAME}" | awk '{print $1}')"
echo "Taille du dossier (décompressé) : ${DIR_SIZE}"

VERSION="${1:-$(date +%Y%m%d-%H%M)}"
ARCHIVE="MarkdownConverter-linux-${VERSION}.tar.gz"
tar -czf "$ROOT/$ARCHIVE" -C dist "${DIR_NAME}"

ARCH_SIZE="$(du -sh "$ROOT/$ARCHIVE" | awk '{print $1}')"
echo "OK — archive prête :"
echo "  $ROOT/$ARCHIVE"
echo "  Taille : ${ARCH_SIZE} (GitHub Release : max 2 Go par asset ; ne pas committer dans Git)"
echo ""
echo "Lancement :"
echo "  tar -xzf ${ARCHIVE}"
echo "  ./\"${DIR_NAME}\"/\"${DIR_NAME}\""
