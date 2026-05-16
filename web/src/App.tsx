import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "./components/layout/AppShell";
import { FooterBar } from "./components/layout/FooterBar";
import { InspectorPanel } from "./components/layout/InspectorPanel";
import { LogDrawer } from "./components/layout/LogDrawer";
import { MainColumn } from "./components/layout/MainColumn";
import { useTheme } from "./theme/useTheme";
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
type InspectorTab = "preview" | "output" | "details";

function countDone(items: QueueState["items"]): number {
  return items.filter((i) =>
    ["success", "success_review", "success_fallback"].includes(i.status),
  ).length;
}

function QueueListBody({
  items,
  selectedPath,
  onSelect,
}: {
  items: QueueState["items"];
  selectedPath: string | null;
  onSelect: (path: string) => void;
}) {
  if (items.length === 0) {
    return (
      <p className="queue-empty">
        Glissez-déposez des fichiers ou utilisez Fichiers / Dossier (parité DnD — PLO-53).
      </p>
    );
  }

  return (
    <ul className="queue-list">
      {items.map((item) => {
        const name = item.sourcePath.split("/").pop() ?? item.sourcePath;
        const selected = item.sourcePath === selectedPath;
        return (
          <li
            key={item.sourcePath}
            className={`queue-list__item${selected ? " queue-list__item--selected" : ""}`}
            onClick={() => onSelect(item.sourcePath)}
          >
            <div className="queue-list__name">{name}</div>
            <div className="queue-list__status">{item.statusLabel}</div>
          </li>
        );
      })}
    </ul>
  );
}

export function App() {
  const { isDark, toggleTheme } = useTheme();
  const [status, setStatus] = useState<BridgeStatus>("loading");
  const [error, setError] = useState<string | null>(null);
  const [backend, setBackend] = useState<WebBackendBridge | null>(null);
  const [queue, setQueue] = useState<QueueState | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [batchPercent, setBatchPercent] = useState(0);
  const strictMode = false; /* modes Standard/Strict — PLO-50 */
  const [logOpen, setLogOpen] = useState(false);
  const [inspectorTab, setInspectorTab] = useState<InspectorTab>("preview");
  const [selectedPath, setSelectedPath] = useState<string | null>(null);

  const pushLog = useCallback((line: string) => {
    setLogs((prev) => [...prev.slice(-200), line]);
  }, []);

  const refreshQueue = useCallback(async (b: WebBackendBridge) => {
    const state = await fetchQueueState(b);
    setQueue(state);
    setSelectedPath((prev) => {
      if (state.items.length === 0) return null;
      if (prev && state.items.some((i) => i.sourcePath === prev)) return prev;
      return state.items[0]?.sourcePath ?? null;
    });
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const b = await connectBackend();
        if (cancelled) return;
        const pong = await pingBackend(b, "démarrage");
        pushLog(`[INFO] ping : ${pong}`);

        b.logEmitted?.connect((level, message) => {
          pushLog(`[${level.toUpperCase()}] ${message}`);
        });
        b.progressUpdated?.connect((progressJson) => {
          const ev = parseJson<ProgressEvent>(progressJson);
          setBatchPercent(ev.batchPercent);
        });
        b.queueUpdated?.connect((queueJson) => {
          const state = parseJson<QueueState>(queueJson);
          setQueue(state);
        });
        b.conversionFinished?.connect((summaryJson) => {
          const ev = parseJson<{ summary: { records: { statusLabel: string }[] } }>(summaryJson);
          const n = ev.summary.records.length;
          const ok = ev.summary.records.filter((r) => r.statusLabel.startsWith("OK")).length;
          pushLog(`[INFO] conversion terminée : ${ok}/${n} fichier(s)`);
          setBatchPercent(1);
        });
        b.conversionFailed?.connect((message) => {
          pushLog(`[ERROR] ${message}`);
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

  const bridgeReady = status === "ready" && backend !== null;
  const items = queue?.items ?? [];
  const doneCount = useMemo(() => countDone(items), [items]);

  const onPickFiles = async () => {
    if (!backend) return;
    await qtInvoke(() => backend.pickFiles());
    await refreshQueue(backend);
    pushLog("[INFO] fichiers ajoutés");
  };

  const onPickFolder = async () => {
    if (!backend) return;
    await qtInvoke(() => backend.pickFolder());
    await refreshQueue(backend);
    pushLog("[INFO] dossier ajouté à la file");
  };

  const onPickOutput = async () => {
    if (!backend) return;
    const raw = await qtInvoke(() => backend.pickOutputDir());
    pushLog(`[INFO] sortie : ${raw}`);
    await refreshQueue(backend);
  };

  const onConvert = async () => {
    if (!backend) return;
    setLogOpen(true);
    const cmd = JSON.stringify({
      schemaVersion: "0",
      useConversionFallback: !strictMode,
    });
    await qtInvoke(() => backend.startConversion(cmd));
    pushLog("[INFO] conversion démarrée");
  };

  const onClear = async () => {
    if (!backend) return;
    await qtInvoke(() => backend.clearQueue());
    setSelectedPath(null);
    await refreshQueue(backend);
    pushLog("[INFO] file vidée");
  };

  return (
    <AppShell
      isDark={isDark}
      onToggleTheme={toggleTheme}
      bridgeStatus={status}
      bridgeError={error}
      main={
        <MainColumn
          queue={queue}
          bridgeReady={bridgeReady}
          onPickFiles={() => void onPickFiles()}
          onPickFolder={() => void onPickFolder()}
          onClear={() => void onClear()}
          onPickOutput={() => void onPickOutput()}
          queueList={
            <QueueListBody
              items={items}
              selectedPath={selectedPath}
              onSelect={setSelectedPath}
            />
          }
        />
      }
      inspector={
        <InspectorPanel
          tab={inspectorTab}
          onTabChange={setInspectorTab}
          hasSelection={selectedPath !== null}
        />
      }
      footer={
        <FooterBar
          batchPercent={batchPercent}
          itemCount={items.length}
          doneCount={doneCount}
          canConvert={queue?.canStartConversion ?? false}
          bridgeReady={bridgeReady}
          onConvert={() => void onConvert()}
        />
      }
      logDrawer={
        <LogDrawer lines={logs} open={logOpen} onToggle={() => setLogOpen((o) => !o)} />
      }
    />
  );
}
