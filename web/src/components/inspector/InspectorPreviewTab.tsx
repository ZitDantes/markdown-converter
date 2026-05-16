import { useEffect, useState } from "react";
import type { FileQueueItem, InspectorPreviewResult, WebBackendBridge } from "@shared/bridge-contract";
import { parseJson, qtInvoke } from "@shared/bridge-contract";
import { isSuccessLike } from "../queue/statusStyles";

type InspectorPreviewTabProps = {
  item: FileQueueItem;
  backend: WebBackendBridge | null;
  bridgeReady: boolean;
};

export function InspectorPreviewTab({ item, backend, bridgeReady }: InspectorPreviewTabProps) {
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<InspectorPreviewResult | null>(null);

  useEffect(() => {
    if (!backend || !bridgeReady) {
      setPreview(null);
      return;
    }
    if (!isSuccessLike(item.status)) {
      setPreview({
        schemaVersion: "0",
        ok: false,
        message: item.message ?? "Aucun Markdown disponible pour ce fichier.",
      });
      return;
    }

    let cancelled = false;
    setLoading(true);
    void (async () => {
      try {
        const raw = await qtInvoke(() => backend.getInspectorPreview(item.sourcePath));
        const data = parseJson<InspectorPreviewResult>(raw);
        if (!cancelled) setPreview(data);
      } catch {
        if (!cancelled) {
          setPreview({
            schemaVersion: "0",
            ok: false,
            message: "Impossible de charger l'aperçu.",
          });
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [backend, bridgeReady, item.sourcePath, item.status, item.message]);

  if (loading && !preview) {
    return <p className="inspector__hint">Chargement de l'aperçu…</p>;
  }

  if (!preview?.ok) {
    return <p className="inspector__message">{preview?.message ?? "Aperçu indisponible."}</p>;
  }

  const fm = preview.frontMatter ?? {};
  const fmKeys = Object.keys(fm);

  return (
    <div className="inspector-preview">
      {preview.warning && (
        <div className="inspector-preview__warning" role="status">
          <span aria-hidden>⚠</span>
          <span>{preview.warning}</span>
        </div>
      )}
      {item.usedPandocFallback && (
        <div className="inspector-preview__fallback" role="status">
          Ce Markdown a pu être produit via le moteur de secours lorsque la conversion principale
          n'a pas suffi.
        </div>
      )}
      {fmKeys.length > 0 && (
        <div className="inspector-preview__yaml">
          <div className="inspector-preview__yaml-title">Métadonnées</div>
          <pre className="inspector-preview__yaml-pre">
            {fmKeys.map((key) => (
              <div key={key}>
                <span className="inspector-preview__yaml-key">{key}</span>
                <span className="inspector-preview__yaml-sep">: </span>
                <span className="inspector-preview__yaml-val">&quot;{fm[key]}&quot;</span>
              </div>
            ))}
          </pre>
        </div>
      )}
      <pre className="inspector-preview__body">{(preview.body ?? "").trim() || "—"}</pre>
    </div>
  );
}
