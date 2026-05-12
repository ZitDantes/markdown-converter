# Convertisseur Markdown IA (MVP)

> **Licence en cours de définition** — Ce dépôt est public sur GitHub, mais **aucune licence open source n’a encore été formalisée** (pas de fichier `LICENSE` à la racine). Tant que ce n’est pas le cas, le code reste par défaut **« tous droits réservés »** (*All rights reserved*) du point de vue du droit d’auteur : toute réutilisation ou redistribution nécessite une autorisation explicite des mainteneurs.

Application **macOS** (Python 3) pour convertir en lot des documents bureautiques en fichiers **Markdown** (UTF-8), en vue d’alimenter une base de connaissances ou un système RAG. **Tout est local** : aucune donnée n’est envoyée vers un service cloud.

## Table des matières

- [Pour les utilisateurs](#pour-les-utilisateurs)
- [Qualité, limites et bonnes pratiques](#qualite-limites-et-bonnes-pratiques)
- [Pour les développeurs et la distribution (macOS)](#pour-les-developpeurs-et-la-distribution-macos)
- [Licence](#licence)

---

## Pour les utilisateurs

### Prérequis

- **macOS** (testé en conception pour macOS ; Python/Tkinter peut fonctionner ailleurs).
- **Python 3.10 ou supérieur** (requis par [MarkItDown](https://github.com/microsoft/markitdown)). Avec **Python 3.9**, `pip` n’installe qu’une très ancienne alpha du paquet `markitdown` **sans** la classe `MarkItDown` — l’application affiche alors un message et refuse de démarrer tant que vous n’utilisez pas Python 3.10+.
- **Tkinter** : nécessaire pour l’interface. Avec **Homebrew**, le paquet `python@3.12` **ne contient pas** Tk par défaut ; installez aussi **`python-tk@3.12`** (même numéro de version que votre Python). Alternative : l’installeur officiel depuis [python.org](https://www.python.org/downloads/macos/) inclut en général Tkinter.

#### Dépannage : `ModuleNotFoundError: No module named '_tkinter'`

Typique après `brew install python@3.12` **sans** le paquet Tk. Installez-le puis recréez le venv :

```bash
brew install python-tk@3.12
# adaptez 3.12 si vous utilisez 3.11 ou 3.10 : python-tk@3.11, etc.

cd markdown-converter   # racine du dépôt cloné (dossier contenant main.py)
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

#### Dépannage : `ImportError: cannot import name 'MarkItDown' from 'markitdown'`

Vous êtes très probablement en **Python 3.9** (vérifiez avec `python3 --version`). Recréez un environnement avec Python 3.10+ (ex. 3.12) :

```bash
cd markdown-converter   # racine du dépôt cloné (dossier contenant main.py)
rm -rf .venv
python3.12 -m venv .venv   # ou python3.11, python3.10 selon ce qui est installé
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 main.py
```

- Outils de développement Apple (**Xcode Command Line Tools**) si `pip` doit compiler certaines dépendances rares ; en général les *wheels* précompilées suffisent.

### Installation

Clonez le dépôt (ou téléchargez une archive ZIP depuis GitHub), puis ouvrez un terminal dans ce dossier :

```bash
git clone https://github.com/ZitDantes/markdown-converter.git
cd markdown-converter
```

Ensuite :

**Si vous utilisez Homebrew (recommandé sur Apple Silicon)** — Python **et** Tk pour la même version :

```bash
brew install python@3.12 python-tk@3.12
```

Puis création du venv et dépendances :

```bash
cd markdown-converter   # racine du dépôt cloné (dossier contenant main.py)
python3.12 -m venv .venv
# ou : python3.11 -m venv .venv  /  python3.10 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

#### Pandoc (optionnel, recommandé en secours)

Si [Pandoc](https://pandoc.org/) est installé et visible dans le `PATH`, il sera utilisé **uniquement** lorsque MarkItDown échoue ou produit un contenu vide. Sans Pandoc, l’application fonctionne **normalement** avec MarkItDown seul ; le journal indique alors une simple note à ce sujet (ce n’est pas une erreur).

Installation possible via Homebrew :

```bash
brew install pandoc
```

### Lancement

Avec l’environnement virtuel activé :

```bash
source .venv/bin/activate
python3 main.py
```

### Utilisation (interface)

1. **Ajouter des fichiers** : formats `.docx`, `.pptx`, `.pdf`, `.xlsx`, `.html`, `.htm`, `.txt`.
2. **Ajouter un dossier** : parcours **récursif** ; seuls les fichiers aux formats supportés sont pris en compte.
3. **Choisir le dossier de sortie** : les `.md` y sont créés (un par document source), en évitant les collisions de noms (`_2`, `_3`, …).
4. **Convertir** : suivez la barre de progression et le journal.
5. Ouvrez **`rapport_conversion.md`** dans le dossier de sortie pour le bilan détaillé.

Les textes de l’interface et du rapport sont en **français**.

### Sécurité et confidentialité

- Aucune intégration d’API cloud, pas de télémétrie.
- Les conversions utilisent **uniquement** des fichiers locaux (`convert_local` côté MarkItDown).
- Ne passez pas d’URL à l’application : le MVP est conçu pour des chemins disque.

---

## Qualité, limites et bonnes pratiques

### Limites connues

- La conversion **n’est pas parfaite** : objectif = texte exploitable pour un LLM/RAG, pas une reproduction fidèle à 100 %.
- **PDF** et **PPTX** : ordre des blocs, tableaux, notes et images peuvent être approximatifs ; **relecture humaine indispensable** (rappel aussi dans le rapport).
- **XLSX** : perte probable des formules, graphiques et styles ; structure tabulaire simplifiée en texte/Markdown.
- **HTML** : scripts et mise en page complexes ne sont pas reproduits à l’identique.
- **Pandoc** : ne couvre pas tous les formats (ex. secours **non garanti** pour Excel) ; le moteur principal reste **MarkItDown**.
- **Dossiers** : seuls les formats listés sont collectés ; les autres fichiers présents dans l’arborescence sont **ignorés sans être tous nommés** dans le rapport (seuls les fichiers ajoutés directement avec une mauvaise extension apparaissent dans « formats non supportés »).

### Formats recommandés pour la meilleure qualité

| Priorité | Format | Commentaire |
|----------|--------|-------------|
| Élevée | `.docx`, `.html`, `.txt` | Structure de titres et texte généralement bien conservés. |
| Moyenne | `.xlsx` | Préférer des feuilles simples, peu de fusion de cellules. |
| À relire | `.pdf`, `.pptx` | Utiliser pour dégrossir ; prévoir relecture/correction. |

### Conseils pour préparer les documents avant conversion

- Utiliser les **styles de titres** (Titre 1, Titre 2…) dans Word plutôt que du texte mis en forme manuellement.
- Pour les **PDF**, privilégier les PDF « texte » ; les scans sans OCR donnent souvent un résultat vide ou médiocre.
- Dans **Excel**, une seule feuille claire par sujet, en-têtes de colonnes explicites, éviter les tableaux croisés dynamiques comme unique source.
- Dans **PowerPoint**, texte dans les zones de titre et de contenu standard ; les mises en page exotiques se dégradent davantage.
- Éviter les mots de passe / fichiers chiffrés : la conversion peut échouer.

---

## Pour les développeurs et la distribution (macOS)

Objectif : produire une **application autonome** (`.app`) pour des utilisateurs qui **n’installent pas** Python ni de venv.

### Structure du projet

| Fichier | Rôle |
|---------|------|
| `main.py` | Lancement de l’application. |
| `ui.py` | Interface Tkinter (français). |
| `converter.py` | Conversion (MarkItDown, secours Pandoc). |
| `report.py` | Génération de `rapport_conversion.md`. |
| `utils.py` | Extensions, chemins, nettoyage, détection Pandoc. |
| `ConvertisseurMarkdownIA.spec` | Définition PyInstaller (build `.app` reproductible). |
| `scripts/build_mac_app.sh` | Script : PyInstaller + ZIP daté + LISEZMOI pour collègues. |
| `docs/LISEZMOI_COLLEGUES.txt` | Texte d’accompagnement pour l’archive distribuée. |

L’API de `converter.py` (callbacks `on_log` / `on_progress`) est pensée pour pouvoir brancher une autre interface (par ex. PySide6) plus tard sans réécrire la logique métier.

### Lint et formatage (ruff)

Le projet utilise [ruff](https://docs.astral.sh/ruff/) pour le **lint** et le **formatage** (configuration dans [`pyproject.toml`](pyproject.toml)). C’est un seul outil pour les deux usages, configuré pour cibler Python 3.10+.

Installation des dépendances de développement :

```bash
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

Commandes courantes :

```bash
ruff check .            # vérifier le lint
ruff check . --fix      # corriger automatiquement ce qui peut l’être
ruff format .           # appliquer le formatage
ruff format --check .   # vérifier le formatage sans modifier
```

Toute modification doit garder `ruff check .` et `ruff format --check .` verts avant push.

### Prérequis côté build

- Un Mac avec **Python 3.10+** et **Tkinter** (sur Homebrew : `python@3.12` **et** `python-tk@3.12`, comme pour le développement).
- Dans le dépôt : venv activé, `pip install -r requirements.txt`, puis PyInstaller (voir `requirements.txt` ou `pip install pyinstaller`).

### Build PyInstaller (fichier `.spec` recommandé)

Le fichier **[`ConvertisseurMarkdownIA.spec`](ConvertisseurMarkdownIA.spec)** est la référence de build (mode fenêtré, collecte complète de **markitdown**). Préférez-le aux commandes manuelles ci-dessous.

```bash
cd markdown-converter   # racine du dépôt cloné (dossier contenant main.py)
source .venv/bin/activate
python3 -m pip install pyinstaller
python3 -m PyInstaller --noconfirm ConvertisseurMarkdownIA.spec
```

Le résultat se trouve dans **`dist/Convertisseur Markdown IA.app`**.

**Alternative** en une ligne (équivalent approximatif sans fichier `.spec` dédié) :

```bash
pyinstaller --windowed --name "Convertisseur Markdown IA" --collect-all markitdown main.py
```

### Archive ZIP pour distribution (`build_mac_app.sh`)

Pour régénérer `dist/…` et créer une archive prête à envoyer (`.app` + `LISEZMOI.txt` dérivé de [`docs/LISEZMOI_COLLEGUES.txt`](docs/LISEZMOI_COLLEGUES.txt)) :

```bash
./scripts/build_mac_app.sh
```

Cela crée à la racine du projet une archive du type **`ConvertisseurMarkdownIA-mac-AAAAMMJJ-HHMM.zip`**.

### Ce que font les utilisateurs du ZIP

- Télécharger / récupérer le **ZIP**, le décompresser, glisser **« Convertisseur Markdown IA.app »** dans **Applications**.
- Au **premier lancement**, si macOS bloque l’app (développeur non identifié) : **clic droit → Ouvrir** sur l’icône, ou autoriser dans **Réglages système → Confidentialité et sécurité**. Sans **signature / notarisation Apple** (compte développeur payant), ce comportement est normal pour une app interne.
- **Pandoc** n’est **pas** dans le bundle : le secours Pandoc ne fonctionne que si Pandoc est installé séparément sur leur Mac ; l’app fonctionne sans.

### Vérification avant envoi

Tester le **`.app` sur un Mac sans le dépôt ni le venv** (compte test ou collègue) : lancement, conversion d’un petit `.docx` / `.pdf`, présence de `rapport_conversion.md`.

### Option « plus propre » : DMG

Pour une fenêtre « glisser vers Applications » au lieu d’un simple ZIP, vous pouvez créer une image disque avec **`hdiutil`** (ligne de commande macOS) ou un outil comme **`create-dmg`** ; le contenu reste le même `.app`.

### Phase ultérieure (IT stricte)

Si l’entreprise impose des apps **notarisées** : compte Apple Developer, **codesign**, **notarytool**, **stapler** sur le `.app` — hors périmètre du script de build actuel.

### Dépendances système éventuelles (build / runtime)

- **PDF** : les bibliothèques empaquetées avec MarkItDown/`[pdf]` couvrent en principe la lecture locale ; selon versions, des binaires ou libs peuvent nécessiter des réglages PyInstaller (`--hidden-import`, `--collect-binaries`).
- **Pandoc** : si vous comptez sur le secours Pandoc dans l’app packagée, Pandoc doit être installé **sur la machine utilisateur** (non inclus dans le bundle PyInstaller par défaut).

Testez toujours le `.app` sur une machine « propre » avant distribution.

---

## Licence

**Statut : `License: TBD` (à définir).**

- Aucun fichier `LICENSE` n’est encore présent dans ce dépôt ; le choix (MIT, Apache-2.0, GPL-3.0, autre) est en cours de réflexion par les mainteneurs.
- En attendant, considérez le contenu du dépôt comme **non licencié pour la réutilisation** : contactez les mainteneurs si vous souhaitez forker, redistribuer ou intégrer ce code dans un autre produit.

Une fois la licence choisie, cette section sera remplacée par l’identifiant SPDX (ex. `MIT`, `Apache-2.0`) et un lien vers le fichier `LICENSE`.
