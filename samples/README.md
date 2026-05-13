# `samples/` — Documents de test locaux

Ce dossier sert à **stocker des documents de test** (`.docx`, `.pdf`, `.pptx`, `.xlsx`, `.html`, `.htm`, `.txt`) pour valider les conversions à la main, sans avoir à bricoler avec des fichiers temporaires dans `/tmp`.

## Règles

- **Le contenu de ce dossier est ignoré par git** (cf. [`.gitignore`](../.gitignore)), à l'exception de ce `README.md` et de `.gitkeep`. Chaque dev pose ici ses propres fichiers de test ; rien n'est partagé via le repo.
- Pourquoi : éviter d'embarquer des documents potentiellement personnels ou soumis à des droits d'auteur dans l'historique git.

## Conventions

| Sous-dossier | Usage |
|---|---|
| `samples/` (racine) | Documents d'entrée à convertir. |
| `samples/output/` | Dossier de sortie suggéré pour les `.md` produits et le `rapport_conversion.md`. Ignoré aussi. |

Les formats reconnus par l'app sont définis dans [`utils.py`](../utils.py) (`SUPPORTED_EXTENSIONS`).

## Lancer une conversion manuelle

### Via l'interface graphique

```bash
source .venv/bin/activate
python3 main.py
```

Ensuite : ajouter les fichiers depuis `samples/`, choisir `samples/output/` comme dossier de sortie, cliquer *Convertir*.

### En une ligne depuis Python

Pour un test rapide sans UI (utile pour le smoke test après un refactor) :

```bash
source .venv/bin/activate
python3 -c "
from pathlib import Path
from converter import convert_files
from report import write_report

summary = convert_files(
    explicit_files=list(Path('samples').glob('*.docx')),
    directory_roots=[],
    output_dir=Path('samples/output'),
    on_log=print,
)
print('Rapport :', write_report(summary))
"
```

Adapter le `glob('*.docx')` au format que tu veux tester (`*.pdf`, `*.pptx`, etc.) ou utiliser `directory_roots=[Path('samples')]` pour tout convertir d'un coup.

## Bon à savoir

- L'app affiche un **avertissement** dans le journal pour les PDF et PPTX : conversion automatique = relecture humaine recommandée avant intégration sérieuse.
- Si **Pandoc** est installé (`brew install pandoc`), il est utilisé comme secours quand MarkItDown échoue ou renvoie un Markdown vide. Sinon, MarkItDown seul.
