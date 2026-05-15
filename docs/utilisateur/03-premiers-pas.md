# Premiers pas

## 1. Ouvrir l’application

Lancez **Markdown Converter** (`.app` ou `MARKDOWN_CONVERTER_UI=qt python3 main.py`).

## 2. Choisir le dossier de sortie

Dans le bandeau **Dossier de sortie**, indiquez où seront créés les fichiers `.md`. Utilisez **Choisir** pour parcourir le disque. Le chemin est **mémorisé** entre les sessions.

## 3. Ajouter des documents

- **Fichiers** : un ou plusieurs documents (`.docx`, `.pdf`, `.pptx`, `.xlsx`, `.html`, `.txt`, …).
- **Dossier** : parcours récursif ; seuls les formats pris en charge sont ajoutés.
- **Glisser-déposer** : déposez fichiers ou dossiers sur la zone de la file (surbrillance au survol).

Pour retirer toute la liste avant un nouveau lot : **Vider**.

## 4. Lancer la conversion

1. Vérifiez la file et le dossier de sortie.
2. Choisissez le mode **Standard (recommandé)** ou **Strict** (voir [Interface](04-interface.md)).
3. Cliquez sur **Convertir**.

La progression s’affiche par fichier et pour l’ensemble du lot. Le journal (tiroir en bas) détaille les messages.

## 5. Récupérer les résultats

- Fichiers `.md` dans le dossier de sortie (noms dérivés des sources ; suffixes `_2`, `_3` en cas de doublon).
- **`rapport_conversion.md`** : bilan du lot (succès, avertissements, erreurs).
- **Inspecteur** (panneau de droite) : aperçu du Markdown pour la ligne sélectionnée.

## Statuts utiles

| Affichage | Signification |
|-----------|----------------|
| OK | Conversion réussie |
| À relire | Réussi, mais le format demande une relecture (ex. PDF, PPTX) |
| Erreur | Échec pour ce fichier |
| En cours / En attente | Lot en cours ou file en attente |

[← Installation](02-installation.md) · [Interface →](04-interface.md)
