# Interface (UI Qt)

L’interface v0.2 est organisée en zones fixes (de haut en bas) :

```
Titlebar  →  titre, indicateur secours, thème clair/sombre
Toolbar   →  Fichiers, Dossier, Vider, filtres, recherche
Bandeau   →  dossier de sortie
File      →  une ligne par fichier (statut, progression)
Inspecteur→  Aperçu / Sortie / Détails (fichier sélectionné)
Footer    →  progression globale, ETA, Convertir, Rapport
Journal   →  tiroir repliable (logs)
```

Captures de référence : [`design_handoff_ui_refonte/screenshots/`](../../design_handoff_ui_refonte/screenshots/).

## File de conversion

- **Tri** par colonnes, **filtres** par extension (puces avec compteurs), **recherche** texte.
- **Progression** par ligne pendant le lot.
- **Sélection** d’une ligne pour alimenter l’inspecteur.

## Inspecteur

| Onglet | Contenu |
|--------|---------|
| **Aperçu** | Markdown produit (front-matter YAML + corps) |
| **Sortie** | Chemin du `.md`, actions utiles |
| **Détails** | Statut, taille, durée, message d’erreur ou d’avertissement |

## Journal

- Repliable, **caché par défaut**.
- Filtres **Tout / Info / Avertissement / Erreur**.
- Lien pour **ouvrir le fichier de log** persistant (`run.log`).

## Thème

Boutons **Clair** / **Sombre** dans la barre de titre. La préférence est enregistrée localement (`settings.json`).

## Modes Standard et Strict

| Mode | Comportement |
|------|----------------|
| **Standard (recommandé)** | En cas d’échec de la conversion principale, une **voie de secours** peut être tentée si elle est disponible sur votre machine. |
| **Strict** | Aucun secours : seule la conversion principale compte ; utile pour un résultat prévisible. |

L’interface n’affiche **pas** de noms de bibliothèques ou de moteurs techniques en libellés principaux : vous choisissez une **intention** (Standard / Strict). Une pastille indique si le **secours** (ex. binaire Pandoc) est détecté.

## Session

Au redémarrage, la **liste des chemins sources** (jusqu’à 100) et le **dossier de sortie** peuvent être restaurés. Les fichiers supprimés ou formats non supportés sont ignorés silencieusement.

[← Premiers pas](03-premiers-pas.md) · [Formats et qualité →](05-formats-et-qualite.md)
