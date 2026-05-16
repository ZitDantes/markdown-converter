import type { ReactNode } from "react";
import type { FileQueueItem, QueueState } from "@shared/bridge-contract";
import {
  ConversionToolbar,
  type ConversionMode,
} from "../toolbar/ConversionToolbar";

type MainColumnProps = {
  queue: QueueState | null;
  items: FileQueueItem[];
  isDark: boolean;
  bridgeReady: boolean;
  searchQuery: string;
  onSearchChange: (value: string) => void;
  activeExtensions: ReadonlySet<string>;
  onToggleExtension: (ext: string) => void;
  onClearFilters: () => void;
  conversionMode: ConversionMode;
  onConversionModeChange: (mode: ConversionMode) => void;
  onPickFiles: () => void;
  onPickFolder: () => void;
  onClear: () => void;
  onPickOutput: () => void;
  queueList: ReactNode;
};

export function MainColumn({
  queue,
  items,
  isDark,
  bridgeReady,
  searchQuery,
  onSearchChange,
  activeExtensions,
  onToggleExtension,
  onClearFilters,
  conversionMode,
  onConversionModeChange,
  onPickFiles,
  onPickFolder,
  onClear,
  onPickOutput,
  queueList,
}: MainColumnProps) {
  return (
    <div className="main-column">
      <ConversionToolbar
        items={items}
        isDark={isDark}
        bridgeReady={bridgeReady}
        searchQuery={searchQuery}
        onSearchChange={onSearchChange}
        activeExtensions={activeExtensions}
        onToggleExtension={onToggleExtension}
        onClearFilters={onClearFilters}
        conversionMode={conversionMode}
        onConversionModeChange={onConversionModeChange}
        onPickFiles={onPickFiles}
        onPickFolder={onPickFolder}
        onClear={onClear}
      />

      <div className="output-bar">
        <span className="output-bar__icon" aria-hidden>
          📁
        </span>
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

      <div className="queue-region">{queueList}</div>
    </div>
  );
}

