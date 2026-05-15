# Bienvenue

**Markdown Converter** transforme vos documents bureautiques (Word, PDF, PowerPoint, Excel, HTML, texte…) en fichiers **Markdown** (`.md`), prêts à être indexés pour un **RAG** ou utilisés comme **contexte** dans un outil d’IA.

## Ce que fait l’application

- Conversion **par lot** : plusieurs fichiers ou dossiers entiers.
- Un fichier `.md` par document source, dans le dossier de sortie que vous choisissez.
- Rapport de fin de lot (`rapport_conversion.md`) et journal détaillé.
- Interface graphique en **français** (recommandée : **PySide6**, voir [Installation](02-installation.md)).

## Ce que l’application ne fait pas

- Elle **n’envoie aucune donnée** sur Internet : tout reste sur votre machine.
- Ce n’est pas un éditeur Markdown avancé : l’objectif est un texte **exploitable** par un LLM, pas une mise en page pixel-perfect.
- Les PDF scannés sans texte intégré donnent souvent un résultat vide ou médiocre (OCR non inclus dans cette version).

## Public visé

Utilisateurs qui travaillent avec des **LLM** et veulent importer des documents **par glisser-déposer**, sans ligne de commande — y compris des profils peu techniques.

[Suite : Installation →](02-installation.md)
