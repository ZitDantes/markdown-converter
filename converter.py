"""
Logique de conversion : orchestre les moteurs (MarkItDown en priorité,
Pandoc en secours si disponible).

Toute l'intégration spécifique aux moteurs est isolée dans le package
``engines`` ; ce module se concentre sur l'orchestration du lot, le statut
par fichier et la construction du front-matter Markdown.
"""

from __future__ import annotations

import inspect
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from engines import (
    ConverterEngine,
    EngineConversionError,
    MarkItDownEngine,
    PandocEngine,
)
from errors import (
    EmptyConversionError,
    EngineFailureError,
    OutputWriteError,
    UnsupportedFormatError,
)
from logging_setup import (
    CallbackHandler,
    LogCallback,
    get_logger,
    install_callback_handler,
    remove_callback_handler,
)
from utils import (
    SUPPORTED_EXTENSIONS,
    clean_markdown_body,
    format_warning_for_extension,
    is_effectively_empty_markdown,
    merge_file_lists,
    normalize_extension,
    unique_output_md_path,
    yaml_scalar_double_quoted,
)

logger = get_logger("converter")


class ConversionStatus(str, Enum):
    """
    Statuts de fin pour un fichier source.

    Trois variantes de succès sont distinguées pour l'UI et le rapport :

    - ``SUCCESS`` : conversion OK, sans avertissement de format, via le moteur
      primaire (MarkItDown aujourd'hui).
    - ``SUCCESS_REVIEW`` : conversion OK mais le format demande une relecture
      humaine (cf. ``utils.format_warning_for_extension``).
    - ``SUCCESS_FALLBACK`` : conversion OK obtenue **uniquement** grâce au moteur
      de secours (Pandoc) — le moteur primaire a échoué ou produit du vide.

    **Règle de priorité** lorsque les deux conditions s'appliquent
    (ex. PDF récupéré par Pandoc) : ``SUCCESS_REVIEW`` l'emporte sur
    ``SUCCESS_FALLBACK``. L'information actionnable pour l'utilisateur
    (« il faut relire ») prime sur l'information technique (« obtenu via
    secours »). Le drapeau ``FileConversionRecord.used_pandoc_fallback`` reste
    disponible pour qu'une UI affiche l'info technique en plus.
    """

    SUCCESS = "success"
    SUCCESS_REVIEW = "success_review"
    SUCCESS_FALLBACK = "success_fallback"
    ERROR = "error"
    UNSUPPORTED = "unsupported"
    EMPTY = "empty"
    # Transitoire : un fichier est en cours de traitement dans ``convert_files``.
    # Ne doit pas figurer dans un résumé final (toujours remplacé par un statut
    # terminal avant de passer au fichier suivant).
    PROCESSING = "processing"


SUCCESS_STATUSES: frozenset[ConversionStatus] = frozenset(
    {
        ConversionStatus.SUCCESS,
        ConversionStatus.SUCCESS_REVIEW,
        ConversionStatus.SUCCESS_FALLBACK,
    }
)


@dataclass
class FileConversionRecord:
    """Résultat pour un fichier source."""

    source_path: Path
    status: ConversionStatus
    output_path: Path | None = None
    message: str | None = None
    used_pandoc_fallback: bool = False
    # Nom du moteur ayant produit le Markdown (None si aucun n'a réussi).
    # Plus évolutif que ``used_pandoc_fallback`` pour de futurs moteurs (OCR, etc.).
    engine_used: str | None = None
    # Nom de la classe d'exception associée au statut non-SUCCESS (ex. "EngineFailureError",
    # "OutputWriteError", "EmptyConversionError"). ``None`` pour un succès.
    error_type: str | None = None
    # Progression du fichier courant dans ``[0.0, 1.0]`` (1.0 = étape terminée).
    # Mis à jour pendant la boucle de conversion pour les UIs type barre par ligne.
    progress_percent: float = 0.0
    # Corps Markdown produit (front-matter compris), rempli uniquement quand
    # ``convert_files(..., keep_output_in_memory=True)`` ET que l'écriture sur disque
    # a réussi. Sinon ``None`` pour ne pas charger la RAM sur de gros lots. Pratique
    # pour un onglet « Aperçu » côté UI sans relire le fichier produit.
    output_md_text: str | None = None


@dataclass
class ConversionSummary:
    """Synthèse d'un lot de conversions."""

    started_at: datetime
    finished_at: datetime
    output_dir: Path
    records: list[FileConversionRecord] = field(default_factory=list)
    unsupported_skipped: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    pandoc_available: bool = False


LogFn = LogCallback  # rétro-compat : type alias public exporté par converter.py
# ``index`` / ``total`` / ``label`` : inchangés par rapport à l'API historique.
# ``percent`` (0.0-1.0) : avancement **global du lot** ; absent pour les callbacks à trois arguments.
ProgressFn = Callable[..., None]


def _batch_percent_0_1(idx: int, total: int, file_progress: float) -> float:
    """
    Part du lot dans ``[0.0, 1.0]``.

    ``idx`` : indice 1-based du fichier dans le lot, ``file_progress`` : fraction
    ``[0, 1]`` pour le fichier courant (0 = début, 1 = terminé).
    """
    if total <= 0:
        return 1.0
    return min(1.0, max(0.0, (idx - 1 + file_progress) / total))


def _wrap_progress_callback(
    on_progress: ProgressFn | None,
) -> Callable[[int, int, str, float], None]:
    """Adapte les callbacks ``(i, t, l)`` (historique) et ``(i, t, l, p)`` (enrichi)."""

    if on_progress is None:
        return lambda *_a, **_k: None

    def wrapped(index: int, total: int, label: str, percent: float) -> None:
        sig = inspect.signature(on_progress)
        params = [
            p
            for p in sig.parameters.values()
            if p.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        if len(params) >= 4:
            on_progress(index, total, label, percent)  # type: ignore[misc]
        else:
            on_progress(index, total, label)  # type: ignore[misc]

    return wrapped


def _infer_title_from_body(stem: str, body: str) -> str:
    """Titre : première ligne ``# ...`` si présente, sinon nom de fichier sans extension."""
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip() or stem
    return stem


def _build_front_matter(
    titre: str,
    fichier_source: str,
    date_conversion: str,
    avertissement: str | None,
) -> str:
    lines = [
        "---",
        f"titre: {yaml_scalar_double_quoted(titre)}",
        f"fichier_source: {yaml_scalar_double_quoted(fichier_source)}",
        f"date_conversion: {yaml_scalar_double_quoted(date_conversion)}",
    ]
    if avertissement:
        lines.append(f"avertissement: {yaml_scalar_double_quoted(avertissement)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def _resolve_success_status(
    fmt_warning: str | None,
    used_fallback: bool,
) -> ConversionStatus:
    """
    Sélectionne le statut de succès fin selon le contexte.

    Voir la docstring de ``ConversionStatus`` pour la règle de priorité
    (``SUCCESS_REVIEW`` > ``SUCCESS_FALLBACK`` > ``SUCCESS``).
    """
    if fmt_warning:
        return ConversionStatus.SUCCESS_REVIEW
    if used_fallback:
        return ConversionStatus.SUCCESS_FALLBACK
    return ConversionStatus.SUCCESS


def _convert_and_clean(engine: ConverterEngine, src: Path) -> str:
    """Convertit ``src`` avec ``engine`` puis nettoie le Markdown produit."""
    return clean_markdown_body(engine.convert(src))


def _try_fallback_convert(engine: ConverterEngine, src: Path) -> str | None:
    """
    Tente une conversion via ``engine`` (utilisé en secours).

    Renvoie le Markdown nettoyé, ou ``None`` si le moteur a levé une
    ``EngineConversionError`` (l'erreur est alors loggée en WARNING). Les
    autres exceptions sont laissées remonter à l'orchestrateur.
    """
    try:
        return _convert_and_clean(engine, src)
    except EngineConversionError as e:
        logger.warning("%s (secours) n'a pas pu convertir « %s » : %s", engine.name, src.name, e)
        return None


def _write_markdown_output(out_path: Path, header: str, body: str) -> str:
    """
    Écrit ``header + body + "\n"`` dans ``out_path`` et retourne le contenu écrit.

    Le retour est l'image fidèle de ce qui se trouve sur disque (front-matter
    + corps + saut de ligne final), pratique pour le remettre ensuite dans
    ``FileConversionRecord.output_md_text`` sans relire le fichier.

    Lève ``OutputWriteError`` (avec ``OSError`` comme cause) si l'écriture échoue
    pour une raison disque/permissions.
    """
    content = header + body + "\n"
    try:
        out_path.write_text(content, encoding="utf-8")
    except OSError as e:
        raise OutputWriteError(f"Impossible d'écrire « {out_path.name} » : {e}") from e
    return content


def convert_files(
    explicit_files: list[Path],
    directory_roots: list[Path],
    output_dir: Path,
    on_log: LogFn | None = None,
    on_progress: ProgressFn | None = None,
    *,
    keep_output_in_memory: bool = False,
) -> ConversionSummary:
    """
    Convertit une liste de fichiers et/ou l'arborescence de dossiers vers ``output_dir``.

    ``on_log(level, message)`` reçoit le niveau (``"INFO"`` / ``"WARNING"`` /
    ``"ERROR"``) et le message en français.

    ``on_progress(index, total, label, percent=...)`` : ``index`` et ``total``
    suivent la convention historique (``index`` vaut ``idx - 1`` au début du
    fichier ``idx``, puis ``idx`` une fois le fichier terminé). ``percent``
    (``0.0``-``1.0``) est la part **globale** du lot ; il est omis pour les
    callbacks existants à trois arguments (rétrocompatibilité).

    ``keep_output_in_memory`` (par défaut ``False``) : si ``True``, le Markdown
    produit (front-matter inclus) est conservé dans
    ``FileConversionRecord.output_md_text`` après écriture réussie, pour
    permettre à une UI d'afficher un aperçu sans relire le disque. À utiliser
    avec précaution sur de gros lots (consommation mémoire ∝ taille du lot).
    Sinon le champ reste ``None``.

    Tous les messages sont également écrits dans le fichier de log persistant
    configuré par ``logging_setup.setup_logging()``.
    """
    started = datetime.now()
    prog = _wrap_progress_callback(on_progress)

    callback_handler: CallbackHandler | None = (
        install_callback_handler(on_log) if on_log is not None else None
    )

    try:
        return _run_conversion(
            explicit_files,
            directory_roots,
            output_dir,
            prog,
            started,
            keep_output_in_memory=keep_output_in_memory,
        )
    finally:
        if callback_handler is not None:
            remove_callback_handler(callback_handler)


def _run_conversion(
    explicit_files: list[Path],
    directory_roots: list[Path],
    output_dir: Path,
    prog: Callable[[int, int, str, float], None],
    started: datetime,
    *,
    keep_output_in_memory: bool,
) -> ConversionSummary:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    pandoc_ok = PandocEngine.is_available()
    if not pandoc_ok:
        logger.info(
            "Note : Pandoc n'est pas installé ou absent du PATH. "
            "La conversion utilise **uniquement MarkItDown**, ce qui est le fonctionnement "
            "normal du programme. Pandoc est **optionnel** : il sert de secours si un fichier "
            "pose problème avec MarkItDown. Pour l'ajouter : « brew install pandoc » (macOS) "
            "ou voir https://pandoc.org/installing.html ."
        )
    else:
        logger.info(
            "Pandoc est disponible (%s) ; "
            "il ne sera utilisé qu'en secours si MarkItDown échoue ou renvoie un contenu vide.",
            PandocEngine.executable_path(),
        )

    supported, unsupported = merge_file_lists(explicit_files, directory_roots)
    summary = ConversionSummary(
        started_at=started,
        finished_at=started,
        output_dir=output_dir,
        unsupported_skipped=list(unsupported),
        pandoc_available=pandoc_ok,
    )

    for p in unsupported:
        ext = normalize_extension(p)
        msg = f"Ignoré (format non supporté « {ext or '(sans extension)'} ») : {p}"
        logger.warning(msg)
        summary.warnings.append(msg)

    total = len(supported)
    if total == 0:
        logger.warning(
            "Aucun fichier à convertir : ajoutez des fichiers ou un dossier "
            "contenant des formats supportés."
        )
        summary.finished_at = datetime.now()
        return summary

    # Instanciation des moteurs (le primaire peut lever EngineNotAvailableError → propagé).
    primary: ConverterEngine = MarkItDownEngine()
    fallback: ConverterEngine | None = PandocEngine() if pandoc_ok else None

    for idx, src in enumerate(supported, start=1):
        label = src.name
        ext = normalize_extension(src)
        progress_closed = False

        if ext not in SUPPORTED_EXTENSIONS:
            summary.records.append(
                FileConversionRecord(
                    source_path=src,
                    status=ConversionStatus.UNSUPPORTED,
                    message="Extension non reconnue.",
                    error_type=UnsupportedFormatError.__name__,
                    progress_percent=1.0,
                )
            )
            prog(idx - 1, total, label, _batch_percent_0_1(idx, total, 0.0))
            prog(idx, total, label, _batch_percent_0_1(idx, total, 1.0))
            progress_closed = True
            continue

        rec = FileConversionRecord(
            source_path=src,
            status=ConversionStatus.PROCESSING,
            progress_percent=0.0,
        )
        summary.records.append(rec)
        prog(idx - 1, total, label, _batch_percent_0_1(idx, total, 0.0))

        fmt_warning = format_warning_for_extension(ext)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def _make_tick(
            r: FileConversionRecord,
            i: int,
            tot: int,
            lab: str,
        ) -> Callable[[float], None]:
            def inner(file_part: float) -> None:
                r.progress_percent = file_part
                prog(i - 1, tot, lab, _batch_percent_0_1(i, tot, file_part))

            return inner

        tick = _make_tick(rec, idx, total, label)

        try:
            body = _convert_and_clean(primary, src)
            tick(0.2)
            used_fallback = False
            engine_used: str | None = primary.name

            if is_effectively_empty_markdown(body) and fallback is not None:
                fallback_body = _try_fallback_convert(fallback, src)
                if fallback_body is not None:
                    body = fallback_body
                    used_fallback = True
                    engine_used = fallback.name

            tick(0.55)

            if is_effectively_empty_markdown(body):
                msg = (
                    "Le document converti est vide après nettoyage. "
                    "Le fichier Markdown n'a pas été créé pour éviter un fichier vide."
                )
                logger.error("Échec pour « %s » : %s", src.name, msg)
                rec.status = ConversionStatus.EMPTY
                rec.message = msg
                rec.error_type = EmptyConversionError.__name__
                rec.progress_percent = 1.0
                summary.warnings.append(f"{src} : {msg}")
                prog(idx, total, label, _batch_percent_0_1(idx, total, 1.0))
                progress_closed = True
                continue

            titre = _infer_title_from_body(src.stem, body)
            header = _build_front_matter(
                titre=titre,
                fichier_source=str(src),
                date_conversion=date_str,
                avertissement=fmt_warning,
            )
            out_path = unique_output_md_path(output_dir, src.stem)
            tick(0.85)
            written = _write_markdown_output(out_path, header, body)

            rec.status = _resolve_success_status(fmt_warning, used_fallback)
            rec.output_path = out_path
            rec.used_pandoc_fallback = used_fallback
            rec.engine_used = engine_used
            rec.progress_percent = 1.0
            if keep_output_in_memory:
                rec.output_md_text = written
            how = f"{engine_used} (secours)" if used_fallback else engine_used
            logger.info("OK — « %s » → « %s » (%s).", src.name, out_path.name, how)

        except EngineConversionError as e:
            human = f"{type(e).__name__} : {e}"
            logger.warning("Erreur moteur pour « %s » : %s", src.name, human)

            if fallback is not None:
                fallback_body = _try_fallback_convert(fallback, src)
                if fallback_body is not None and not is_effectively_empty_markdown(fallback_body):
                    titre = _infer_title_from_body(src.stem, fallback_body)
                    header = _build_front_matter(
                        titre=titre,
                        fichier_source=str(src),
                        date_conversion=date_str,
                        avertissement=fmt_warning,
                    )
                    out_path = unique_output_md_path(output_dir, src.stem)
                    try:
                        tick(0.75)
                        written = _write_markdown_output(out_path, header, fallback_body)
                    except OutputWriteError as we:
                        logger.error("Erreur d'écriture pour « %s » : %s", src.name, we)
                        rec.status = ConversionStatus.ERROR
                        rec.message = str(we)
                        rec.error_type = OutputWriteError.__name__
                        rec.progress_percent = 1.0
                        summary.warnings.append(f"{src} : {we}")
                        prog(idx, total, label, _batch_percent_0_1(idx, total, 1.0))
                        progress_closed = True
                        continue
                    rec.status = _resolve_success_status(fmt_warning, used_fallback=True)
                    rec.output_path = out_path
                    rec.used_pandoc_fallback = True
                    rec.engine_used = fallback.name
                    rec.message = (
                        f"Conversion réussie via {fallback.name} après échec de {primary.name}."
                    )
                    rec.progress_percent = 1.0
                    if keep_output_in_memory:
                        rec.output_md_text = written
                    logger.info(
                        "Récupéré par %s — « %s » → « %s ».",
                        fallback.name,
                        src.name,
                        out_path.name,
                    )
                    prog(idx, total, label, _batch_percent_0_1(idx, total, 1.0))
                    progress_closed = True
                    continue

            logger.error("Échec total pour « %s » : %s", src.name, human)
            rec.status = ConversionStatus.ERROR
            rec.message = human
            rec.error_type = EngineFailureError.__name__
            rec.progress_percent = 1.0
            summary.warnings.append(f"{src} : {human}")

        except OutputWriteError as we:
            logger.error("Erreur d'écriture pour « %s » : %s", src.name, we)
            rec.status = ConversionStatus.ERROR
            rec.message = str(we)
            rec.error_type = OutputWriteError.__name__
            rec.progress_percent = 1.0
            summary.warnings.append(f"{src} : {we}")

        except Exception as e:  # noqa: BLE001
            tb = traceback.format_exc()
            human = f"{type(e).__name__} : {e}"
            logger.error("Erreur inattendue pour « %s » : %s", src.name, human)
            rec.status = ConversionStatus.ERROR
            rec.message = human
            rec.error_type = type(e).__name__
            rec.progress_percent = 1.0
            summary.warnings.append(f"Trace technique pour « {src} » :\n```\n{tb}\n```")

        if not progress_closed:
            prog(idx, total, label, _batch_percent_0_1(idx, total, 1.0))

    summary.finished_at = datetime.now()
    return summary
