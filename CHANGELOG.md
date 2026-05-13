# Journal des modifications

Le format est inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), et ce projet adhère au [versionnement sémantique](https://semver.org/lang/fr/) (`MAJOR.MINOR.PATCH`).

## [Unreleased]

### Ajouté

- Fichier [`LICENSE`](LICENSE) à la racine : **licence MIT** (copyright 2026 ZitDantes) ; README et CONTRIBUTING alignés.

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
