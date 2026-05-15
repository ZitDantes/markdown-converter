# Dépannage

## Fichier de log

En plus du journal à l’écran, l’app écrit un log persistant :

| Système | Emplacement |
|---------|-------------|
| macOS | `~/Library/Logs/MarkdownConverter/run.log` |
| Linux / autres | `~/.markdown-converter/logs/run.log` |

Le chemin exact apparaît au démarrage dans le journal. Rotation automatique (~1 Mo, 5 archives).

Pour forcer un autre dossier (tests) :

```bash
export CONVERTISSEUR_LOG_DIR="$HOME/Desktop/logs-markdown-converter"
MARKDOWN_CONVERTER_UI=qt python3 main.py
```

## Problèmes fréquents

### L’app ne s’ouvre pas (macOS)

Gatekeeper : clic droit → **Ouvrir**, ou autoriser dans **Confidentialité et sécurité**.

### Interface Tk au lieu de Qt

Installez PySide6 et lancez avec la variable d’environnement :

```bash
pip install -r requirements-qt.txt
MARKDOWN_CONVERTER_UI=qt python3 main.py
```

### `ModuleNotFoundError: _tkinter`

Avec Python Homebrew, installez `python-tk@3.12` (même version que Python), puis recréez le venv. Voir [README.md](../../README.md).

### Conversion vide ou erreur sur un PDF

Souvent un PDF image sans texte. Essayez un export « texte » ou un autre format source.

### `MagikaError: model dir not found` (application packagée `.app`)

Version corrigée à partir de **v0.2.0** (rebuild PyInstaller avec les modèles `magika` inclus). Si vous voyez encore ce message, retéléchargez la dernière archive **GitHub Release** ou reconstruisez avec `./scripts/build_mac_app.sh`.

### Secours non disponible

En mode **Standard**, si la conversion principale échoue et qu’aucun secours n’est installé, le fichier reste en erreur. Installez [Pandoc](https://pandoc.org/) (`brew install pandoc`) ou passez en revue le format source.

### Dossier de sortie refusé

Vérifiez que le dossier existe et est **accessible en écriture**.

## Support

Pour un signalement, joignez `run.log` (et `run.log.1` si l’erreur est ancienne) via une issue GitHub du dépôt.

[← Formats et qualité](05-formats-et-qualite.md) · [Confidentialité →](07-confidentialite.md)
