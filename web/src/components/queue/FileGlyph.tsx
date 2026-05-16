type FileGlyphProps = {
  /** Extension avec point (ex. ``.pptx``) */
  extension: string;
  color: string;
  size?: number;
  isDark?: boolean;
};

function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  if (h.length !== 6) return `rgba(120, 120, 120, ${alpha})`;
  const r = Number.parseInt(h.slice(0, 2), 16);
  const g = Number.parseInt(h.slice(2, 4), 16);
  const b = Number.parseInt(h.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/** Glyphe extension — aligné sur ``design_handoff_ui_refonte/prototype/data.jsx`` (FileGlyph). */
/** Taille par défaut 30 px (handoff drop zone) ; 26 px trop étroit pour « html » / « xlsx ». */
export function FileGlyph({ extension, color, size = 30, isDark = false }: FileGlyphProps) {
  const ext = extension.replace(/^\./, "").toLowerCase();
  const height = size * 1.18;
  const fontSize = size * 0.28;
  const tintAlpha = isDark ? 0.18 : 0.12;

  return (
    <span
      className="file-glyph"
      style={{
        width: size,
        height,
        background: hexToRgba(color, tintAlpha),
        borderColor: `${color}33`,
        color,
        fontSize,
      }}
      aria-hidden
    >
      <span className="file-glyph__fold" style={{ background: color }} />
      <span className="file-glyph__label">{ext}</span>
    </span>
  );
}
