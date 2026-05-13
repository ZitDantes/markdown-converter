"""
Interface graphique Tkinter (français) pour Markdown Converter.
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from converter import convert_files
from logging_setup import get_log_file_path
from report import write_report

LEVEL_PREFIX: dict[str, str] = {
    "INFO": "[INFO] ",
    "WARNING": "[WARN] ",
    "ERROR": "[ERROR] ",
}

LEVEL_COLOR: dict[str, str] = {
    "WARNING": "#b06a00",
    "ERROR": "#b00020",
}


class MarkdownConverterApp(tk.Tk):
    """Fenêtre principale."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Markdown Converter")
        self.minsize(720, 520)

        self._explicit_files: list[Path] = []
        self._directory_roots: list[Path] = []
        self._output_dir: Path | None = None

        self._log_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self._build_ui()
        self._log_async("INFO", f"Fichier de log : {get_log_file_path()}")
        self.after(120, self._drain_log_queue)

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 6}

        frm_top = ttk.Frame(self)
        frm_top.pack(fill=tk.X, **pad)

        ttk.Button(frm_top, text="Ajouter des fichiers", command=self._on_add_files).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(frm_top, text="Ajouter un dossier", command=self._on_add_folder).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(frm_top, text="Vider la liste", command=self._on_clear_list).pack(
            side=tk.LEFT, padx=4
        )

        ttk.Label(self, text="Fichiers et dossiers sources :").pack(
            anchor=tk.W, padx=10, pady=(8, 0)
        )

        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._listbox = tk.Listbox(list_frame, height=12, yscrollcommand=scroll.set)
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self._listbox.yview)

        frm_out = ttk.Frame(self)
        frm_out.pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(frm_out, text="Choisir dossier de sortie", command=self._on_pick_output).pack(
            side=tk.LEFT
        )
        self._lbl_output = ttk.Label(frm_out, text="(aucun dossier de sortie sélectionné)")
        self._lbl_output.pack(side=tk.LEFT, padx=10)

        frm_prog = ttk.Frame(self)
        frm_prog.pack(fill=tk.X, padx=10, pady=4)
        self._progress = ttk.Progressbar(frm_prog, mode="determinate", maximum=100)
        self._progress.pack(fill=tk.X)
        self._lbl_progress = ttk.Label(frm_prog, text="Prêt.")
        self._lbl_progress.pack(anchor=tk.W, pady=(4, 0))

        ttk.Label(self, text="Journal :").pack(anchor=tk.W, padx=10, pady=(6, 0))
        log_frame = ttk.Frame(self)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._log = tk.Text(
            log_frame, height=10, wrap=tk.WORD, state=tk.DISABLED, yscrollcommand=log_scroll.set
        )
        self._log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.config(command=self._log.yview)

        for level, color in LEVEL_COLOR.items():
            self._log.tag_configure(level, foreground=color)

        frm_bottom = ttk.Frame(self)
        frm_bottom.pack(fill=tk.X, padx=10, pady=10)
        self._btn_convert = ttk.Button(frm_bottom, text="Convertir", command=self._on_convert)
        self._btn_convert.pack(side=tk.RIGHT)

    def _append_log(self, level: str, message: str) -> None:
        prefix = LEVEL_PREFIX.get(level, f"[{level}] ")
        tag = level if level in LEVEL_COLOR else ""
        self._log.config(state=tk.NORMAL)
        self._log.insert(tk.END, f"{prefix}{message}\n", tag)
        self._log.see(tk.END)
        self._log.config(state=tk.DISABLED)

    def _drain_log_queue(self) -> None:
        try:
            while True:
                level, msg = self._log_queue.get_nowait()
                self._append_log(level, msg)
        except queue.Empty:
            pass
        self.after(120, self._drain_log_queue)

    def _log_async(self, level: str, message: str) -> None:
        self._log_queue.put((level, message))

    def _refresh_listbox(self) -> None:
        self._listbox.delete(0, tk.END)
        for d in self._directory_roots:
            self._listbox.insert(tk.END, f"[Dossier] {d}")
        for f in self._explicit_files:
            self._listbox.insert(tk.END, f"[Fichier] {f}")

    def _on_add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Sélectionner des documents",
            filetypes=[
                ("Documents supportés", "*.docx *.pptx *.pdf *.xlsx *.html *.htm *.txt"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        for p in paths:
            self._explicit_files.append(Path(p).resolve())
        self._refresh_listbox()

    def _on_add_folder(self) -> None:
        d = filedialog.askdirectory(title="Choisir un dossier à parcourir récursivement")
        if d:
            self._directory_roots.append(Path(d).resolve())
            self._refresh_listbox()

    def _on_clear_list(self) -> None:
        self._explicit_files.clear()
        self._directory_roots.clear()
        self._refresh_listbox()

    def _on_pick_output(self) -> None:
        d = filedialog.askdirectory(title="Dossier de sortie pour les fichiers Markdown")
        if d:
            self._output_dir = Path(d).resolve()
            self._lbl_output.config(text=str(self._output_dir))

    def _on_convert(self) -> None:
        if self._output_dir is None:
            messagebox.showwarning(
                "Dossier de sortie",
                "Veuillez d'abord choisir un dossier de sortie.",
            )
            return
        if not self._explicit_files and not self._directory_roots:
            messagebox.showwarning(
                "Aucune source",
                "Ajoutez au moins un fichier ou un dossier contenant des documents supportés.",
            )
            return
        self._btn_convert.config(state=tk.DISABLED)
        self._progress["value"] = 0
        self._lbl_progress.config(text="Conversion en cours…")

        def worker() -> None:
            try:
                summary = convert_files(
                    explicit_files=list(self._explicit_files),
                    directory_roots=list(self._directory_roots),
                    output_dir=self._output_dir,  # type: ignore[arg-type]
                    on_log=self._log_async,
                    on_progress=lambda i, t, lab, *_: self.after(
                        0,
                        lambda i=i, t=t, lab=lab: self._update_progress(i, t, lab),
                    ),
                )
                report_path = write_report(summary)
                self._log_async("INFO", f"Rapport enregistré : {report_path}")
                self.after(0, lambda: self._conversion_finished(True, None))
            except Exception as e:  # noqa: BLE001
                # Garde-fou du thread worker : tout doit être attrapé sinon le thread
                # meurt silencieusement et l'UI reste figée. On préfixe le message
                # par le type d'exception (ex. « EngineNotAvailableError : … »)
                # pour faciliter le diagnostic côté utilisateur.
                err = f"{type(e).__name__} : {e}"
                self._log_async("ERROR", f"Erreur fatale du worker : {err}")
                self.after(0, lambda err=err: self._conversion_finished(False, err))

        threading.Thread(target=worker, daemon=True).start()

    def _update_progress(self, index: int, total: int, label: str) -> None:
        pct = 0 if total <= 0 else int(min(100, max(0, round(100 * index / total))))
        self._progress["value"] = pct
        self._lbl_progress.config(text=f"{index}/{total} — {label}")

    def _conversion_finished(self, ok: bool, err: str | None) -> None:
        self._btn_convert.config(state=tk.NORMAL)
        self._progress["value"] = 100 if ok else 0
        self._lbl_progress.config(text="Terminé." if ok else "Interrompu ou en erreur.")
        if ok:
            messagebox.showinfo(
                "Conversion", "Conversion terminée. Consultez le journal et le rapport."
            )
        else:
            messagebox.showerror(
                "Erreur",
                "Une erreur inattendue s'est produite pendant le traitement.\n\n" + (err or ""),
            )


def run_app() -> None:
    app = MarkdownConverterApp()
    app.mainloop()
