#!/usr/bin/env bash
# Build le front web (Vite) dans web/dist/
set -euo pipefail
cd "$(dirname "$0")/../web"
npm ci
npm run build
echo "Build terminé : web/dist/"
