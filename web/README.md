# Interface web — Markdown Converter (PLO-46)

Front **Vite + React + TypeScript**, embarqué dans l’app via **Qt WebEngine** (`MARKDOWN_CONVERTER_UI=web`).

## Prérequis

- **Node.js** 20+ et **npm** (développement uniquement ; l’utilisateur final reçoit `web/dist` via le bundle ou un build release).
- **PySide6 + WebEngine** : `pip install -r requirements-qt.txt`

## Commandes

```bash
cd web
npm ci
npm run build    # produit dist/ (chargé en file: par ui_web_shell)
npm run dev      # serveur Vite (hors WebEngine — debug UI seule)
```

Depuis la racine du repo :

```bash
./scripts/build_web.sh
MARKDOWN_CONVERTER_UI=web python3 main.py
```

## Structure

| Chemin | Rôle |
|--------|------|
| `src/` | Application React (shell minimal) |
| `shared/bridge-contract.ts` | Types du pont (miroir `bridge_contract/`) |
| `dist/` | Build statique (généré, non versionné) |

Contrat : [ADR 0001](../docs/adr/0001-contrat-pont-webchannel-js-python.md).

## Si WebEngine est indisponible (PLO-54)

Au lancement avec `MARKDOWN_CONVERTER_UI=web`, l’app vérifie PySide6, **Qt WebEngineWidgets** et la présence de `web/dist/index.html`.

| Variable | Comportement |
|----------|----------------|
| *(défaut)* | Repli vers **Tkinter** (`ui.py`) |
| `MARKDOWN_CONVERTER_WEB_FALLBACK=none` | Message d’erreur en français, puis arrêt (code 1) |

`MARKDOWN_CONVERTER_WEB_FALLBACK=qt` est obsolète (PLO-56) et équivaut à Tkinter.

Dépendances Linux : voir [spike/webengine/README.md](../spike/webengine/README.md).
