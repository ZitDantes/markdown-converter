"""
Parseur léger de front-matter YAML pour l'inspecteur Qt (PLO-38).

Conçu pour lire **précisément** le format produit par
``converter._build_front_matter`` : un bloc délimité par ``---`` avec
des paires ``cle: "valeur en double-guillemets"`` encodées via
``utils.yaml_scalar_double_quoted``. On n'introduit volontairement pas
de dépendance PyYAML.

Si le contenu ne commence pas par ``---``, ``parse_front_matter`` renvoie
un dict vide et le texte d'origine (pas de front-matter à exposer).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrontMatterParseResult:
    """Résultat du parsing d'un Markdown produit par ``converter``."""

    front_matter: dict[str, str]
    body: str
    raw_front_matter: str  # bloc `---\n...\n---\n` recopié tel quel (vide si absent)


_DELIM = "---"


def _unescape_double_quoted(scalar: str) -> str:
    """Inverse de ``utils.yaml_scalar_double_quoted`` (sans les guillemets entourants)."""
    out: list[str] = []
    i = 0
    n = len(scalar)
    while i < n:
        ch = scalar[i]
        if ch == "\\" and i + 1 < n:
            nxt = scalar[i + 1]
            if nxt == "n":
                out.append("\n")
            elif nxt == "r":
                out.append("\r")
            elif nxt == '"':
                out.append('"')
            elif nxt == "\\":
                out.append("\\")
            else:
                # séquence inconnue : on garde le backslash + caractère, défensif
                out.append(ch)
                out.append(nxt)
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _parse_scalar(raw: str) -> str:
    """Parse une valeur de front-matter (double-guillemets ou nu)."""
    raw = raw.strip()
    if len(raw) >= 2 and raw.startswith('"') and raw.endswith('"'):
        return _unescape_double_quoted(raw[1:-1])
    return raw


def parse_front_matter(md_text: str) -> FrontMatterParseResult:
    """Sépare le front-matter ``---`` du corps Markdown.

    Le front-matter retourné est un dict ordonné selon l'ordre d'apparition
    des clés dans le bloc (Python 3.7+ : dict insertion-ordered).

    Si aucun front-matter n'est détecté, ``front_matter`` est vide et
    ``body`` vaut ``md_text``.
    """
    lines = md_text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != _DELIM:
        return FrontMatterParseResult({}, md_text, "")

    # Trouver la ligne de fermeture ``---``.
    end_idx: int | None = None
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n") == _DELIM:
            end_idx = i
            break

    if end_idx is None:
        # Bloc non fermé : on ne tente pas de deviner, on rend tel quel.
        return FrontMatterParseResult({}, md_text, "")

    raw_block = "".join(lines[: end_idx + 1])
    front: dict[str, str] = {}
    for raw_line in lines[1:end_idx]:
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            continue
        if ":" not in line:
            # ligne inattendue : on ignore proprement
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        if not key:
            continue
        front[key] = _parse_scalar(value)

    body_start = end_idx + 1
    # Le format produit par ``converter`` ajoute ``\n\n`` après le bloc — on
    # ne saute pas ces lignes vides pour préserver fidèlement la sortie.
    body = "".join(lines[body_start:])
    return FrontMatterParseResult(front, body, raw_block)
