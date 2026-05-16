import type { ReactNode } from "react";
import type { QueueState } from "@shared/bridge-contract";

type MainColumnProps = {
  queue: QueueState | null;
  bridgeReady: boolean;
  onPickFiles: () => void;
  onPickFolder: () => void;
  onClear: () => void;
  onPickOutput: () => void;
  queueList: ReactNode;
};

export function MainColumn({
  queue,
  bridgeReady,
  onPickFiles,
  onPickFolder,
  onClear,
  onPickOutput,
  queueList,
}: MainColumnProps) {
  const itemCount = queue?.items.length ?? 0;

  return (
    <div className="main-column">
      <div className="toolbar" role="toolbar" aria-label="Actions principales">
        <button type="button" className="btn" disabled={!bridgeReady} onClick={onPickFiles}>
          Fichiers
        </button>
        <button type="button" className="btn" disabled={!bridgeReady} onClick={onPickFolder}>
          Dossier
        </button>
        <button type="button" className="btn btn--ghost" disabled={!bridgeReady} onClick={onClear}>
          Vider
        </button>
        <span className="toolbar__sep" aria-hidden />
        <span className="toolbar__stub" title="Parité toolbar — PLO-50">
          Modes Standard / Strict (à venir)
        </span>
        <span className="toolbar__flex" />
        <span className="toolbar__stub toolbar__stub--search" title="Recherche — PLO-50">
          Rechercher…
        </span>
      </div>

      <div className="output-bar">
        <span className="output-bar__icon" aria-hidden>📁</span>
        <div className="output-bar__text">
          <span className="output-bar__label">Sortie</span>
          <span className="output-bar__path" title={queue?.outputDir ?? undefined}>
            {queue?.outputDir ?? "Aucun dossier de sortie"}
          </span>
        </div>
        <button type="button" className="btn btn--sm" disabled={!bridgeReady} onClick={onPickOutput}>
          Choisir…
        </button>
      </div>

      <div className="queue-region">
        <header className="queue-region__header">
          <span className="queue-region__title">File de conversion</span>
          <span className="queue-region__meta">
            {itemCount} fichier{itemCount !== 1 ? "s" : ""}
          </span>
        </header>
        <div className="queue-card">{queueList}</div>
      </div>
    </div>
  );
}
