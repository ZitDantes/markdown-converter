# Installation

## Option 1 — Application macOS (recommandée)

1. Ouvrez les [Releases GitHub](https://github.com/ZitDantes/markdown-converter/releases/latest).
2. Téléchargez `MarkdownConverter-mac-v0.2.0.zip` (ou la dernière version indiquée).
3. Décompressez et placez **Markdown Converter.app** dans **Applications**.
4. Au **premier lancement**, macOS peut bloquer l’app (développeur non identifié) :
   - Clic droit sur l’app → **Ouvrir**, puis confirmer ;
   - ou **Réglages système → Confidentialité et sécurité** → autoriser l’ouverture.

L’application n’est pas notarisée Apple ; c’est normal pour une distribution open source en bêta.

### Pandoc (optionnel)

[Pandoc](https://pandoc.org/) peut aider à récupérer certains fichiers lorsque la conversion principale échoue. Sans Pandoc, l’app fonctionne ; un indicateur dans l’interface signale si le **secours** est disponible.

```bash
brew install pandoc
```

## Option 2 — Depuis les sources (développeurs)

Prérequis : **Python 3.10+**, **PySide6** pour l’interface recommandée.

```bash
git clone https://github.com/ZitDantes/markdown-converter.git
cd markdown-converter
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-qt.txt
MARKDOWN_CONVERTER_UI=qt python3 main.py
```

Sur macOS avec Homebrew, installez aussi **Tk** si besoin (`python-tk@3.12`) — utilisé en secours si Qt n’est pas disponible.

Variables utiles :

| Variable | Effet |
|----------|--------|
| `MARKDOWN_CONVERTER_UI=qt` | Lance l’interface **Qt** (recommandée en v0.2). |
| `MARKDOWN_CONVERTER_UI=tk` | Interface Tkinter classique (défaut si variable absente). |
| `CONVERTISSEUR_LOG_DIR` | Dossier personnalisé pour les fichiers de log. |

Détails techniques : [README.md](../../README.md) à la racine du dépôt.

[← Bienvenue](01-bienvenue.md) · [Premiers pas →](03-premiers-pas.md)
