import { useCallback, useEffect, useState } from "react";
import {
  connectBackend,
  fetchQueueState,
  pingBackend,
  type ProgressEvent,
  type QueueState,
  type WebBackendBridge,
} from "./bridge";
import { parseJson, qtInvoke } from "@shared/bridge-contract";

type BridgeStatus = "loading" | "ready" | "error";

export function App() {
  const [status, setStatus] = useState<BridgeStatus>("loading");
  const [error, setError] = useState<string | null>(null);
  const [backend, setBackend] = useState<WebBackendBridge | null>(null);
  const [queue, setQueue] = useState<QueueState | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [batchPercent, setBatchPercent] = useState(0);
  const [strictMode, setStrictMode] = useState(false);

  const pushLog = useCallback((line: string) => {
    setLogs((prev) => [...prev.slice(-80), line]);
  }, []);

  const refreshQueue = useCallback(async (b: WebBackendBridge) => {
    const state = await fetchQueueState(b);
    setQueue(state);
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const b = await connectBackend();
        if (cancelled) return;
        const pong = await pingBackend(b, "démarrage");
        pushLog(`→ ping : ${pong}`);

        b.logEmitted?.connect((level, message) => {
          pushLog(`[${level}] ${message}`);
        });
        b.progressUpdated?.connect((progressJson) => {
          const ev = parseJson<ProgressEvent>(progressJson);
          setBatchPercent(ev.batchPercent);
        });
        b.queueUpdated?.connect((queueJson) => {
          setQueue(parseJson<QueueState>(queueJson));
        });
        b.conversionFinished?.connect((summaryJson) => {
          const ev = parseJson<{ summary: { records: { statusLabel: string }[] } }>(
            summaryJson,
          );
          const n = ev.summary.records.length;
          const ok = ev.summary.records.filter((r) => r.statusLabel.startsWith("OK")).length;
          pushLog(`→ conversion terminée : ${ok}/${n} fichier(s)`);
          setBatchPercent(1);
        });
        b.conversionFailed?.connect((message) => {
          pushLog(`→ échec : ${message}`);
        });

        setBackend(b);
        await refreshQueue(b);
        setStatus("ready");
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e));
          setStatus("error");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [pushLog, refreshQueue]);

  const onPickFiles = async () => {
    if (!backend) return;
    const raw = await qtInvoke(() => backend.pickFiles());
    pushLog(`→ fichiers ajoutés`);
    void raw;
  };

  const onPickFolder = async () => {
    if (!backend) return;
    await qtInvoke(() => backend.pickFolder());
    pushLog("→ dossier ajouté à la file");
  };

  const onPickOutput = async () => {
    if (!backend) return;
    const raw = await qtInvoke(() => backend.pickOutputDir());
    pushLog(`→ sortie : ${raw}`);
  };

  const onConvert = async () => {
    if (!backend) return;
    const cmd = JSON.stringify({
      schemaVersion: "0",
      useConversionFallback: !strictMode,
    });
    const raw = await qtInvoke(() => backend.startConversion(cmd));
    pushLog(`→ conversion : ${raw}`);
  };

  const onClear = async () => {
    if (!backend) return;
    await qtInvoke(() => backend.clearQueue());
    pushLog("→ file vidée");
  };

  return (
    <div className="app">
      <h1>Markdown Converter</h1>
      <p className="meta">Interface web locale (socle PLO-46)</p>

      <p className={`status ${status === "ready" ? "ok" : status === "error" ? "err" : ""}`}>
        {status === "loading" && "Connexion au pont…"}
        {status === "ready" && "Pont actif — prêt"}
        {status === "error" && `Erreur : ${error}`}
      </p>

      <div className="toolbar">
        <button type="button" disabled={!backend} onClick={() => void onPickFiles()}>
          Ajouter des fichiers
        </button>
        <button type="button" disabled={!backend} onClick={() => void onPickFolder()}>
          Ajouter un dossier
        </button>
        <button type="button" disabled={!backend} onClick={() => void onPickOutput()}>
          Dossier de sortie
        </button>
        <button type="button" disabled={!backend || !queue?.canStartConversion} onClick={() => void onConvert()}>
          Convertir
        </button>
        <button type="button" disabled={!backend} onClick={() => void onClear()}>
          Vider la file
        </button>
        <label>
          <input
            type="checkbox"
            checked={strictMode}
            onChange={(e) => setStrictMode(e.target.checked)}
            disabled={!backend}
          />{" "}
          Mode Strict
        </label>
      </div>

      <div className="panel">
        <h2>File</h2>
        {queue?.outputDir && <p className="meta">Sortie : {queue.outputDir}</p>}
        <ul className="queue-list">
          {(queue?.items ?? []).map((item) => (
            <li key={item.sourcePath}>
              {item.statusLabel} — {item.sourcePath.split("/").pop()}
            </li>
          ))}
          {(queue?.items.length ?? 0) === 0 && <li>Aucun fichier</li>}
        </ul>
        <div className="progress" aria-hidden>
          <span style={{ width: `${Math.round(batchPercent * 100)}%` }} />
        </div>
      </div>

      <div className="panel">
        <h2>Journal</h2>
        <pre className="log">{logs.join("\n") || "—"}</pre>
      </div>
    </div>
  );
}
