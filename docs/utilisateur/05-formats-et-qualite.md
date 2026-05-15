# Formats et qualité

## Extensions prises en charge

`.docx`, `.pptx`, `.pdf`, `.xlsx`, `.html`, `.htm`, `.txt`

Les autres extensions ajoutées à la file apparaissent comme **non supportées** dans le rapport.

## Qualité attendue

La conversion vise un texte **utile pour un LLM**, pas une copie fidèle du document source.

| Priorité | Format | Commentaire |
|----------|--------|-------------|
| Élevée | `.docx`, `.html`, `.txt` | Structure de titres en général bien conservée |
| Moyenne | `.xlsx` | Feuilles simples ; formules et graphiques perdus |
| À relire | `.pdf`, `.pptx` | Ordre des blocs, tableaux et visuels approximatifs |

## Bonnes pratiques avant conversion

- **Word** : utiliser les styles Titre 1, Titre 2… plutôt que du gras manuel.
- **PDF** : préférer un PDF « texte » ; les scans sans OCR donnent souvent du vide.
- **Excel** : une feuille claire par sujet, en-têtes explicites.
- **PowerPoint** : texte dans les zones titre et contenu standard.
- Éviter fichiers **protégés par mot de passe**.

## Rapport et avertissements

Le front-matter YAML des `.md` peut contenir un champ **avertissement** (ex. pour PDF/PPTX). L’inspecteur et le rapport rappellent les fichiers **à relire**.

[← Interface](04-interface.md) · [Dépannage →](06-depannage.md)
