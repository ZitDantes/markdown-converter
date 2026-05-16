import type { FileQueueItem } from "@shared/bridge-contract";
import { FileGlyph } from "./FileGlyph";
import { MiniProgress, progressHint } from "./MiniProgress";
import { isSuccessLike, isUnsupportedLike } from "./statusStyles";
import { StatusPill } from "./StatusPill";

type FileRowProps = {
  item: FileQueueItem;
  selected: boolean;
  disabled: boolean;
  isDark: boolean;
  onSelect: () => void;
  onRemove: () => void;
};

export function FileRow({
  item,
  selected,
  disabled,
  isDark,
  onSelect,
  onRemove,
}: FileRowProps) {
  const showProgress = item.status === "processing" || isSuccessLike(item.status);
  const unsupported = isUnsupportedLike(item.status);

  return (
    <div
      className={`file-row${selected ? " file-row--selected" : ""}${unsupported ? " file-row--muted" : ""}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
    >
      <FileGlyph extension={item.extension} color={item.formatColor} isDark={isDark} />
      <div className="file-row__main">
        <div className="file-row__name" title={item.fileName}>
          {item.fileName}
        </div>
        <div className="file-row__meta" title={item.parentDir}>
          {item.parentDir} · {item.sizeLabel}
        </div>
      </div>
      <StatusPill status={item.status} label={item.statusLabel} isDark={isDark} />
      <div className="file-row__progress">
        {showProgress ? (
          <MiniProgress value={item.progressPercent} status={item.status} />
        ) : (
          <span className="file-row__hint">{progressHint(item.status, item.outputPath)}</span>
        )}
      </div>
      <div className="file-row__actions" onClick={(e) => e.stopPropagation()}>
        <button
          type="button"
          className="file-row__action"
          title="Renommer le .md de sortie (PLO-51)"
          disabled
          aria-disabled
        >
          ✎
        </button>
        <button
          type="button"
          className="file-row__action"
          title="Exclure du lot (à venir)"
          disabled
          aria-disabled
        >
          ⊘
        </button>
        <button
          type="button"
          className="file-row__action"
          title="Retirer de la file"
          disabled={disabled}
          onClick={onRemove}
        >
          ×
        </button>
      </div>
    </div>
  );
}
