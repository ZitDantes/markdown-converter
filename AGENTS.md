# AGENTS.md — Convertisseur Markdown IA

Ce fichier décrit comment les agents IA (Cursor, et tout autre outil compatible AGENTS.md) doivent collaborer sur ce projet. Il complète `README.md` (qui s'adresse aux humains).

## 1. Stack et rôles

- **Linear** (préfixe d'équipe : `PLO`) — source de vérité du **backlog**, des specs et de l'avancement.
- **GitHub** (`ZitDantes/markdown-converter`) — code, Pull Requests, Releases.
- **Cursor** — environnement de développement, avec le MCP Linear actif.

L'humain **ZitDantes** reste **chef d'orchestre** : l'agent **propose**, il **ne dispose pas**.

## 2. Règles d'orchestration (non négociables)

L'agent doit **demander une confirmation explicite** avant toute action ayant un effet externe :

- `git commit`, `git push`, `git merge`, création/suppression de branche distante
- Création/modification/suppression d'un ticket Linear, changement de statut
- Création d'une Pull Request, d'une Release, d'un tag
- `pip install` / modification de `requirements.txt`
- Toute commande destructive (`rm -rf`, `git reset --hard`, force push, etc.)

Lecture, exploration du code, propositions de diffs, et exécution de tests locaux non destructifs : **autorisés sans confirmation**.

## 3. Boucle de travail standard

Pour toute nouvelle tâche significative :

1. **Comprendre le besoin** — récupérer le ticket Linear concerné (`PLO-<n>`) via le MCP et reformuler l'objectif en une phrase pour validation.
2. **Branche dédiée** — `PLO-<n>-<slug-court-en-kebab>` (ex. `PLO-12-fix-pdf-encoding`). Toujours brancher depuis `main` à jour.
3. **Commits atomiques** — message au format :
   ```
   PLO-<n>: <verbe à l'impératif, description courte>
   ```
   L'ID Linear en préfixe active l'**auto-link** Linear ↔ GitHub.
4. **Pull Request** — titre `PLO-<n> — <description>`, description contenant `Closes PLO-<n>` pour fermer automatiquement le ticket au merge.
5. **Review structurée** — avant le merge, lancer le skill [`code-review`](.cursor/skills/code-review/SKILL.md) qui restitue un verdict (bloquants / suggestions / points positifs) aligné sur les règles d'AGENTS.md. Le skill ne merge **jamais** automatiquement et ne fait **jamais** d'`approve` sur GitHub sans validation explicite ; il propose les actions à exécuter (`gh pr review --approve`, etc.) et attend un « ok ».
6. **Mise à jour Linear** — proposer (jamais imposer) le passage du ticket en *In Progress* au début, *In Review* à l'ouverture de la PR, *Done* à la fusion.

### Après le merge : nettoyage automatique

Le repo GitHub a l'option **« Automatically delete head branches »** activée. Conséquences :

- La branche distante (`origin/PLO-<n>-...`) est **supprimée automatiquement** dès qu'une PR est mergée. Aucun `git push origin --delete` à prévoir.
- Côté local, l'agent (ou l'humain) fait simplement `git fetch --prune` pour aligner les refs `origin/*` avec la réalité du remote.
- La branche **locale** mergée peut être supprimée avec `git branch -d PLO-<n>-...` (mode sécurisé qui refuse si elle n'est pas mergée).

## 4. Conventions techniques

- **Python ≥ 3.10** (cf. `README.md` pour Tkinter et la version `python-tk@x.y` correspondante).
- Dépendances déclarées dans `requirements.txt`. Toute nouvelle dépendance doit être justifiée dans le commit/PR.
- Code et UI **en français** (interface, logs utilisateur, rapports).
- Conserver l'API actuelle de `converter.py` (callbacks `on_log` / `on_progress`) pour permettre un futur swap d'UI.
- Build macOS : `./scripts/build_mac_app.sh` ou directement via `ConvertisseurMarkdownIA.spec` (PyInstaller).
- **Ne jamais committer** : `.venv/`, `build/`, `dist/`, `__pycache__/`, archives `.zip`/`.dmg`, `.DS_Store`. Cf. `.gitignore`.
- **Distribution binaire** : via GitHub Releases, pas dans le repo (la limite GitHub est 100 MB par fichier).

## 5. Style de commit et de PR

- Messages de commit : **français**, impératif, ≤ 72 caractères pour la première ligne, corps facultatif pour le *pourquoi*.
- **Un commit = un changement cohérent.** Éviter les commits fourre-tout.
- Les PR contiennent : objectif, lien Linear (`Closes PLO-<n>`), résumé des changements, captures si UI, plan de test.

## 6. Tests et vérifications attendues avant de proposer un commit

- L'app démarre (`python3 main.py`) sans erreur.
- Pas de régression sur une conversion simple (`.docx` ou `.txt` → `.md`).
- Avant un commit touchant le packaging : reconstruction `.app` réussie via `./scripts/build_mac_app.sh`.
- Pour les changements UI : vérification visuelle ; toujours mentionner ce qui a été testé manuellement.

## 7. Quand utiliser quel outil

| Action | Outil |
|---|---|
| Lire, créer, mettre à jour un ticket Linear (issue) | **MCP Linear** (`save_issue`, `get_issue`, `list_issues`) |
| Ajouter un commentaire à un ticket Linear | **MCP Linear** (`save_comment`) |
| Créer un projet, un milestone ou un label Linear | **MCP Linear** (`save_project`, `save_milestone`, `create_issue_label`) |
| Créer une branche, commit local, push | **Shell git** (avec validation) |
| Créer/lire une PR, gérer les Releases | **UI GitHub** ou `gh` CLI quand installé |
| Recherche dans le code | Outils de recherche Cursor |
| Édition de fichiers | Outils d'édition Cursor (jamais via `sed`/`echo`) |

## 8. Capture d'idées et création d'issues à la volée

Pendant une session de travail, si une **amélioration**, un **bug** ou une **idée hors périmètre** émerge, l'agent doit la capturer dans Linear plutôt que de la perdre ou de polluer la tâche en cours.

### Quand proposer la création d'une issue

- L'utilisateur exprime une idée du type : « on devrait aussi… », « tiens, il faudrait que… », « note ça pour plus tard ».
- L'agent identifie un bug ou une dette technique hors du scope du ticket en cours.
- Une décision de design importante est prise en discussion et mérite trace écrite.

### Règle de validation

L'agent **ne crée jamais** une issue silencieusement. Il propose toujours :

1. Un **résumé court** de ce qui va être créé.
2. Le **titre** suggéré.
3. La **description** suggérée (Markdown, en français).
4. Les **métadonnées** (team `PLO`, priorité par défaut **Medium**, labels suggérés s'ils existent, parent éventuel).

Et il attend un **« ok »** explicite avant d'appeler `save_issue`.

### Format attendu

- **Titre** : en français, impératif court (ex. « Ajouter le support des fichiers `.odt` »).
- **Description** : contexte (1-2 phrases) + critères d'acceptation en liste à puces.
- **Labels** : utiliser ceux existants (lister via `list_issue_labels` si besoin) avant d'en créer un nouveau.
- **Lien retour** : si l'idée est née d'une discussion sur une PR ou un ticket, le mentionner dans la description (`Voir PLO-X` ou lien GitHub).

### À éviter

- Créer plusieurs micro-issues là où une seule suffit.
- Créer une issue pour un TODO qui sera résolu dans la même PR (utiliser plutôt un commentaire de code `# TODO` ou résoudre tout de suite).
- Définir une priorité **Urgent / High** sans validation explicite.

## 9. Sécurité et confidentialité

- L'app reste **100 % locale** : ne pas introduire d'appels réseau, télémétrie ou API cloud sans validation explicite et discussion préalable dans un ticket Linear.
- Ne jamais committer de secrets, tokens, ou chemins absolus contenant des données personnelles.

## 10. Évolution du workflow — penser aux hooks Cursor

> **Rappel à se faire de temps en temps** (tous les 2-3 mois ou à chaque palier projet) : passer en revue les frictions répétitives de la session pour évaluer si un **hook Cursor** (`.cursor/hooks.json`) permettrait de les automatiser et de muscler le workflow.

Pistes typiques à considérer au fil de l'avancement :

- **Pre-commit** : vérifier la présence d'un ID `PLO-<n>` dans le message de commit.
- **On-prompt** : injecter automatiquement dans le contexte le ticket Linear en cours (déduit du nom de la branche).
- **Post-push** : poster un commentaire automatique dans le ticket Linear avec le lien du commit ou de la PR.
- **Pre-build** : vérifier la version Python et la présence de `python-tk` avant de lancer PyInstaller.

Ces hooks ne sont **pas obligatoires** au démarrage : ils s'ajoutent quand un même réflexe manuel revient trop souvent.
