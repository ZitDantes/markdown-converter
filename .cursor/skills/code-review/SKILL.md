---
name: code-review
description: Effectue une review structurée d'une Pull Request GitHub alignée sur AGENTS.md (préfixe PLO-X, ruff check, smoke imports, critères d'acceptation Linear). Use when the user asks for "review", "relire la PR", "fais la revue", "code review", or right after the agent opens a PR via `gh pr create`. Restitue un verdict (Approve / Request changes / Comment) sans jamais merger ni approuver sans validation explicite.
---

# Code review d'une Pull Request

Skill propre au projet **Convertisseur Markdown IA**. Aligné sur les règles d'[`AGENTS.md`](../../../AGENTS.md) : §2 (confirmations explicites pour les actions externes), §3 (boucle de travail standard), §5 (style commits et PR).

## Quand l'utiliser

- L'utilisateur demande explicitement une review (« review », « relire la PR », « fais la revue », « code review »).
- L'agent vient d'ouvrir une PR via `gh pr create` et il est pertinent de la relire avant de la transmettre à l'humain.
- L'utilisateur dit « valide cette PR » ou « passe la PR en review ».

## Canaux de review possibles

Deux canaux peuvent recevoir la review, à choisir selon le contexte :

1. **GitHub direct** via `gh pr review <num> --comment|--approve|--request-changes` — toujours disponible. Demander à l'utilisateur quel canal il préfère si non précisé.

2. **Linear Diffs** (si activé sur le workspace, cf. [Linear docs Diffs](https://linear.app/docs/diffs)) — l'utilisateur peut ouvrir le PR dans Linear et faire la review depuis là. Les commentaires et le statut de review se synchronisent automatiquement avec GitHub. **Bonus** : la review apparaît directement à côté du ticket `PLO-<n>` correspondant.

L'agent ne sait pas distinguer si Linear Diffs est activé. **Restitue toujours la review en chat** (format imposé à l'étape 7 ci-dessous), puis **propose** l'action GitHub correspondante. Si l'utilisateur préfère faire la review depuis Linear, il copie/colle simplement la restitution dans le panneau Linear Diffs.

## Règles d'or (AGENTS.md §2)

1. **Jamais de merge automatique**, même si la review est positive.
2. **Jamais d'approve sur GitHub** sans validation explicite de l'utilisateur.
3. **Jamais de changement de statut Linear** au-delà de ce qui est proposé à l'humain.
4. Toute action externe (`gh pr review`, `gh pr merge`, `save_issue state=...`) doit être **proposée** puis attendre un « ok » explicite.

## Workflow

Copie cette checklist et avance pas à pas :

```
- [ ] 1. Identifier la PR (numéro + ticket PLO-X)
- [ ] 2. Récupérer le contexte (PR + ticket Linear)
- [ ] 3. Vérifier la conformité AGENTS.md
- [ ] 4. Vérifier les critères d'acceptation du ticket
- [ ] 5. Lancer les vérifs techniques automatisables
- [ ] 6. Relire le diff de manière critique
- [ ] 7. Restituer le verdict
- [ ] 8. Proposer les actions de suivi
```

### 1. Identifier la PR

Si l'utilisateur n'a pas précisé de numéro :

```bash
gh pr list --state open --json number,title,headRefName
```

Demander confirmation si plusieurs PRs sont ouvertes.

### 2. Récupérer le contexte

```bash
gh pr view <num> --json title,body,headRefName,baseRefName,files,commits,additions,deletions
gh pr diff <num>
```

Si le titre matche `PLO-<n>` : récupérer le ticket Linear via le MCP pour avoir les critères d'acceptation officiels (et les comparer avec ce que la PR livre vraiment).

### 3. Vérifier la conformité AGENTS.md

Cocher chaque ligne et noter les écarts dans la restitution :

| Critère | Source | Attendu |
|---|---|---|
| Titre PR | AGENTS.md §3 | `PLO-<n> — <description>` |
| Body PR | AGENTS.md §3 | Contient `Closes PLO-<n>` |
| Préfixe commits | AGENTS.md §5 | Tous préfixés `PLO-<n>:` |
| Format commits | AGENTS.md §5 | Impératif, français, ≤ 72 caractères pour la première ligne |
| Branche | AGENTS.md §3 | `PLO-<n>-<slug-kebab>` |
| Atomicité | AGENTS.md §5 | Un commit = un changement cohérent |

### 4. Vérifier les critères d'acceptation du ticket

Reprendre la liste à cocher du ticket Linear et confirmer une à une, en référençant le fichier/le diff qui valide chaque point. Lister à part les critères **non vérifiables automatiquement** (smoke test UI manuel, build PyInstaller…) pour qu'ils soient confirmés par l'humain.

### 5. Vérifs techniques automatisables

Depuis la branche reviewée (`gh pr checkout <num>` puis revenir sur sa branche initiale après) :

```bash
source .venv/bin/activate
ruff check .                                            # doit être clean
ruff format --check .                                   # doit être clean
python3 -c "import main, ui, converter, utils, report"  # smoke import
```

Tout `# noqa` ajouté par la PR doit être justifié (commentaire dans le code ou ticket de suivi). Idem pour toute nouvelle dépendance ajoutée à `requirements.txt` ou `requirements-dev.txt`.

### 6. Relire le diff de manière critique

Points d'attention obligatoires sur ce projet :

- [ ] Aucun secret, token, ou chemin absolu personnel (`/Users/<nom>/...`) committé.
- [ ] Aucune dépendance ajoutée sans justification dans le body de la PR (AGENTS.md §4).
- [ ] Aucun appel réseau ni télémétrie introduit (AGENTS.md §9, l'app est 100 % locale).
- [ ] Aucun fichier `build/`, `dist/`, `.venv/`, `__pycache__/`, `.DS_Store`, `.zip`, `.dmg` committé.
- [ ] Si UI modifiée : capture ou description du test manuel.
- [ ] Si packaging modifié : mention de la reconstruction `.app` réussie.
- [ ] Commentaires de code : utiles uniquement, pas de narration ligne à ligne.
- [ ] Aucune régression évidente sur l'API publique de `converter.py` (callbacks `on_log` / `on_progress`).
- [ ] Code et UI restent **en français** (interface, logs utilisateur, rapports).

### 7. Restituer le verdict

Utiliser **exactement** ce format de sortie en français :

```markdown
## Review de la PR #<num> — PLO-<n>

### 🔴 Bloquants
- _(rien si vide)_

### 🟡 Suggestions
- ...

### 🟢 Points positifs
- ...

### Couverture des critères d'acceptation
- [x] Critère 1 — vérifié via `<fichier>:<ligne>` ou `<commande>`
- [ ] Critère 2 — **à valider manuellement** par l'humain

### Verdict
**Approve** | **Request changes** | **Comment**
```

### 8. Proposer les actions de suivi

Selon le verdict, proposer (et attendre un « ok » explicite avant exécution) :

- **Approve**
  - `gh pr review <num> --approve --body "<résumé en 1 ligne>"`
  - Le merge reste à la main de l'humain (jamais `gh pr merge` automatique).
- **Request changes**
  - `gh pr review <num> --request-changes --body "<résumé des bloquants>"`
  - Ne pas modifier le statut Linear : il reste *In Review* tant que l'auteur n'a pas répondu.
- **Comment**
  - `gh pr review <num> --comment --body "<remarques>"`

## Anti-patterns

- ❌ Annoncer « PR approuvée » dans le chat sans avoir lancé la checklist.
- ❌ Exécuter `gh pr review --approve` sans validation utilisateur.
- ❌ Restituer en anglais ou sans le format de la section 7.
- ❌ Ignorer les critères d'acceptation Linear même quand le diff paraît propre.
- ❌ Mélanger plusieurs verdicts (« Approve avec des request changes »).

## Quand ce skill ne s'applique pas

- Review d'un commit isolé hors PR → workflow ad hoc, pas ce skill.
- Audit post-merge → ce skill cible le **pre-merge** ; après fusion c'est de l'audit, hors scope.
- Review d'une PR sur un autre repo que `ZitDantes/markdown-converter` → adapter manuellement (la checklist AGENTS.md ne s'y applique pas telle quelle).

## Référence

- [`AGENTS.md`](../../../AGENTS.md) à la racine du repo — règles d'orchestration et conventions complètes.
