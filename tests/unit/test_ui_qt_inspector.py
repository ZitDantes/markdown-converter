"""Tests offscreen du panneau inspecteur Qt (PLO-38)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


@pytest.fixture
def qt_app() -> object:
    pytest.importorskip("PySide6", reason="PySide6 non installé localement")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(sys.argv)


def _build_md(title: str = "Mon titre", warning: str | None = None) -> str:
    from utils import yaml_scalar_double_quoted

    lines = [
        "---",
        f"titre: {yaml_scalar_double_quoted(title)}",
        'fichier_source: "/tmp/source.docx"',
        'date_conversion: "2026-05-14 01:00:00"',
    ]
    if warning:
        lines.append(f"avertissement: {yaml_scalar_double_quoted(warning)}")
    lines.append("---")
    return "\n".join(lines) + f"\n\n# {title}\n\nContenu du document.\n"


def _make_record(tmp_path: Path, **kwargs: object):  # type: ignore[no-untyped-def]
    from converter import ConversionStatus, FileConversionRecord

    src = tmp_path / kwargs.pop("source_name", "source.docx")
    src.write_bytes(b"x")
    status = kwargs.pop("status", ConversionStatus.SUCCESS)
    return FileConversionRecord(source_path=src, status=status, **kwargs)


def test_panel_has_three_tabs(qt_app: object) -> None:
    from PySide6.QtWidgets import QTabWidget

    from ui_qt_inspector import MarkdownInspectorPanel

    panel = MarkdownInspectorPanel()
    assert panel.objectName() == "inspector"
    tabs = panel.findChild(QTabWidget, "inspector_tabs")
    assert tabs is not None
    assert tabs.count() == 3
    assert [tabs.tabText(i) for i in range(3)] == ["Aperçu", "Sortie", "Détails"]


def test_set_record_none_shows_invitation(qt_app: object) -> None:
    from PySide6.QtWidgets import QLabel

    from ui_qt_inspector import MarkdownInspectorPanel

    panel = MarkdownInspectorPanel()
    panel.set_record(None)
    msg = panel.findChild(QLabel, "inspector_preview_message")
    assert msg is not None
    assert "Sélectionnez" in msg.text()


def test_set_record_success_with_in_memory_text(qt_app: object, tmp_path: Path) -> None:
    from PySide6.QtWidgets import QLabel, QTextEdit

    from ui_qt_inspector import MarkdownInspectorPanel

    md = _build_md(title="Rapport hebdo")
    rec = _make_record(tmp_path, output_md_text=md, output_path=tmp_path / "out.md")
    panel = MarkdownInspectorPanel()
    panel.set_record(rec)

    msg = panel.findChild(QLabel, "inspector_preview_message")
    assert msg is not None and msg.isHidden() is True

    yaml_view = panel.findChild(QTextEdit, "inspector_preview_yaml")
    assert yaml_view is not None and yaml_view.isHidden() is False
    # Le HTML inséré contient bien la clé titre + sa valeur.
    yaml_html = yaml_view.toHtml()
    assert "titre" in yaml_html
    assert "Rapport hebdo" in yaml_html

    body = panel.findChild(QTextEdit, "inspector_preview_body")
    assert body is not None
    assert "# Rapport hebdo" in body.toPlainText()
    assert "Contenu du document." in body.toPlainText()


def test_set_record_success_reads_from_disk_when_text_missing(
    qt_app: object, tmp_path: Path
) -> None:
    from PySide6.QtWidgets import QTextEdit

    from ui_qt_inspector import MarkdownInspectorPanel

    md_file = tmp_path / "doc.md"
    md_file.write_text(_build_md(title="Sur disque"), encoding="utf-8")
    rec = _make_record(tmp_path, output_path=md_file)
    panel = MarkdownInspectorPanel()
    panel.set_record(rec)
    body = panel.findChild(QTextEdit, "inspector_preview_body")
    assert body is not None
    assert "# Sur disque" in body.toPlainText()


def test_set_record_with_avertissement_shows_warning_banner(qt_app: object, tmp_path: Path) -> None:
    from PySide6.QtWidgets import QLabel

    from converter import ConversionStatus
    from ui_qt_inspector import MarkdownInspectorPanel

    md = _build_md(title="Doc PDF", warning="Relecture recommandée : conversion approximative.")
    rec = _make_record(
        tmp_path,
        status=ConversionStatus.SUCCESS_REVIEW,
        output_md_text=md,
        output_path=tmp_path / "x.md",
    )
    panel = MarkdownInspectorPanel()
    panel.set_record(rec)
    warning = panel.findChild(QLabel, "inspector_preview_warning")
    assert warning is not None
    assert warning.isHidden() is False
    assert "Relecture recommandée" in warning.text()


def test_set_record_error_shows_message(qt_app: object, tmp_path: Path) -> None:
    from PySide6.QtWidgets import QLabel, QTextEdit

    from converter import ConversionStatus
    from ui_qt_inspector import MarkdownInspectorPanel

    rec = _make_record(
        tmp_path,
        status=ConversionStatus.ERROR,
        message="Le moteur a échoué : fichier corrompu.",
    )
    panel = MarkdownInspectorPanel()
    panel.set_record(rec)
    msg = panel.findChild(QLabel, "inspector_preview_message")
    assert msg is not None
    assert "moteur a échoué" in msg.text()
    body = panel.findChild(QTextEdit, "inspector_preview_body")
    assert body is not None
    assert body.toPlainText() == ""


def test_set_record_success_without_output_falls_back_to_message(
    qt_app: object, tmp_path: Path
) -> None:
    from PySide6.QtWidgets import QLabel

    from ui_qt_inspector import MarkdownInspectorPanel

    rec = _make_record(tmp_path, output_md_text=None, output_path=None)
    panel = MarkdownInspectorPanel()
    panel.set_record(rec)
    msg = panel.findChild(QLabel, "inspector_preview_message")
    assert msg is not None
    assert "introuvable" in msg.text().lower() or "illisible" in msg.text().lower()


def test_output_tab_shows_resolved_path_and_enables_buttons(qt_app: object, tmp_path: Path) -> None:
    from PySide6.QtWidgets import QLineEdit, QPushButton

    from ui_qt_inspector import MarkdownInspectorPanel

    out = tmp_path / "sous" / "sortie.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("# x", encoding="utf-8")
    rec = _make_record(tmp_path, output_path=out)
    panel = MarkdownInspectorPanel()
    panel.set_record(rec)

    path_edit = panel.findChild(QLineEdit, "inspector_output_path")
    assert path_edit is not None
    assert str(out.resolve()) == path_edit.text()

    copy_btn = panel.findChild(QPushButton, "inspector_output_copy")
    open_btn = panel.findChild(QPushButton, "inspector_output_open_folder")
    assert copy_btn is not None and open_btn is not None
    assert copy_btn.isEnabled() is True
    assert open_btn.isEnabled() is True


def test_output_copy_puts_absolute_path_on_clipboard(qt_app: object, tmp_path: Path) -> None:
    from PySide6.QtWidgets import QApplication, QPushButton

    from ui_qt_inspector import MarkdownInspectorPanel

    out = tmp_path / "out.md"
    out.write_text("# x", encoding="utf-8")
    rec = _make_record(tmp_path, output_path=out)
    panel = MarkdownInspectorPanel()
    panel.set_record(rec)

    copy_btn = panel.findChild(QPushButton, "inspector_output_copy")
    assert copy_btn is not None
    copy_btn.click()
    clip = QApplication.clipboard()
    assert clip is not None
    assert clip.text() == str(out.resolve())


def test_output_open_folder_invokes_desktop_services(
    qt_app: object, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import QPushButton

    from ui_qt_inspector import MarkdownInspectorPanel

    opened: list[QUrl] = []

    def fake_open(url: QUrl) -> bool:
        opened.append(url)
        return True

    monkeypatch.setattr(QDesktopServices, "openUrl", fake_open)

    out = tmp_path / "d" / "f.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("# x", encoding="utf-8")
    rec = _make_record(tmp_path, output_path=out)
    panel = MarkdownInspectorPanel()
    panel.set_record(rec)

    open_btn = panel.findChild(QPushButton, "inspector_output_open_folder")
    assert open_btn is not None
    open_btn.click()

    assert len(opened) == 1
    assert opened[0].toLocalFile() == str(out.parent.resolve())


def test_output_tab_no_path_when_error_without_output(qt_app: object, tmp_path: Path) -> None:
    from PySide6.QtWidgets import QLineEdit, QPushButton

    from converter import ConversionStatus
    from ui_qt_inspector import MarkdownInspectorPanel

    rec = _make_record(tmp_path, status=ConversionStatus.ERROR, message="Échec.", output_path=None)
    panel = MarkdownInspectorPanel()
    panel.set_record(rec)

    path_edit = panel.findChild(QLineEdit, "inspector_output_path")
    assert path_edit is not None
    assert path_edit.text() == ""

    copy_btn = panel.findChild(QPushButton, "inspector_output_copy")
    open_btn = panel.findChild(QPushButton, "inspector_output_open_folder")
    assert copy_btn is not None and open_btn is not None
    assert copy_btn.isEnabled() is False
    assert open_btn.isEnabled() is False


def test_inspector_wired_to_file_selection(qt_app: object, tmp_path: Path) -> None:
    from PySide6.QtCore import QItemSelectionModel

    from ui_qt import MarkdownConverterQtApp, add_paths_to_model

    app = MarkdownConverterQtApp()
    app.build()
    assert app.file_view_parts is not None
    assert app.inspector_panel is not None

    src = tmp_path / "doc.docx"
    src.write_bytes(b"x")
    add_paths_to_model(app.file_view_parts.model, [src])

    proxy = app.file_view_parts.proxy
    table = app.file_view_parts.table
    selection_model = table.selectionModel()
    assert selection_model is not None
    selection_model.setCurrentIndex(
        proxy.index(0, 0),
        QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows,
    )
    current = app.inspector_panel.current_record()
    assert current is not None
    assert current.source_path.name == "doc.docx"
