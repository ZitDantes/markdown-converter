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
