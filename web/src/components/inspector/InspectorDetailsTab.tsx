import type { FileQueueItem } from "@shared/bridge-contract";

type InspectorDetailsTabProps = {
  item: FileQueueItem;
};

function DetailRow({ label, value, title }: { label: string; value: string; title?: string }) {
  return (
    <div className="inspector-detail-row">
      <span className="inspector-detail-row__label">{label}</span>
      <span className="inspector-detail-row__value" title={title}>
        {value}
      </span>
    </div>
  );
}

export function InspectorDetailsTab({ item }: InspectorDetailsTabProps) {
  const fallbackLabel = item.usedPandocFallback ? "Oui" : "Non";
  const fallbackTitle = item.usedPandocFallback
    ? "Ce Markdown a été produit (en tout ou en partie) via le moteur de secours."
    : undefined;

  return (
    <div className="inspector-details">
      <DetailRow label="Format" value={item.extension || "—"} />
      <DetailRow label="Taille source" value={item.sizeLabel} />
      <DetailRow label="Statut" value={item.statusLabel} />
      <DetailRow label="Moteur" value={item.engineUsed?.trim() || "—"} />
      <DetailRow label="Secours" value={fallbackLabel} title={fallbackTitle} />
      <DetailRow label="Type d'erreur" value={item.errorType?.trim() || "—"} />
      {(item.message ?? "").trim() ? (
        <div className="inspector-details__message-block">
          <span className="inspector-detail-row__label">Message</span>
          <pre className="inspector-details__message">{item.message}</pre>
        </div>
      ) : null}
    </div>
  );
}
