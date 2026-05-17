# Journal des modifications

Le format est inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), et ce projet adhère au [versionnement sémantique](https://semver.org/lang/fr/) (`MAJOR.MINOR.PATCH`).

## [Unreleased]

## [0.3.2] — 2026-05-17

### Corrigé

- **Crash au lancement du `.app` macOS** : PyInstaller rangeait `QtWebEngineProcess` et les ressources Chromium sous `Versions/Resources/` au lieu de `Versions/A/`. Réparation au build (`webengine_macos_repair.py`) + variables `QTWEBENGINEPROCESS_PATH` / `QTWEBENGINE_RESOURCES_PATH` au runtime.

## [0.3.1] — 2026-05-17

### Corrigé

- **Packaging macOS** : l’archive `MarkdownConverter-mac-*.zip` utilisait `zip -rq`, qui **dupliquait les hard links** de Qt WebEngine (~2,9 Go décompressés au lieu de ~550 Mo). Le script `build_mac_app.sh` emploie désormais **`ditto -c -k`** (~200 Mo de ZIP, ~550 Mo une fois le `.app` extrait).

### À retenir pour les utilisateurs

- Préférer **`MarkdownConverter-mac-v0.3.1.zip`** (ou une release ultérieure). L’asset **v0.3.0** sur GitHub est **gonflé** : même application, mais archive incorrecte.

## [0.3.0] — 2026-05-17

Version orientée **interface web locale** (React + Vite) embarquée dans **PySide6 + Qt WebEngine**, avec pont **QWebChannel** vers le moteur Python existant. Clôture de l’epic UI web ([PLO-43](https://linear.app/dantes/issue/PLO-43)).

### Ajouté

- **UI web** (`MARKDOWN_CONVERTER_UI=web`) : shell PySide6 + `QWebEngineView`, front `web/` (layout, file, toolbar, inspecteur, journal, glisser-déposer, modes Standard / Strict).
- **Contrat pont** : ADR 0001 (`docs/adr/0001-contrat-pont-webchannel-js-python.md`), schéma v0 (`bridge_contract/`, `web/shared/bridge-contract.ts`).
- **CI** : build du front (`npm ci` / `npm run build`) en échec si le bundle casse.
- **Fallback** : si WebEngine est indisponible, repli **Tkinter** (variable `MARKDOWN_CONVERTER_WEB_FALLBACK`, défaut `tk`).
- **Spike** documenté : `spike/webengine/` (chargement `file:` / `qrc:`).

### Modifié

- **Bundle macOS** : UI **web** par défaut dans le `.app` (plus les widgets Qt legacy).
- **Archivage** : modules `ui_qt_*` widgets déplacés vers `archive/ui_qt_widgets/` ; modules partagés (`ui_qt_file_model`, worker, inspecteur) conservés pour le pont web.
- **Signaux QWebChannel** : ordre de chargement `qwebchannel.js`, connexion typée ; polling `getQueueState` pendant la conversion pour la file et la barre de progression (limitation WebEngine).

### À retenir pour les utilisateurs

- Distribution macOS : voir **v0.3.1** pour la taille correcte (~550 Mo `.app`, ~200 Mo ZIP). La v0.3.0 avait un ZIP défectueux (~2,9 Go décompressés).
- Depuis les sources : `cd web && npm ci && npm run build` puis `MARKDOWN_CONVERTER_UI=web python3 main.py`.
- `MARKDOWN_CONVERTER_UI=qt` est **obsolète** (traité comme `web`).
- L’interface **Tkinter** reste disponible (`MARKDOWN_CONVERTER_UI=tk` ou repli automatique).
- **100 % local** — aucun appel réseau au runtime.

## [0.2.0] — 2026-05-15

Version orientée **interface graphique PySide6** (UI Qt complète) et **documentation utilisateur** dans le dépôt (`docs/`).

### Ajouté

- **Interface PySide6** (opt-in via `MARKDOWN_CONVERTER_UI=qt`) : file de conversion avec statuts et progression par fichier, inspecteur (aperçu / sortie / détails), journal repliable avec filtres, thème clair/sombre persistant, glisser-déposer, modes **Standard** / **Strict**, persistance de la file et du dossier de sortie (`settings.json`).
- **Documentation utilisateur** : guide dans [`docs/`](docs/README.md) (installation, premiers pas, interface, dépannage, confidentialité).
- Fichier [`LICENSE`](LICENSE) à la racine : **licence MIT** (copyright 2026 ZitDantes) ; README et CONTRIBUTING alignés.
- Tests d’intégration UI Qt (`QT_QPA_PLATFORM=offscreen`) en CI (Python 3.12).

### Modifié

- Statuts de conversion enrichis (`SUCCESS_REVIEW`, `SUCCESS_FALLBACK`, `QUEUED`, progression par fichier, aperçu Markdown en mémoire optionnel).
- README : section prototype Qt mise à jour ; lien vers la documentation `docs/`.

### À retenir pour les utilisateurs

- L’UI **recommandée** en v0.2 est **Qt** (`MARKDOWN_CONVERTER_UI=qt` depuis les sources ; voir [docs/utilisateur/02-installation.md](docs/utilisateur/02-installation.md)).
- L’interface **Tkinter** reste disponible par défaut si la variable d’environnement n’est pas définie.
- Distribution macOS : archive `MarkdownConverter-mac-v0.2.0.zip` sur GitHub Releases (~310 Mo : MarkItDown + PySide6 ; interface **Qt** par défaut dans le `.app` via `LSEnvironment`).

## [0.1.0] — 2026-05-13

Première version publique. Conclut l’EPIC « Stabiliser le MVP ».

### Ajouté

- **Architecture modulaire** : moteurs de conversion isolés derrière une interface commune `ConverterEngine` (`engines/base.py`), implémentations `MarkItDownEngine` (principal) et `PandocEngine` (secours). Voir [PR #3](https://github.com/ZitDantes/markdown-converter/pull/3).
- **Typologie d’erreurs** : hiérarchie `ConverterError` (`UnsupportedFormatError`, `EngineFailureError`, `EmptyConversionError`, `OutputWriteError`) ; timeout configurable sur Pandoc ; champ `error_type` dans le rapport. Voir [PR #6](https://github.com/ZitDantes/markdown-converter/pull/6).
- **Logging structuré** : niveaux INFO/WARNING/ERROR, fichier de log persistant rotatif (`RotatingFileHandler`, 1 Mo, 5 backups), callback UI couleur. Voir [PR #7](https://github.com/ZitDantes/markdown-converter/pull/7).
  - macOS : `~/Library/Logs/MarkdownConverter/run.log` (visible dans Console.app).
  - Autres systèmes : `~/.markdown-converter/logs/run.log`.
  - Variable d’environnement `CONVERTISSEUR_LOG_DIR` pour override.
- **Suite de tests** : pytest (31 tests, unitaires + intégration) avec isolation automatique du dossier de logs. Voir [PR #8](https://github.com/ZitDantes/markdown-converter/pull/8).
- **CI GitHub Actions** : workflow matriciel Python 3.10 / 3.11 / 3.12 sur Ubuntu (ruff check + ruff format --check + pytest), badge dans le README. Voir [PR #9](https://github.com/ZitDantes/markdown-converter/pull/9).
- **Documentation contributeurs** : [`CONTRIBUTING.md`](CONTRIBUTING.md) à la racine (setup, tests, commits, PR, dépendances) ; [`AGENTS.md`](AGENTS.md) pour les agents IA. Voir [PR #10](https://github.com/ZitDantes/markdown-converter/pull/10).
- **Skill Cursor `code-review`** : checklist de revue de PR (bloquants / suggestions / points positifs) alignée sur AGENTS.md.

### Modifié

- **Nom du produit** : `Convertisseur Markdown IA` → **Markdown Converter**, en cohérence avec le slug du repo. Renommage du `.spec` PyInstaller, du `.app` produit, du préfixe d’archive ZIP, et de l’identifiant de bundle macOS (`io.github.zitdantes.markdownconverter`). Voir [PR #11](https://github.com/ZitDantes/markdown-converter/pull/11).
- **Outillage qualité** : ruff configuré comme unique outil de lint et de formatage (pas de Black séparé), `pyproject.toml`. Voir [PR #2](https://github.com/ZitDantes/markdown-converter/pull/2).
- **README** : restructuration en sections utilisateur / qualité / développeur ; table des matières ; section *Logs et diagnostic* ; lien vers `CONTRIBUTING.md`.

### Breaking

- **Chemin du dossier de logs** : les anciennes installations écrivaient dans `~/Library/Logs/ConvertisseurMarkdownIA/` (macOS) ou `~/.convertisseur-markdown-ia/logs/` (autres systèmes). Ces emplacements ne sont plus utilisés ; **aucune migration automatique** n’est faite. Vous pouvez supprimer manuellement ces dossiers s’ils contiennent uniquement les logs d’une ancienne version du produit.

### À retenir pour les utilisateurs

- L’application reste **100 % locale** : aucun appel réseau, aucune télémétrie.
- macOS uniquement pour le moment, bundle PyInstaller fourni dans la release (`MarkdownConverter-mac-v0.1.0.zip`).
- Au premier lancement, macOS peut bloquer l’application (développeur non identifié) : clic droit → **Ouvrir**, ou autoriser dans **Réglages système → Confidentialité et sécurité**. L’app n’est pas notarisée Apple.
