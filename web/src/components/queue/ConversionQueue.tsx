import type { FileQueueItem, QueueState } from "@shared/bridge-contract";
import { FileRow } from "./FileRow";

type ConversionQueueProps = {
  items: FileQueueItem[];
  queue: QueueState | null;
  selectedPath: string | null;
  isDark: boolean;
  actionsDisabled: boolean;
  onSelect: (path: string) => void;
  onRemove: (path: string) => void;
};

export function ConversionQueue({
  items,
  queue,
  selectedPath,
  isDark,
  actionsDisabled,
  onSelect,
  onRemove,
}: ConversionQueueProps) {
  if (items.length === 0) {
    return (
      <div className="queue-card">
        <p className="queue-empty">
          Glissez-déposez des fichiers ou utilisez Fichiers / Dossier (parité DnD — PLO-53).
        </p>
      </div>
    );
  }

  const total = items.length;
  const meta =
    queue?.totalSizeLabel != null
      ? `${total} fichier${total !== 1 ? "s" : ""} · ${queue.totalSizeLabel}`
      : `${total} fichier${total !== 1 ? "s" : ""}`;

  return (
    <>
      <header className="queue-region__header">
        <span className="queue-region__title">File de conversion</span>
        <span className="queue-region__meta">{meta}</span>
      </header>
      <div className="queue-card queue-card--rows">
        {items.map((item, index) => (
          <div key={item.sourcePath}>
            {index > 0 && <hr className="queue-card__sep" />}
            <FileRow
              item={item}
              selected={item.sourcePath === selectedPath}
              disabled={actionsDisabled}
              isDark={isDark}
              onSelect={() => onSelect(item.sourcePath)}
              onRemove={() => onRemove(item.sourcePath)}
            />
          </div>
        ))}
      </div>
    </>
  );
}
