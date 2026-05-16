import { useEffect } from "react";
import type { FileQueueItem, WebBackendBridge } from "@shared/bridge-contract";
import { FileGlyph } from "../queue/FileGlyph";
import { isSuccessLike, isUnsupportedLike } from "../queue/statusStyles";
import { StatusPill } from "../queue/StatusPill";
import { InspectorDetailsTab } from "./InspectorDetailsTab";
import { InspectorOutputTab } from "./InspectorOutputTab";
import { InspectorPreviewTab } from "./InspectorPreviewTab";

export type InspectorTab = "preview" | "output" | "details";

type InspectorPanelProps = {
  item: FileQueueItem | null;
  tab: InspectorTab;
  onTabChange: (tab: InspectorTab) => void;
  isDark: boolean;
  outputDir: string | null;
  backend: WebBackendBridge | null;
  bridgeReady: boolean;
  actionsDisabled: boolean;
  onPickOutput: () => void;
  onAfterRename: () => Promise<void>;
  onLog: (line: string) => void;
};

const TABS: { id: InspectorTab; label: string }[] = [
  { id: "preview", label: "Aperçu" },
  { id: "output", label: "Sortie" },
  { id: "details", label: "Détails" },
];

export function InspectorPanel({
  item,
  tab,
  onTabChange,
  isDark,
  outputDir,
  backend,
  bridgeReady,
  actionsDisabled,
  onPickOutput,
  onAfterRename,
  onLog,
}: InspectorPanelProps) {
  useEffect(() => {
    if (!item) return;
    if (isSuccessLike(item.status)) {
      onTabChange("preview");
    } else if (
      item.status === "error" ||
      item.status === "empty" ||
      isUnsupportedLike(item.status)
    ) {
      onTabChange("details");
    }
  }, [item?.sourcePath, item?.status, onTabChange]);

  return (
    <aside className="inspector" aria-label="Inspecteur">
      {item && (
        <header className="inspector__header">
          <FileGlyph extension={item.extension} color={item.formatColor} isDark={isDark} />
          <div className="inspector__header-text">
            <div className="inspector__file-name" title={item.fileName}>
              {item.fileName}
            </div>
            <div className="inspector__file-meta">
              {item.extension} · {item.sizeLabel}
            </div>
          </div>
          <StatusPill status={item.status} label={item.statusLabel} isDark={isDark} />
        </header>
      )}

      <div className="inspector__tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={`inspector__tab${tab === t.id ? " inspector__tab--active" : ""}`}
            onClick={() => onTabChange(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="inspector__content" role="tabpanel">
        {!item ? (
          <p className="inspector__empty">
            Sélectionnez un fichier dans la file pour afficher l'inspecteur.
          </p>
        ) : tab === "preview" ? (
          <InspectorPreviewTab item={item} backend={backend} bridgeReady={bridgeReady} />
        ) : tab === "output" ? (
          <InspectorOutputTab
            item={item}
            outputDir={outputDir}
            backend={backend}
            bridgeReady={bridgeReady}
            actionsDisabled={actionsDisabled}
            onPickOutput={onPickOutput}
            onAfterRename={onAfterRename}
            onLog={onLog}
          />
        ) : (
          <InspectorDetailsTab item={item} />
        )}
      </div>
    </aside>
  );
}
