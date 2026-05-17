# Markdown Converter (MVP)

[![CI](https://github.com/ZitDantes/markdown-converter/actions/workflows/ci.yml/badge.svg)](https://github.com/ZitDantes/markdown-converter/actions/workflows/ci.yml)
[![Licence : MIT](https://img.shields.io/badge/Licence-MIT-blue.svg)](LICENSE)

Le code source est distribué sous **licence MIT** (voir le fichier [`LICENSE`](LICENSE) à la racine). Vous pouvez réutiliser et modifier le logiciel librement, sous réserve de conserver l’avis de copyright et la licence.

Application **macOS** (Python 3) pour convertir en lot des documents bureautiques en fichiers **Markdown** (UTF-8), en vue d’alimenter une base de connaissances ou un système RAG. **Tout est local** : aucune donnée n’est envoyée vers un service cloud.

**Guide pas à pas (installation, interface Qt, dépannage)** : [`docs/README.md`](docs/README.md).

## Table des matières

- [Documentation utilisateur (`docs/`)](docs/README.md)
- [Pour les utilisateurs](#pour-les-utilisateurs)
  - [Télécharger la dernière version](#telecharger-la-derniere-version)
- [Logs et diagnostic](#logs-et-diagnostic)
- [Qualité, limites et bonnes pratiques](#qualite-limites-et-bonnes-pratiques)
- [Pour les développeurs et la distribution (macOS)](#pour-les-developpeurs-et-la-distribution-macos)
- [Contribuer au projet](CONTRIBUTING.md)
- [Licence](#licence)

---

## Pour les utilisateurs

### Télécharger la dernière version

L’option **la plus simple** pour utiliser l’application sans rien installer côté développement : récupérer le bundle `.app` packagé depuis la page **[Releases](https://github.com/ZitDantes/markdown-converter/releases/latest)** du dépôt.

1. Télécharger l’archive `MarkdownConverter-mac-vX.Y.Z.zip` attachée à la dernière release.
2. La décompresser, puis glisser **« Markdown Converter.app »** dans le dossier **Applications**.
3. Voir [Ce que font les utilisateurs du ZIP](#ce-que-font-les-utilisateurs-du-zip) pour les détails du premier lancement (autorisation Gatekeeper).

Pour suivre le détail des changements entre versions : voir [`CHANGELOG.md`](CHANGELOG.md). Pour exécuter l’application depuis les sources (développeurs ou contributeurs), suivez plutôt les sections ci-dessous.

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

## Logs et diagnostic

L’application écrit un **fichier de log persistant** en plus du journal visible dans la fenêtre. Trois niveaux sont utilisés : **INFO** (information), **WARNING** (avertissement, conversion à surveiller) et **ERROR** (échec, fichier non produit).

### Où trouver le fichier de log

- **macOS** : `~/Library/Logs/MarkdownConverter/run.log` (visible aussi dans **Console.app**, section *Fichiers journaux*).
- **Autres systèmes** : `~/.markdown-converter/logs/run.log`.

**Mise à jour** : si vous utilisiez une version antérieure du produit, les journaux étaient dans `~/Library/Logs/ConvertisseurMarkdownIA/` (macOS) ou `~/.convertisseur-markdown-ia/logs/` (autres systèmes). Ces emplacements ne sont plus utilisés ; vous pouvez les examiner puis les supprimer manuellement si vous n’en avez plus besoin.

Le chemin exact est affiché dans la première ligne du journal au démarrage de l’app.

### Rotation

Le fichier est limité à **~1 Mo** ; au-delà, il est archivé en `run.log.1`, `run.log.2`, etc. (5 backups). Aucune action n’est requise.

### Surcharger l’emplacement (cas avancé)

L’environnement `CONVERTISSEUR_LOG_DIR` permet de pointer vers un autre dossier, utile pour les tests ou un déploiement spécifique :

```bash
export CONVERTISSEUR_LOG_DIR="$HOME/Desktop/logs-markdown-converter"
python3 main.py
```

### En cas de problème

Joignez **`run.log`** (et les `.1`, `.2`… si l’erreur est ancienne) à votre demande de support : ils contiennent les horodatages, niveaux et messages techniques nécessaires au diagnostic.

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

Pour **contribuer au code** (correctifs, évolutions, documentation technique), suivez le guide **[CONTRIBUTING.md](CONTRIBUTING.md)** (setup, lint, tests, commits, PR, dépendances).

### Structure du projet

| Fichier ou dossier | Rôle |
|--------------------|------|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Guide de contribution (humains) : setup, lint, tests, PR, dépendances. |
| `main.py` | Lancement de l’application. |
| `ui.py` | Interface Tkinter (français, **par défaut**). |
| `ui_qt.py` | Interface PySide6 (opt-in via `MARKDOWN_CONVERTER_UI=qt`, voir [Prototype d'UI PySide6](#prototype-dui-pyside6)). |
| `ui_qt_file_drop_table.py` | Vue de file avec glisser-déposer natif (fichiers et dossiers, même règles que l'ajout par boutons). |
| `ui_qt_settings.py` | Chemins et lecture/écriture du fichier JSON de préférences Qt (thème, file, dossier de sortie). |
| `ui_qt_theme.py` | Application du thème clair / sombre (palette Fusion). |
| `requirements-qt.txt` | Dépendances optionnelles pour l'UI PySide6 (`PySide6`). |
| `converter.py` | Orchestration du lot (boucle, statut par fichier, rapport). |
| `engines/` | Moteurs de conversion isolés derrière une interface commune. |
| `engines/base.py` | Classe abstraite `ConverterEngine` et exceptions custom. |
| `engines/markitdown_engine.py` | Moteur principal **MarkItDown** (import paresseux). |
| `engines/pandoc_engine.py` | Moteur de secours **Pandoc** (binaire externe). |
| `report.py` | Génération de `rapport_conversion.md`. |
| `logging_setup.py` | Configuration centralisée du logging (fichier rotatif + callback UI). |
| `errors.py` | Hiérarchie d’exceptions métier (`ConverterError` et descendants). |
| `utils.py` | Extensions, chemins, nettoyage Markdown, avertissements par format. |
| `MarkdownConverter.spec` | Définition PyInstaller (build `.app` reproductible). |
| `scripts/build_mac_app.sh` | Script : PyInstaller + ZIP daté + LISEZMOI pour collègues. |
| `docs/README.md` | Index de la **documentation utilisateur** (guides en `docs/utilisateur/`). |
| `docs/LISEZMOI_COLLEGUES.txt` | Texte d’accompagnement pour l’archive distribuée. |
| `samples/` | Dossier local pour les documents de test (ignoré par git, voir [`samples/README.md`](samples/README.md)). |
| `tests/` | Suite pytest (`unit/`, `integration/`, `fixtures/`, `conftest.py`). |

L'API de `converter.py` (callbacks `on_log(level, message)` / `on_progress(index, total, label[, percent])`) est pensée pour pouvoir brancher une autre interface (par ex. PySide6) plus tard sans réécrire la logique métier. Le quatrième argument `percent` (0.0-1.0, part globale du lot) est optionnel : les callbacks à trois arguments restent valides. Le callback `on_log` est branché en interne sur le logger nommé `markdown_converter` ; tout passe donc aussi par le fichier de log persistant (voir [Logs et diagnostic](#logs-et-diagnostic)).

Pour les UIs qui veulent afficher un **aperçu** du Markdown produit sans relire le disque, `convert_files(..., keep_output_in_memory=True)` remplit `FileConversionRecord.output_md_text` avec le contenu exact écrit (front-matter + corps). Par défaut le champ reste `None` pour éviter de charger inutilement la RAM sur de gros lots. L'argument optionnel `use_conversion_fallback` (défaut `True`) permet de désactiver le secours ; voir [`converter.py`](converter.py) et la section prototype Qt ci-dessous.

#### Prototype d'UI PySide6

L'interface Tkinter (`ui.py`) reste l'UI par défaut. L'UI PySide6 vit dans `ui_qt.py` et les modules `ui_qt_*.py` ; l'épic [PLO-26](https://linear.app/dantes/issue/PLO-26) est **terminé** (sous-tickets [PLO-34](https://linear.app/dantes/issue/PLO-34) à [PLO-39](https://linear.app/dantes/issue/PLO-39)). Pour l'essayer :

```bash
source .venv/bin/activate
pip install -r requirements-qt.txt   # ajoute PySide6 (dépendance facultative)
MARKDOWN_CONVERTER_UI=qt python3 main.py
```

La **file** de conversion (tri, filtres, recherche, **glisser-déposer** de fichiers et dossiers depuis le gestionnaire de fichiers avec surbrillance au survol), l'exécution du lot dans un **thread** dédié, la **toolbar**, l'**inspecteur** (aperçu Markdown, sortie, détails), le **journal** repliable et le **pied de page** (progression, ETA, rapport) sont implémentés. **Thème clair / sombre** : boutons **« Sombre »** / **« Clair »** dans la barre de titre ; préférence enregistrée dans un fichier ``settings.json`` (Linux : ``~/.config/markdown-converter/`` ; macOS : ``~/Library/Application Support/Markdown Converter/`` ; Windows : ``%APPDATA%\Markdown Converter\``). **Session Qt** ([PLO-29](https://linear.app/dantes/issue/PLO-29)) : la liste des **chemins sources** (clés JSON ``source_paths``, jusqu'à 100 entrées) et le **dossier de sortie** (``output_dir``) sont relus au prochain lancement ; les fichiers absents ou formats non pris en charge ne sont pas remis en file ; un dossier de sortie enregistré mais devenu invalide est ignoré sans message d'erreur. **Modes Standard / Strict** ([PLO-40](https://linear.app/dantes/issue/PLO-40)) : le mode **Strict** désactive le secours dans ``convert_files(..., use_conversion_fallback=False)`` ; l'interface Tk n'expose pas encore ce réglage. **Forçage exclusif de la voie de secours** : hors surface produit ; une variable d'environnement ou des préférences avancées pourront le proposer plus tard — ce n'est pas encore implémenté (aucune variable active à ce jour). Variable optionnelle ``MARKDOWN_CONVERTER_SETTINGS_DIR`` pour forcer le dossier de configuration (tests, portable). La suite (exposition des moteurs, etc.) est suivie dans le projet Linear [Refonte interface (PySide6)](https://linear.app/dantes/project/refonte-interface-pyside6-a49711c9504d). Si PySide6 n'est pas installé alors que `MARKDOWN_CONVERTER_UI=qt`, l'application affiche un message et retombe automatiquement sur Tkinter.

#### Prototype d'UI web (WebEngine)

Socle **Vite + React** embarqué dans Qt WebEngine ([PLO-46](https://linear.app/dantes/issue/PLO-46)) ; contrat pont : [`docs/adr/0001-contrat-pont-webchannel-js-python.md`](docs/adr/0001-contrat-pont-webchannel-js-python.md).

```bash
source .venv/bin/activate
pip install -r requirements-qt.txt
./scripts/build_web.sh          # ou : cd web && npm ci && npm run build
MARKDOWN_CONVERTER_UI=web python3 main.py
```

**Node.js** est requis pour **construire** le front (`web/`), pas pour lancer l'app une fois `web/dist/` généré. Détails : [`web/README.md`](web/README.md).

Si **Qt WebEngine** est absent, l'app affiche un message en français et bascule par défaut vers l'interface **Qt widgets** (`MARKDOWN_CONVERTER_WEB_FALLBACK`, voir `web/README.md`).

#### Ajouter un moteur de conversion

Pour ajouter un nouveau moteur (OCR, conversion cloud, format exotique…), il suffit de :

1. Créer un fichier `engines/<nom>_engine.py` avec une classe qui hérite de [`ConverterEngine`](engines/base.py) et implémente `is_available()`, `supports(path)` et `convert(path) -> str`.
2. Exposer la nouvelle classe dans `engines/__init__.py`.
3. La brancher dans l’orchestration de [`convert_files()`](converter.py) (ordre de priorité, secours, etc.).

L’interface garantit que l’orchestrateur n’a pas besoin de connaître les détails du moteur.

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

### Tests (pytest)

Le projet utilise [pytest](https://docs.pytest.org/) (configuration dans [`pyproject.toml`](pyproject.toml), section `[tool.pytest.ini_options]`). La suite est organisée ainsi :

| Dossier | Rôle |
|---|---|
| `tests/unit/` | Tests unitaires des fonctions pures (ex. `utils.py`). |
| `tests/integration/` | Tests de bout en bout sur `converter.convert_files()` avec de petits fichiers réels. |
| `tests/fixtures/` | Documents minimaux versionnés (sans donnée personnelle) utilisés par les tests. |
| `tests/conftest.py` | Fixtures partagées : isolation du dossier de logs via `CONVERTISSEUR_LOG_DIR`, accès à `fixtures_dir`. |

Lancement local :

```bash
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt   # installe pytest si besoin
pytest                                            # toute la suite
pytest tests/unit                                 # uniquement les tests unitaires
pytest -k normalize_extension                     # filtrer par nom de test
```

La suite doit rester verte avant tout push. Les tests **n'écrivent jamais** dans `~/Library/Logs/…` : la fixture `_isolated_log_dir` redirige les logs vers un dossier temporaire.

### Intégration continue (GitHub Actions)

Sur chaque **pull request** et sur chaque **push** vers `main`, le workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) exécute automatiquement :

- **ruff check** (lint) ;
- **ruff format --check** (formatage, sans modifier les fichiers) ;
- **pytest** (toute la suite) ;
- **build front** (`./scripts/build_web.sh`, Node.js 20, dossier `web/`) — job parallèle **PLO-47**.

Les versions **Python 3.10, 3.11 et 3.12** sont testées sur **Ubuntu** (matrice Python). Le front est compilé sur **Ubuntu** avec **Node.js 20**. Le badge CI en tête de ce fichier renvoie vers la dernière exécution sur la branche par défaut.

> **Note** : une ancienne version du backlog mentionnait *black* ; le projet utilise uniquement **ruff** pour le lint et le format (cf. section [Lint et formatage (ruff)](#lint-et-formatage-ruff)).

### Prérequis côté build

- Un Mac avec **Python 3.10+** et **Tkinter** (sur Homebrew : `python@3.12` **et** `python-tk@3.12`, comme pour le développement).
- Dans le dépôt : venv activé, `pip install -r requirements.txt`, puis PyInstaller (voir `requirements.txt` ou `pip install pyinstaller`).

### Build PyInstaller (fichier `.spec` recommandé)

Le fichier **[`MarkdownConverter.spec`](MarkdownConverter.spec)** est la référence de build (mode fenêtré, **markitdown**, **Qt WebEngine**, front **`web/dist`** embarqué). L’UI par défaut dans le bundle est **`MARKDOWN_CONVERTER_UI=web`** (repli Qt/Tk documenté dans [`web/README.md`](web/README.md)).

```bash
cd markdown-converter   # racine du dépôt cloné (dossier contenant main.py)
source .venv/bin/activate
python3 -m pip install -r requirements.txt -r requirements-qt.txt pyinstaller
./scripts/build_web.sh
python3 -m PyInstaller --noconfirm MarkdownConverter.spec
```

- **macOS** : **`dist/Markdown Converter.app`**
- **Linux** : dossier **`dist/Markdown Converter/`** (pas de `.app` ; voir ci‑dessous)

**Taille (ordre de grandeur, macOS arm64)** :

| Artefact | Taille typique |
|----------|----------------|
| `Markdown Converter.app` seul | **~550 Mo** (`du -sh`) |
| Archive ZIP | **~1,1 Go** (compression faible sur binaires Qt) |

Le Finder peut afficher une valeur plus élevée (métadonnées, copies locales). **Ne pas cumuler** ZIP + `.app` décompressée + dossier `dist/` du build : cela double ou triple l’espace disque perçu.

L’ajout de WebEngine dépasse la limite **GitHub Release (100 Mo/fichier)** : prévoir hébergement alternatif, découpage, ou release « widgets seule » sans WebEngine (voir historique v0.2).

**Alternative** en une ligne (équivalent approximatif sans fichier `.spec` dédié) :

```bash
pyinstaller --windowed --name "Markdown Converter" --collect-all markitdown main.py
```

### Archive ZIP pour distribution (`build_mac_app.sh`)

Pour régénérer `dist/…` et créer une archive prête à envoyer (`.app` + `LISEZMOI.txt` dérivé de [`docs/LISEZMOI_COLLEGUES.txt`](docs/LISEZMOI_COLLEGUES.txt)) :

```bash
./scripts/build_mac_app.sh              # build web + PyInstaller ; archive horodatée
./scripts/build_mac_app.sh v0.1.0       # archive nommée pour une release GitHub
```

Le script affiche la **taille du .app** et du **ZIP** à la fin du build.

### Build Linux (`build_linux_app.sh`)

Sur **Ubuntu 22.04+** (ou équivalent), après les paquets listés dans [`spike/webengine/README.md`](spike/webengine/README.md) :

```bash
./scripts/build_linux_app.sh
./scripts/build_linux_app.sh v0.3.0     # produit MarkdownConverter-linux-v0.3.0.tar.gz
```

Lancement : extraire l’archive, puis exécuter `./Markdown\ Converter/Markdown\ Converter` depuis le dossier extrait.

Sans argument, l’archive porte un nom du type **`MarkdownConverter-mac-AAAAMMJJ-HHMM.zip`**. Avec un argument de version (ex. `v0.1.0`), elle s’appelle **`MarkdownConverter-mac-v0.1.0.zip`**, prête à être attachée à une [GitHub Release](https://github.com/ZitDantes/markdown-converter/releases).

### Ce que font les utilisateurs du ZIP

- Télécharger / récupérer le **ZIP**, le décompresser, glisser **« Markdown Converter.app »** dans **Applications**.
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

**SPDX : `MIT`**

Le projet **Markdown Converter** est publié sous la [licence MIT](https://opensource.org/licenses/MIT). Le texte juridique complet se trouve dans le fichier [`LICENSE`](LICENSE) à la racine du dépôt.

**Pourquoi le MIT ?** C’est une licence permissive et largement adoptée dans l’écosystème Python ; elle autorise usage commercial et intégration dans des produits propriétaires, tout en limitant la responsabilité légale des auteurs (« tel quel », sans garantie). Elle ne requiert pas d’en-tête de licence dans chaque fichier source (contrairement au copyleft type GPL).

Les **binaires** distribués via [GitHub Releases](https://github.com/ZitDantes/markdown-converter/releases) empaquetent des dépendances tierces (ex. [MarkItDown](https://github.com/microsoft/markitdown)) soumises à **leurs propres licences** ; en cas de redistribution du bundle, vérifiez la conformité avec ces licences.
