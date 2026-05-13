# Contribuer au projet

Merci de l’intérêt que vous portez à ce dépôt. Ce guide résume ce qu’il faut savoir pour proposer des changements de façon alignée avec l’équipe et la CI.

Pour le **contexte produit**, les prérequis (macOS, Python, Tkinter) et l’installation pas à pas, voir le **[README.md](README.md)**.

Pour le **workflow détaillé** (Linear, agents IA, actions à valider explicitement), voir **[AGENTS.md](AGENTS.md)** — ce fichier complète le présent guide sans le dupliquer.

---

## Setup local

1. Cloner le dépôt et se placer à la racine (dossier contenant `main.py`).
2. Créer un environnement virtuel **Python 3.10 ou plus** et activer le venv.
3. Installer les dépendances d’exécution et de développement :

   ```bash
   python3 -m pip install --upgrade pip
   python3 -m pip install -r requirements.txt -r requirements-dev.txt
   ```

4. Lancer l’application :

   ```bash
   python3 main.py
   ```

Les détails (Homebrew, `python-tk`, Pandoc optionnel) sont dans le README.

---

## Lancer les tests et le lint

Avant d’ouvrir une PR, la suite suivante doit être **verte** localement (c’est ce que la CI GitHub exécute aussi) :

```bash
ruff check .
ruff format --check .
pytest
```

- Configuration **ruff** et **pytest** : [`pyproject.toml`](pyproject.toml).
- Workflow CI : [`.github/workflows/ci.yml`](.github/workflows/ci.yml) (matrice Python 3.10, 3.11, 3.12 sur Ubuntu).

---

## Style de code

- **Langue** : code, interface utilisateur, messages utilisateur et rapports en **français** (convention du projet).
- **Lint et formatage** : uniquement **ruff** (pas de Black séparé). Ne pas désactiver une règle sans justification dans la PR.
- **Portée des changements** : préférer des diffs ciblés ; éviter les refactors opportunistes hors sujet du ticket.

---

## Commits

- Messages en **français**, à l’**impératif**, **≤ 72 caractères** sur la première ligne.
- Préfixe obligatoire pour les travaux suivis dans Linear : **`PLO-<n>:`** (ex. `PLO-15: ajouter CONTRIBUTING.md`) — cela active l’auto-lien entre GitHub et Linear.
- **Un commit = un changement cohérent** ; corps de message facultatif pour expliquer le *pourquoi*.

Voir aussi la section **Style de commit et de PR** dans [`AGENTS.md`](AGENTS.md).

---

## Pull requests

1. **Branche** depuis `main` à jour : `PLO-<n>-<slug-court-en-kebab>` (ex. `PLO-15-contributing`).
2. **Titre de PR** : `PLO-<n> — <description courte>`.
3. **Description** : objectif, résumé des changements, `Closes PLO-<n>` pour fermer le ticket au merge, plan de test manuel si UI ou packaging.
4. **Review** : une relecture structurée est attendue avant fusion. Les mainteneurs utilisent le skill Cursor [`code-review`](.cursor/skills/code-review/SKILL.md) (verdict bloquants / suggestions / points positifs). Sur ce dépôt, l’auto-approbation GitHub d’une PR par son auteur peut être impossible : une review sous forme de **commentaire** sur la PR reste valable.

Après merge, si l’option GitHub **« Automatically delete head branches »** est activée, la branche distante est supprimée automatiquement ; en local : `git fetch --prune` puis `git branch -d PLO-<n>-...` si besoin.

---

## Nouvelles dépendances

- Toute dépendance ajoutée à **`requirements.txt`** (runtime) ou **`requirements-dev.txt`** (outillage) doit être **justifiée** dans le message de commit et/ou la description de la PR (usage, alternative envisagée, impact taille / sécurité).
- L’application doit rester **100 % locale** : pas d’appels réseau, télémétrie ou API cloud sans discussion préalable dans un ticket et accord explicite des mainteneurs (voir [`AGENTS.md`](AGENTS.md) §9).

---

## Issues et propositions de fonctionnalités

- Le backlog est géré dans **Linear** (équipe préfixe `PLO`). Pour un sujet **non trivial**, ouvrir ou demander l’ouverture d’un **ticket** avant de développer longtemps dans le vide — cela aligne la portée et évite le travail rejeté.
- Pour un **correctif** ciblé (typo, bug évident), une PR directe peut suffire ; mentionnez le contexte dans la description.
- Ne pas committer de **secrets**, tokens ou chemins absolus contenant des données personnelles.

---

## Résumé des liens utiles

| Sujet | Fichier |
|---|---|
| Installation et usage | [README.md](README.md) |
| Workflow Linear, agents, règles d’orchestration | [AGENTS.md](AGENTS.md) |
| CI (ruff + pytest) | [.github/workflows/ci.yml](.github/workflows/ci.yml) |
| Revue de PR (checklist) | [.cursor/skills/code-review/SKILL.md](.cursor/skills/code-review/SKILL.md) |

Encore merci pour votre contribution.
