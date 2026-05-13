"""
Logique de conversion : orchestre les moteurs (MarkItDown en priorité,
Pandoc en secours si disponible).

Toute l'intégration spécifique aux moteurs est isolée dans le package
``engines`` ; ce module se concentre sur l'orchestration du lot, le statut
par fichier et la construction du front-matter Markdown.
"""

from __future__ import annotations

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
ProgressFn = Callable[[int, int, str], None]


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


def _write_markdown_output(out_path: Path, header: str, body: str) -> None:
    """
    Écrit ``header + body`` dans ``out_path``.

    Lève ``OutputWriteError`` (avec ``OSError`` comme cause) si l'écriture échoue
    pour une raison disque/permissions.
    """
    try:
        out_path.write_text(header + body + "\n", encoding="utf-8")
    except OSError as e:
        raise OutputWriteError(f"Impossible d'écrire « {out_path.name} » : {e}") from e


def convert_files(
    explicit_files: list[Path],
    directory_roots: list[Path],
    output_dir: Path,
    on_log: LogFn | None = None,
    on_progress: ProgressFn | None = None,
) -> ConversionSummary:
    """
    Convertit une liste de fichiers et/ou l'arborescence de dossiers vers ``output_dir``.

    ``on_log(level, message)`` reçoit le niveau (``"INFO"`` / ``"WARNING"`` /
    ``"ERROR"``) et le message en français ; ``on_progress(index, total, label)``.

    Tous les messages sont également écrits dans le fichier de log persistant
    configuré par ``logging_setup.setup_logging()``.
    """
    started = datetime.now()
    prog = on_progress or (lambda _i, _t, _l: None)

    callback_handler: CallbackHandler | None = (
        install_callback_handler(on_log) if on_log is not None else None
    )

    try:
        return _run_conversion(explicit_files, directory_roots, output_dir, prog, started)
    finally:
        if callback_handler is not None:
            remove_callback_handler(callback_handler)


def _run_conversion(
    explicit_files: list[Path],
    directory_roots: list[Path],
    output_dir: Path,
    prog: ProgressFn,
    started: datetime,
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
        prog(idx - 1, total, label)
        ext = normalize_extension(src)
        if ext not in SUPPORTED_EXTENSIONS:
            summary.records.append(
                FileConversionRecord(
                    source_path=src,
                    status=ConversionStatus.UNSUPPORTED,
                    message="Extension non reconnue.",
                    error_type=UnsupportedFormatError.__name__,
                )
            )
            continue

        fmt_warning = format_warning_for_extension(ext)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            body = _convert_and_clean(primary, src)
            used_fallback = False
            engine_used: str | None = primary.name

            if is_effectively_empty_markdown(body) and fallback is not None:
                fallback_body = _try_fallback_convert(fallback, src)
                if fallback_body is not None:
                    body = fallback_body
                    used_fallback = True
                    engine_used = fallback.name

            if is_effectively_empty_markdown(body):
                msg = (
                    "Le document converti est vide après nettoyage. "
                    "Le fichier Markdown n'a pas été créé pour éviter un fichier vide."
                )
                logger.error("Échec pour « %s » : %s", src.name, msg)
                summary.records.append(
                    FileConversionRecord(
                        source_path=src,
                        status=ConversionStatus.EMPTY,
                        message=msg,
                        error_type=EmptyConversionError.__name__,
                    )
                )
                summary.warnings.append(f"{src} : {msg}")
                continue

            titre = _infer_title_from_body(src.stem, body)
            header = _build_front_matter(
                titre=titre,
                fichier_source=str(src),
                date_conversion=date_str,
                avertissement=fmt_warning,
            )
            out_path = unique_output_md_path(output_dir, src.stem)
            _write_markdown_output(out_path, header, body)

            summary.records.append(
                FileConversionRecord(
                    source_path=src,
                    status=_resolve_success_status(fmt_warning, used_fallback),
                    output_path=out_path,
                    used_pandoc_fallback=used_fallback,
                    engine_used=engine_used,
                )
            )
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
                        _write_markdown_output(out_path, header, fallback_body)
                    except OutputWriteError as we:
                        logger.error("Erreur d'écriture pour « %s » : %s", src.name, we)
                        summary.records.append(
                            FileConversionRecord(
                                source_path=src,
                                status=ConversionStatus.ERROR,
                                message=str(we),
                                error_type=OutputWriteError.__name__,
                            )
                        )
                        summary.warnings.append(f"{src} : {we}")
                        continue
                    summary.records.append(
                        FileConversionRecord(
                            source_path=src,
                            status=_resolve_success_status(fmt_warning, used_fallback=True),
                            output_path=out_path,
                            used_pandoc_fallback=True,
                            engine_used=fallback.name,
                            message=(
                                f"Conversion réussie via {fallback.name} "
                                f"après échec de {primary.name}."
                            ),
                        )
                    )
                    logger.info(
                        "Récupéré par %s — « %s » → « %s ».",
                        fallback.name,
                        src.name,
                        out_path.name,
                    )
                    continue

            logger.error("Échec total pour « %s » : %s", src.name, human)
            summary.records.append(
                FileConversionRecord(
                    source_path=src,
                    status=ConversionStatus.ERROR,
                    message=human,
                    error_type=EngineFailureError.__name__,
                )
            )
            summary.warnings.append(f"{src} : {human}")

        except OutputWriteError as we:
            logger.error("Erreur d'écriture pour « %s » : %s", src.name, we)
            summary.records.append(
                FileConversionRecord(
                    source_path=src,
                    status=ConversionStatus.ERROR,
                    message=str(we),
                    error_type=OutputWriteError.__name__,
                )
            )
            summary.warnings.append(f"{src} : {we}")

        except Exception as e:  # noqa: BLE001
            tb = traceback.format_exc()
            human = f"{type(e).__name__} : {e}"
            logger.error("Erreur inattendue pour « %s » : %s", src.name, human)
            summary.records.append(
                FileConversionRecord(
                    source_path=src,
                    status=ConversionStatus.ERROR,
                    message=human,
                    error_type=type(e).__name__,
                )
            )
            summary.warnings.append(f"Trace technique pour « {src} » :\n```\n{tb}\n```")

        prog(idx, total, label)

    summary.finished_at = datetime.now()
    return summary
