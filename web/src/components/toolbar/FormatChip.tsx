import { formatColorForExtension } from "../../lib/formatColors";

type FormatChipProps = {
  extension: string;
  count: number;
  active: boolean;
  isDark: boolean;
  onClick: () => void;
};

export function FormatChip({ extension, count, active, isDark, onClick }: FormatChipProps) {
  const color = formatColorForExtension(extension);

  return (
    <button
      type="button"
      className={`format-chip${active ? " format-chip--active" : ""}`}
      style={
        active
          ? {
              color,
              background: isDark ? `${color}33` : `${color}1f`,
              borderColor: `${color}66`,
            }
          : undefined
      }
      onClick={onClick}
      title={`Filtrer la file pour ne montrer que les ${extension}`}
    >
      <span className="format-chip__dot" style={{ background: color }} aria-hidden />
      <span>{extension}</span>
      <span className="format-chip__count">{count}</span>
    </button>
  );
}
