import { useCallback, useEffect, useState } from "react";
import type {
  BulkRenameApplyResult,
  BulkRenameCaseMode,
  BulkRenamePlanResult,
  FileQueueItem,
  InspectorOutputPathResult,
  WebBackendBridge,
} from "@shared/bridge-contract";
import { parseJson, qtInvoke } from "@shared/bridge-contract";

type InspectorOutputTabProps = {
  item: FileQueueItem;
  outputDir: string | null;
  backend: WebBackendBridge | null;
  bridgeReady: boolean;
  actionsDisabled: boolean;
  onPickOutput: () => void;
  onAfterRename: () => Promise<void>;
  onLog: (line: string) => void;
};

const CASE_OPTIONS: { value: BulkRenameCaseMode; label: string }[] = [
  { value: "unchanged", label: "Inchangée" },
  { value: "lower", label: "minuscules" },
  { value: "upper", label: "MAJUSCULES" },
  { value: "title", label: "Titre" },
];

export function InspectorOutputTab({
  item,
  outputDir,
  backend,
  bridgeReady,
  actionsDisabled,
  onPickOutput,
  onAfterRename,
  onLog,
}: InspectorOutputTabProps) {
  const [prefix, setPrefix] = useState("");
  const [suffix, setSuffix] = useState("");
  const [caseMode, setCaseMode] = useState<BulkRenameCaseMode>("unchanged");
  const [plan, setPlan] = useState<BulkRenamePlanResult | null>(null);
  const [applying, setApplying] = useState(false);
  const [resolvedOutputPath, setResolvedOutputPath] = useState("");

  useEffect(() => {
    if (!backend || !bridgeReady) {
      setResolvedOutputPath(item.outputPath ?? "");
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const raw = await qtInvoke(() => backend.getInspectorOutputPath(item.sourcePath));
        const data = parseJson<InspectorOutputPathResult>(raw);
        if (!cancelled) {
          setResolvedOutputPath(data.ok && data.outputPath ? data.outputPath : "");
        }
      } catch {
        if (!cancelled) setResolvedOutputPath(item.outputPath ?? "");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [backend, bridgeReady, item.sourcePath, item.outputPath]);

  const outputPath = resolvedOutputPath;
  const hasOutput = Boolean(outputPath.trim());

  const refreshPlan = useCallback(async () => {
    if (!backend || !bridgeReady) {
      setPlan(null);
      return;
    }
    const raw = await qtInvoke(() =>
      backend.planBulkRename(
        JSON.stringify({ schemaVersion: "0", prefix, suffix, caseMode }),
      ),
    );
    setPlan(parseJson<BulkRenamePlanResult>(raw));
  }, [backend, bridgeReady, prefix, suffix, caseMode]);

  useEffect(() => {
    const t = window.setTimeout(() => {
      void refreshPlan().catch(() => setPlan(null));
    }, 200);
    return () => window.clearTimeout(t);
  }, [refreshPlan]);

  const onCopyPath = async () => {
    if (!backend || !outputPath) return;
    await qtInvoke(() => backend.copyText(outputPath));
    onLog("[INFO] chemin copié dans le presse-papiers");
  };

  const onOpenFolder = async () => {
    if (!backend) return;
    const raw = await qtInvoke(() => backend.openOutputParentFolder(item.sourcePath));
    const ack = parseJson<{ ok: boolean; message?: string }>(raw);
    if (!ack.ok) {
      onLog(`[WARN] ${ack.message ?? "Impossible d'ouvrir le dossier"}`);
    }
  };

  const onApplyBulk = async () => {
    if (!backend || !plan?.ok || !plan.operations.length) return;
    setApplying(true);
    try {
      const raw = await qtInvoke(() =>
        backend.applyBulkRename(
          JSON.stringify({ schemaVersion: "0", operations: plan.operations }),
        ),
      );
      const result = parseJson<BulkRenameApplyResult>(raw);
      if (!result.ok) {
        onLog(`[ERROR] ${result.message ?? "Renommage en lot échoué"}`);
        return;
      }
      onLog(`[INFO] ${result.renamedCount} fichier(s) renommé(s)`);
      await onAfterRename();
      await refreshPlan();
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="inspector-output">
      <p className="inspector-output__info">
        {hasOutput
          ? "Fichier Markdown produit. Copiez le chemin ou ouvrez son dossier parent."
          : "Aucun fichier Markdown n'est encore associé à cette entrée."}
      </p>

      <label className="inspector-field">
        <span className="inspector-field__label">Dossier de sortie</span>
        <div className="inspector-field__row">
          <span className="inspector-field__path" title={outputDir ?? undefined}>
            {outputDir ?? "—"}
          </span>
          <button
            type="button"
            className="btn btn--sm"
            disabled={!bridgeReady || actionsDisabled}
            onClick={onPickOutput}
          >
            Choisir…
          </button>
        </div>
      </label>

      <label className="inspector-field">
        <span className="inspector-field__label">Chemin du .md produit</span>
        <input
          type="text"
          className="inspector-field__input"
          readOnly
          value={outputPath}
          placeholder="—"
        />
      </label>

      <div className="inspector-output__actions">
        <button
          type="button"
          className="btn btn--sm"
          disabled={!bridgeReady || !hasOutput}
          onClick={() => void onCopyPath()}
        >
          Copier le chemin
        </button>
        <button
          type="button"
          className="btn btn--sm btn--ghost"
          disabled={!bridgeReady || !hasOutput}
          onClick={() => void onOpenFolder()}
        >
          Ouvrir le dossier
        </button>
      </div>

      <hr className="inspector-output__sep" />

      <h3 className="inspector-output__bulk-title">Renommage en lot (.md)</h3>
      <p className="inspector__hint">
        Préfixe, suffixe et casse s'appliquent à tous les fichiers convertis avec succès.
      </p>

      <div className="inspector-output__bulk-fields">
        <label className="inspector-field inspector-field--compact">
          <span className="inspector-field__label">Préfixe</span>
          <input
            type="text"
            className="inspector-field__input"
            value={prefix}
            disabled={actionsDisabled}
            onChange={(e) => setPrefix(e.target.value)}
          />
        </label>
        <label className="inspector-field inspector-field--compact">
          <span className="inspector-field__label">Suffixe</span>
          <input
            type="text"
            className="inspector-field__input"
            value={suffix}
            disabled={actionsDisabled}
            onChange={(e) => setSuffix(e.target.value)}
          />
        </label>
        <label className="inspector-field inspector-field--compact">
          <span className="inspector-field__label">Casse</span>
          <select
            className="inspector-field__select"
            value={caseMode}
            disabled={actionsDisabled}
            onChange={(e) => setCaseMode(e.target.value as BulkRenameCaseMode)}
          >
            {CASE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {plan?.errorMessage && (
        <p className="inspector-output__plan-error" role="alert">
          {plan.errorMessage}
        </p>
      )}

      {plan?.previewLines && plan.previewLines.length > 0 && (
        <ul className="inspector-output__preview">
          {plan.previewLines.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      )}

      <button
        type="button"
        className="btn"
        disabled={
          !bridgeReady ||
          actionsDisabled ||
          applying ||
          !plan?.ok ||
          !plan.operationCount
        }
        onClick={() => void onApplyBulk()}
      >
        {applying ? "Application…" : "Appliquer le renommage"}
      </button>
    </div>
  );
}
