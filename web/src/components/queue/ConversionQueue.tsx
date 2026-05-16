import type { FileQueueItem, QueueState } from "@shared/bridge-contract";
import { FileRow } from "./FileRow";

type ConversionQueueProps = {
  visibleItems: FileQueueItem[];
  totalCount: number;
  queue: QueueState | null;
  selectedPath: string | null;
  isDark: boolean;
  actionsDisabled: boolean;
  onSelect: (path: string) => void;
  onRemove: (path: string) => void;
};

export function ConversionQueue({
  visibleItems,
  totalCount,
  queue,
  selectedPath,
  isDark,
  actionsDisabled,
  onSelect,
  onRemove,
}: ConversionQueueProps) {
  if (totalCount === 0) {
    return (
      <div className="queue-card">
        <p className="queue-empty">
          Glissez-déposez des fichiers ou dossiers ici, ou utilisez Fichiers / Dossier.
        </p>
      </div>
    );
  }

  if (visibleItems.length === 0) {
    return (
      <>
        <header className="queue-region__header">
          <span className="queue-region__title">File de conversion</span>
          <span className="queue-region__meta">{totalCount} fichiers</span>
        </header>
        <div className="queue-card">
          <p className="queue-empty">Aucun fichier ne correspond à ce filtre.</p>
        </div>
      </>
    );
  }

  const visible = visibleItems.length;
  const metaParts: string[] = [];
  if (visible === totalCount) {
    metaParts.push(`${visible} fichier${visible !== 1 ? "s" : ""}`);
  } else {
    metaParts.push(`${visible} sur ${totalCount}`);
  }
  if (queue?.totalSizeLabel) {
    metaParts.push(queue.totalSizeLabel);
  }

  return (
    <>
      <header className="queue-region__header">
        <span className="queue-region__title">File de conversion</span>
        <span className="queue-region__meta">{metaParts.join(" · ")}</span>
      </header>
      <div className="queue-card queue-card--rows">
        {visibleItems.map((item, index) => (
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
