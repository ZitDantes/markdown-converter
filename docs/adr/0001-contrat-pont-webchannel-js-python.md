# ADR 0001 — Contrat pont JavaScript ↔ Python (QWebChannel)

- **Statut** : Accepté
- **Date** : 2026-05-16
- **Tickets** : PLO-45 (cette ADR), epic PLO-43, spike PLO-44
- **Références** : `spike/webengine/`, `converter.py`, `ui_qt_conversion_worker.py`, PLO-33 (surface produit), PLO-40 (modes Standard / Strict)

## Contexte

L’application migre vers une **UI web locale** (Vite / React / TypeScript) embarquée dans **PySide6 + Qt WebEngine**. Le front communique avec le Python existant via **QWebChannel**, sans serveur HTTP ni API cloud.

Le spike **PLO-44** a validé :

- chargement local `file:` (dev) et `qrc:` (release) ;
- pont minimal `ping` / signaux ;
- appels `@Slot` avec **retour asynchrone** côté JS (Promises Qt 6) — voir `qtInvoke` dans `spike/webengine/static_file/app.js`.

L’UI Qt actuelle (`ui_qt*.py`) orchestre déjà `convert_files` dans un **worker thread** et relaie logs / progression vers le GUI via un **sink Qt** (`_WorkerUISink`). Le pont web doit reproduire cette discipline.

## Décision

### 1. Transport : QWebChannel, objet unique `backend`

- Un seul objet exposé : **`backend`** (classe Python `WebBackend`, nom d’enregistrement fixe).
- **Commandes** (UI → Python) : méthodes `@Slot` sur `backend`.
- **Événements** (Python → UI) : `Signal` Qt connectés côté JS via `backend.<signal>.connect(...)`.
- Script fourni par Qt : `qrc:///qtwebchannel/qwebchannel.js` (aucun CDN).

### 2. Payloads structurés : JSON UTF-8 dans des `str`

QWebChannel sérialise mal les graphes d’objets imbriqués. Les structures métier passent en **chaîne JSON** (schéma **v0** dans `bridge_contract/` et `web/shared/bridge-contract.ts`).

Convention :

- suffixe des paramètres / retours : `*Json` quand le contenu est JSON ;
- version du contrat : champ `"schemaVersion": "0"` dans chaque message racine.

### 3. Appels JS : toujours traiter les retours comme Promises

Sous Qt 6, les `@Slot` avec `result=` renvoient souvent une **Promise** côté JavaScript. Le front **doit** utiliser un helper du type `qtInvoke(() => backend.method(...))` (cf. spike PLO-44), jamais une concaténation directe du retour.

### 4. Threading (non négociable)

| Zone | Thread | Règle |
|------|--------|--------|
| `QWebEngineView`, `backend`, slots appelés depuis JS | **GUI (main)** | Léger : validation, lancement worker, émission signaux |
| `convert_files`, I/O, moteurs | **Worker `QThread`** | Seul endroit autorisé pour la conversion |
| Relais worker → UI | **Signaux Qt** | `QueuedConnection` vers le thread GUI ; le worker **ne touche jamais** le DOM ni `backend` depuis son thread |

Équivalent web du `_WorkerUISink` actuel : le worker émet vers un adaptateur GUI qui sérialise en JSON et émet les `Signal` du `backend`.

**Interdit** : appeler `convert_files` depuis un slot JS directement sur le thread GUI.

### 5. Surface produit (PLO-33)

- Libellés de statut affichés : **`statusLabel`** fourni par Python via `conversion_status_label_fr` — le front **n’invente pas** de libellés à partir de codes moteur.
- **Pas** de noms de moteurs (MarkItDown, Pandoc) dans les libellés principaux de la file ou du footer.
- Le mode **Standard / Strict** (PLO-40) est transmis comme `useConversionFallback: boolean` dans `StartConversionCommand` (`true` = Standard, `false` = Strict).

### 6. Sécurité et périmètre local

- **Aucune** exécution arbitraire (pas d’`eval`, pas de `Function`, pas de pont générique type `runPython(code)`).
- Liste **fermée** de commandes (voir § Contrat v0).
- Chemins fichiers : normalisés côté Python ; le JS ne peut déclencher la conversion que sur des entrées validées (file picker natif ou chemins déjà acceptés dans la file).
- **100 % local** : pas de fetch réseau obligatoire au runtime.

## Contrat v0 — commandes (JS → Python)

| Méthode | Paramètres | Retour (`str`, JSON sauf ping) | Description |
|---------|------------|--------------------------------|-------------|
| `ping` | `message: str` | `str` (texte) | Santé du pont (spike / tests) |
| `pickFiles` | — | `PickFilesResult` | Ouvre un sélecteur natif multi-fichiers |
| `pickFolder` | — | `PickFolderResult` | Ouvre un sélecteur de dossier (ajout récursif côté Python) |
| `setOutputDir` | `path: str` | `SetOutputDirResult` | Définit le dossier de sortie (validation) |
| `getQueueState` | — | `QueueState` | Snapshot de la file |
| `clearQueue` | — | `ClearQueueResult` | Vide la file (confirmation côté UI avant appel) |
| `startConversion` | `commandJson: str` | `AckResult` | Lance le worker (`StartConversionCommand`) |
| `cancelConversion` | — | `AckResult` | Réservé v0 — peut renvoyer `ok: false` tant que non implémenté |

## Contrat v0 — événements (Python → JS)

| Signal | Payload | Description |
|--------|---------|-------------|
| `logEmitted` | `level: str`, `message: str` | Entrée de journal (`INFO`, `WARNING`, `ERROR`, …) |
| `progressUpdated` | `progressJson: str` | `ProgressEvent` (lot + fichier courant) |
| `queueUpdated` | `queueJson: str` | `QueueState` complet ou delta futur — v0 : snapshot complet |
| `conversionFinished` | `summaryJson: str` | `ConversionFinishedEvent` |
| `conversionFailed` | `message: str` | Erreur fatale du worker (texte français) |

## Modèle de données v0 (résumé)

Types détaillés : `bridge_contract/models.py`, `web/shared/bridge-contract.ts`.

- **`FileQueueItem`** : `sourcePath`, `status` (`ConversionStatus`), `statusLabel`, `progressPercent`, champs optionnels (`outputPath`, `message`, …).
- **`QueueState`** : `items[]`, `outputDir`, `canStartConversion`.
- **`ProgressEvent`** : `fileIndex`, `fileTotal`, `fileLabel`, `batchPercent` (0–1).
- **`ConversionFinishedEvent`** : `summary` (`ConversionSummaryDto`), horodatages ISO 8601.

Les enums de statut reprennent les valeurs string de `ConversionStatus` dans `converter.py`.

## Conséquences

### Positives

- Contrat stable pour PLO-46 (socle `web/`) et les vagues de parité UI.
- Tests Python possibles sur la (dé)sérialisation sans WebEngine.
- Alignement explicite avec l’architecture Qt éprouvée (worker + signaux).

### Négatives / coûts

- Verbeux : JSON dans des `str` (copie mémoire sur gros lots — optimisations possibles en v1 par delta / pagination).
- Duplication TypeScript / Python à maintenir (mitigée par schéma documenté et tests miroir).

## Pistes v1 (hors scope PLO-45)

- Deltas `queueUpdated` au lieu de snapshots complets.
- `cancelConversion` effectif.
- Typage généré depuis un seul fichier JSON Schema.

## Validation

- [x] ADR versionnée (`docs/adr/0001-…`)
- [x] Schéma v0 : `bridge_contract/models.py` + `web/shared/bridge-contract.ts`
- [x] Règle threading documentée (§4)
- [x] Alignement PLO-33 (§5)
- [x] Tests unitaires sérialisation : `tests/unit/test_bridge_contract.py`
