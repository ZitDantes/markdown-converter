# Confidentialité et traitement local

## Principe

**Markdown Converter** est conçu pour un usage **100 % local** :

- Aucune télémétrie intégrée.
- Aucun envoi de vos fichiers vers un service cloud.
- Aucune clé API requise pour convertir.

Les conversions lisent et écrivent **uniquement** sur votre disque (fichiers sources, dossier de sortie, logs locaux).

## Données stockées sur la machine

| Donnée | Emplacement typique |
|--------|---------------------|
| Fichiers `.md` produits | Dossier de sortie que **vous** choisissez |
| Logs | `~/Library/Logs/MarkdownConverter/` (macOS) ou `~/.markdown-converter/logs/` |
| Préférences UI (thème, file, sortie) | `~/Library/Application Support/Markdown Converter/settings.json` (macOS) |

Vous pouvez supprimer ces dossiers à tout moment.

## Réseau

L’application **ne nécessite pas** Internet pour convertir. Une connexion peut être utilisée par votre système pour d’autres raisons (mises à jour OS, etc.) ; le produit n’y recourt pas pour la conversion.

## Open source

Le code est public sous **licence MIT** : vous pouvez l’auditer sur [GitHub](https://github.com/ZitDantes/markdown-converter).

[← Dépannage](06-depannage.md) · [Index documentation](../README.md)
