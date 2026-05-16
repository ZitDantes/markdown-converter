/** Couleurs par format — aligné sur ``ui_conversion_display.py`` / handoff. */

export const CHIP_EXTENSIONS = [".docx", ".pdf", ".pptx", ".xlsx", ".html", ".txt"] as const;

const FORMAT_COLORS: Record<string, string> = {
  ".docx": "#2b6cb0",
  ".pdf": "#c0392b",
  ".pptx": "#d35400",
  ".xlsx": "#1e8449",
  ".html": "#6b46c1",
  ".htm": "#6b46c1",
  ".txt": "#4a5568",
};

export function formatColorForExtension(ext: string): string {
  const normalized = ext.startsWith(".") ? ext.toLowerCase() : `.${ext.toLowerCase()}`;
  return FORMAT_COLORS[normalized] ?? "#4a5568";
}

export function normalizeFilterExtension(ext: string): string {
  const e = ext.startsWith(".") ? ext.toLowerCase() : `.${ext.toLowerCase()}`;
  return e === ".htm" ? ".html" : e;
}
