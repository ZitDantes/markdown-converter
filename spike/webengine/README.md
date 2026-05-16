# Spike PLO-44 — PySide6 WebEngine + QWebChannel

Valide le chargement d’une UI web **locale** dans `QWebEngineView` et un échange minimal Python ↔ JavaScript via `QWebChannel`. **Aucun appel réseau** n’est requis au runtime.

## Lancer le PoC

Prérequis :

```bash
pip install -r requirements.txt -r requirements-qt.txt
```

### Mode `file:` (défaut — proche du futur flux Vite `dist/`)

```bash
MARKDOWN_CONVERTER_UI=web-spike python3 main.py
```

Fond de page **bleu clair**. Cliquer **Ping Python** : la zone de log doit afficher `pong:…`.

### Mode `qrc:` (ressources embarquées)

```bash
MARKDOWN_CONVERTER_SPIKE_LOADER=qrc MARKDOWN_CONVERTER_UI=web-spike python3 main.py
```

Fond **crème**. Même test de ping.

### Mesures de démarrage (console)

```bash
MARKDOWN_CONVERTER_SPIKE_BENCHMARK=1 MARKDOWN_CONVERTER_UI=web-spike python3 main.py
```

Affiche `show_window_ms` et `load_ms` après `loadFinished`.

## Régénérer les ressources Qt

Après modification de `static_qrc/` ou `resources.qrc` :

```bash
pyside6-rcc spike/webengine/resources.qrc -o spike/webengine/resources_rc.py
```

## Décision `file:` vs `qrc:`

| Critère | `file:` (`QUrl.fromLocalFile`) | `qrc:` (ressources Qt) |
|--------|--------------------------------|-------------------------|
| **Développement** | Idéal : servir le build Vite depuis `web/dist/` sans recompiler | Rebuild `pyside6-rcc` à chaque changement front |
| **PyInstaller / .app** | Chemins relatifs au bundle, permissions WebEngine, risque de fuite de chemins disque | Assets dans le binaire, chemins stables |
| **Sécurité / offline** | Réglages `LocalContentCanAccessFileUrls` requis ; pas d’URL distante activée ici | Pas de dépendance au FS utilisateur pour l’UI |
| **QWebChannel** | `qrc:///qtwebchannel/qwebchannel.js` (fourni par Qt) fonctionne avec une page `file:` | Identique |

**Recommandation pour la suite (PLO-46+)** :

- **Dev** : charger `file://` vers `web/dist/index.html` après `npm run build`.
- **Release** : embarquer `dist/` via **qrc** ou **datas PyInstaller** + URL locale ; garder le pont `QWebChannel` inchangé.

Le spike prouve que **les deux modes** chargent HTML, CSS, JS et le pont.

## Taille du bundle (ordre de grandeur)

Mesure locale indicative (macOS, venv, PySide6 6.11) :

```bash
du -sh .venv/lib/python*/site-packages/PySide6/Qt/lib/QtWebEngine*.framework
du -sh .venv/lib/python*/site-packages/PySide6/Qt/lib/QtWebEngineCore.framework
```

Sur une machine de référence (macOS, PySide6 6.11), **QtWebEngineCore.framework** seul fait environ **588 Mo** dans le venv ; les modules satellites (`QtWebEngineWidgets`, etc.) ajoutent quelques Mo. L’UI widgets actuelle **exclut** WebEngine du `.app` v0.2 (`MarkdownConverter.spec`) pour limiter le ZIP (~316 Mo avec MarkItDown/magika). L’intégration WebEngine en release sera traitée sous **PLO-53**.

Comparaison v0.2 sans WebEngine : voir notes de release GitHub.

## Dépendances Linux (packaging / CI)

Déjà installées en CI (Ubuntu, job Python 3.12 + PySide6) :

- `libegl1`, `libxkbcommon0`, `libfontconfig1`, `libdbus-1-3`

Paquets souvent requis pour **Qt WebEngine** sur Debian/Ubuntu (à valider sur la distro cible avant PLO-53) :

- `libnss3`, `libnspr4`
- `libatk1.0-0`, `libatk-bridge2.0-0`
- `libcups2`, `libdrm2`, `libgbm1`
- `libxcomposite1`, `libxdamage1`, `libxfixes3`, `libxrandr2`
- `libpango-1.0-0`, `libcairo2`, `libasound2`

Commande type (spike manuel sur Ubuntu) :

```bash
sudo apt-get install -y libegl1 libxkbcommon0 libfontconfig1 libdbus-1-3 \
  libnss3 libnspr4 libatk-bridge2.0-0 libcups2 libdrm2 libgbm1 \
  libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libpango-1.0-0 libcairo2 libasound2
```

## Fichiers du spike

| Fichier | Rôle |
|---------|------|
| `bridge.py` | Objet `SpikeBridge` exposé en JS (`ping`, `loaderLabel`) |
| `app.py` | Fenêtre `QWebEngineView` + enregistrement `QWebChannel` |
| `loaders.py` | Résolution URL `file:` / `qrc:` |
| `static_file/` | Assets mode disque |
| `static_qrc/` | Copie embarquée dans `resources.qrc` |
| `resources_rc.py` | Module généré par `pyside6-rcc` |

## Suite (PLO-45+)

Contrat pont JS ↔ Python : [ADR 0001](../../docs/adr/0001-contrat-pont-webchannel-js-python.md), types `web/shared/bridge-contract.ts` et `bridge_contract/`.

## Critères d’acceptation PLO-44

- [x] PoC documenté avec instructions de repro
- [x] Décision `file:` vs `qrc:` argumentée
- [x] Aucun appel réseau obligatoire
- [x] Liste des paquets/libs Linux notée

Capture d’écran : exécuter le PoC en mode `file:` et `qrc:`, comparer les fonds et le ping (à joindre à la PR si souhaité).
