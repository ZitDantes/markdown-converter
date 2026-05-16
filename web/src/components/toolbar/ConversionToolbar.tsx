import type { FileQueueItem } from "@shared/bridge-contract";
import { CHIP_EXTENSIONS } from "../../lib/formatColors";
import { countsByExtension } from "../../lib/queueFilters";
import { FormatChip } from "./FormatChip";
import { Segmented } from "./Segmented";

export type ConversionMode = "standard" | "strict";

type ConversionToolbarProps = {
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
};

const MODE_OPTIONS = [
  {
    value: "standard" as const,
    label: "Standard",
    title:
      "Par défaut : en cas d'échec ou de résultat vide, le programme peut tenter une autre voie de conversion lorsque c'est possible sur cette machine.",
  },
  {
    value: "strict" as const,
    label: "Strict",
    title:
      "Une seule tentative par fichier : aucune méthode de secours. Les documents difficiles peuvent échouer ou rester sans extrait exploitable.",
  },
];

export function ConversionToolbar({
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
}: ConversionToolbarProps) {
  const counts = countsByExtension(items);
  const extensionsWithFiles = CHIP_EXTENSIONS.filter((ext) => (counts[ext] ?? 0) > 0);

  return (
    <div className="conversion-toolbar">
      <div className="toolbar toolbar--actions" role="toolbar" aria-label="Actions principales">
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
        <Segmented
          value={conversionMode}
          options={MODE_OPTIONS.map((o) => ({
            ...o,
            label: o.value === "standard" ? "Standard (recommandé)" : o.label,
          }))}
          onChange={onConversionModeChange}
          disabled={!bridgeReady}
          aria-label="Mode de conversion"
        />
        <span className="toolbar__flex" />
        <input
          type="search"
          className="toolbar-search"
          placeholder="Rechercher un fichier…"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          disabled={!bridgeReady}
          aria-label="Rechercher dans la file"
        />
      </div>

      {extensionsWithFiles.length > 0 && (
        <div className="toolbar-filters">
          <span className="toolbar-filters__label">Filtrer</span>
          {extensionsWithFiles.map((ext) => (
            <FormatChip
              key={ext}
              extension={ext}
              count={counts[ext] ?? 0}
              active={activeExtensions.has(ext)}
              isDark={isDark}
              onClick={() => onToggleExtension(ext)}
            />
          ))}
          {activeExtensions.size > 0 && (
            <button type="button" className="toolbar-filters__clear" onClick={onClearFilters}>
              Tout afficher
            </button>
          )}
        </div>
      )}
    </div>
  );
}
