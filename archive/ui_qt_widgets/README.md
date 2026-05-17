# Archive — UI Qt widgets (PLO-56)

Interface **PySide6 widgets** remplacée par l’UI web (`ui_web_shell.py`, `web/`).

Conservé à titre historique ; **non importé** par `main.py` ni le bundle release.

## Modules archivés

- `ui_qt.py` — fenêtre principale widgets
- `ui_qt_journal.py`, `ui_qt_inspector.py`, `ui_qt_theme.py`, `ui_qt_settings.py`
- `ui_qt_file_proxy.py`, `ui_qt_file_drop_table.py`

## Code encore actif à la racine du repo

Logique partagée avec l’UI web :

- `ui_qt_file_model.py`, `ui_qt_conversion_worker.py`
- `ui_qt_inspector_data.py`, `ui_qt_inspector_rename.py`
- `conversion_queue.py`, `conversion_mime_paths.py`

Lancement : `MARKDOWN_CONVERTER_UI=web` (défaut dans le `.app`) ou `tk` en secours.
