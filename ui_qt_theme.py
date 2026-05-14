"""
Thèmes clair / sombre pour l'UI Qt (PLO-28).

Style ``Fusion`` + ``QPalette`` pour un rendu prévisible sur macOS, Windows et
Linux. Les couleurs d'avertissement / erreur du journal restent alignées sur
``ui.LEVEL_COLOR`` (déjà utilisées dans ``ui_qt_journal``).
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


def apply_qt_theme(app: QApplication, window: QMainWindow, theme: str) -> None:
    """Applique le thème à toute l'application (palette globale + correctifs ciblés)."""
    if theme not in ("light", "dark"):
        theme = "light"
    app.setStyle("Fusion")
    app.setPalette(_palette_for_theme(theme))
    _sync_auxiliary_styles(window, theme)


def _palette_for_theme(theme: str) -> QPalette:
    p = QPalette()
    c = QPalette.ColorRole
    if theme == "light":
        window = QColor("#f6f7f9")
        win_text = QColor("#1c1f26")
        base = QColor("#ffffff")
        alt = QColor("#eef1f6")
        btn = QColor("#e4e7ed")
        btn_text = QColor("#1c1f26")
        highlight = QColor("#0a7aff")
        disabled_text = QColor("#8891a6")
        tip_base = QColor("#ffffe1")
        tip_text = QColor("#1c1f26")
        mid = QColor("#d1d5db")
    else:
        window = QColor("#1c1f26")
        win_text = QColor("#e8eaed")
        base = QColor("#2a2f38")
        alt = QColor("#323842")
        btn = QColor("#3b4250")
        btn_text = QColor("#e8eaed")
        highlight = QColor("#0a7aff")
        disabled_text = QColor("#8b93a6")
        tip_base = QColor("#2a2f38")
        tip_text = QColor("#e8eaed")
        mid = QColor("#404854")

    p.setColor(c.Window, window)
    p.setColor(c.WindowText, win_text)
    p.setColor(c.Base, base)
    p.setColor(c.AlternateBase, alt)
    p.setColor(c.Text, win_text)
    p.setColor(c.Button, btn)
    p.setColor(c.ButtonText, btn_text)
    p.setColor(c.Highlight, highlight)
    p.setColor(c.HighlightedText, QColor("#ffffff"))
    p.setColor(c.Link, highlight)
    p.setColor(c.LinkVisited, highlight)
    p.setColor(c.PlaceholderText, disabled_text)
    p.setColor(c.ToolTipBase, tip_base)
    p.setColor(c.ToolTipText, tip_text)
    p.setColor(c.Mid, mid)
    return p


def _sync_auxiliary_styles(window: QMainWindow, theme: str) -> None:
    """Widgets avec ``setStyleSheet`` figé : les réaligner sur le thème actuel."""
    err_color = "#b00020" if theme == "light" else "#ff8a8a"
    err = window.findChild(QLabel, "output_banner_error")
    if err is not None:
        err.setStyleSheet(f"color: {err_color};")
