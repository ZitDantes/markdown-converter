import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "./components/layout/AppShell";
import { FooterBar } from "./components/layout/FooterBar";
import { InspectorPanel, type InspectorTab } from "./components/inspector/InspectorPanel";
import { LogDrawer } from "./components/layout/LogDrawer";
import { MainColumn } from "./components/layout/MainColumn";
import { ConversionQueue } from "./components/queue/ConversionQueue";
import type { ConversionMode } from "./components/toolbar/ConversionToolbar";
import { filterQueueItems } from "./lib/queueFilters";
import { normalizeLogLevel, parseLogLine, type LogEntry } from "./lib/logJournal";
import { useTheme } from "./theme/useTheme";
import {
  connectBackend,
  fetchQueueState,
  pingBackend,
  type ProgressEvent,
  type QueueState,
  type WebBackendBridge,
} from "./bridge";
import { parseJson, qtInvoke, type AckResult } from "@shared/bridge-contract";

type BridgeStatus = "loading" | "ready" | "error";
function countDone(items: QueueState["items"]): number {
  return items.filter((i) =>
    ["success", "success_review", "success_fallback"].includes(i.status),
  ).length;
}

export function App() {
  const { isDark, toggleTheme } = useTheme();
  const [status, setStatus] = useState<BridgeStatus>("loading");
  const [error, setError] = useState<string | null>(null);
  const [backend, setBackend] = useState<WebBackendBridge | null>(null);
  const [queue, setQueue] = useState<QueueState | null>(null);
  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);
  const [logFilePath, setLogFilePath] = useState<string | null>(null);
  const [batchPercent, setBatchPercent] = useState(0);
  const [conversionMode, setConversionMode] = useState<ConversionMode>("standard");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeExtensions, setActiveExtensions] = useState<Set<string>>(() => new Set());
  const [logOpen, setLogOpen] = useState(false);
  const [inspectorTab, setInspectorTab] = useState<InspectorTab>("preview");
  const [selectedPath, setSelectedPath] = useState<string | null>(null);

  const appendLog = useCallback((level: string, message: string) => {
    setLogEntries((prev) => [
      ...prev.slice(-500),
      { level: normalizeLogLevel(level), message },
    ]);
  }, []);

  const pushLog = useCallback(
    (line: string) => {
      const parsed = parseLogLine(line);
      appendLog(parsed.level, parsed.message);
    },
    [appendLog],
  );

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
          appendLog(level, message);
        });
        b.progressUpdated?.connect((progressJson) => {
          const ev = parseJson<ProgressEvent>(progressJson);
          setBatchPercent(ev.batchPercent);
        });
        b.queueUpdated?.connect((queueJson) => {
          const state = parseJson<QueueState>(queueJson);
          setQueue(state);
          setSelectedPath((prev) => {
            if (state.items.length === 0) return null;
            if (prev && state.items.some((i) => i.sourcePath === prev)) return prev;
            return state.items[0]?.sourcePath ?? null;
          });
        });
        b.conversionFinished?.connect(() => {
          setBatchPercent(1);
          void refreshQueue(b);
        });
        b.conversionFailed?.connect(() => {
          void refreshQueue(b);
        });

        setBackend(b);
        await refreshQueue(b);
        try {
          const rawPath = await qtInvoke(() => b.getLogFilePath());
          const pathDto = parseJson<{ path: string }>(rawPath);
          setLogFilePath(pathDto.path);
          appendLog("INFO", `Fichier de log : ${pathDto.path}`);
        } catch {
          appendLog("INFO", "Fichier de log : indisponible");
        }
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
  }, [appendLog, pushLog, refreshQueue]);

  const bridgeReady = status === "ready" && backend !== null;
  const items = queue?.items ?? [];
  const visibleItems = useMemo(
    () => filterQueueItems(items, activeExtensions, searchQuery),
    [items, activeExtensions, searchQuery],
  );
  const doneCount = useMemo(() => countDone(items), [items]);
  const selectedItem = useMemo(
    () => items.find((i) => i.sourcePath === selectedPath) ?? null,
    [items, selectedPath],
  );
  const isConverting = items.some((i) => i.status === "processing");
  const queueActionsDisabled = !bridgeReady || isConverting;
  const strictMode = conversionMode === "strict";

  const toggleExtension = useCallback((ext: string) => {
    setActiveExtensions((prev) => {
      const next = new Set(prev);
      if (next.has(ext)) next.delete(ext);
      else next.add(ext);
      return next;
    });
  }, []);

  const clearFilters = useCallback(() => {
    setActiveExtensions(new Set());
    setSearchQuery("");
  }, []);

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
    const modeLabel = strictMode ? "Strict" : "Standard";
    pushLog(`[INFO] conversion démarrée (mode ${modeLabel})`);
  };

  const onClear = async () => {
    if (!backend) return;
    await qtInvoke(() => backend.clearQueue());
    setSelectedPath(null);
    clearFilters();
    await refreshQueue(backend);
    pushLog("[INFO] file vidée");
  };

  const onRemoveItem = async (sourcePath: string) => {
    if (!backend) return;
    const raw = await qtInvoke(() => backend.removeQueueItem(sourcePath));
    const ack = parseJson<AckResult>(raw);
    if (!ack.ok) {
      pushLog(`[WARN] ${ack.message ?? "Retrait impossible"}`);
      return;
    }
    await refreshQueue(backend);
    pushLog("[INFO] fichier retiré de la file");
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
          items={items}
          isDark={isDark}
          bridgeReady={bridgeReady}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          activeExtensions={activeExtensions}
          onToggleExtension={toggleExtension}
          onClearFilters={clearFilters}
          conversionMode={conversionMode}
          onConversionModeChange={setConversionMode}
          onPickFiles={() => void onPickFiles()}
          onPickFolder={() => void onPickFolder()}
          onClear={() => void onClear()}
          onPickOutput={() => void onPickOutput()}
          queueList={
            <ConversionQueue
              visibleItems={visibleItems}
              totalCount={items.length}
              queue={queue}
              selectedPath={selectedPath}
              isDark={isDark}
              actionsDisabled={queueActionsDisabled}
              onSelect={setSelectedPath}
              onRemove={(path) => void onRemoveItem(path)}
            />
          }
        />
      }
      inspector={
        <InspectorPanel
          item={selectedItem}
          tab={inspectorTab}
          onTabChange={setInspectorTab}
          isDark={isDark}
          outputDir={queue?.outputDir ?? null}
          backend={backend}
          bridgeReady={bridgeReady}
          actionsDisabled={queueActionsDisabled}
          onPickOutput={() => void onPickOutput()}
          onAfterRename={async () => {
            if (backend) await refreshQueue(backend);
          }}
          onLog={pushLog}
        />
      }
      footer={
        <FooterBar
          batchPercent={batchPercent}
          itemCount={items.length}
          doneCount={doneCount}
          canConvert={queue?.canStartConversion ?? false}
          bridgeReady={bridgeReady}
          journalOpen={logOpen}
          onToggleJournal={() => setLogOpen((o) => !o)}
          onConvert={() => void onConvert()}
        />
      }
      logDrawer={
        <LogDrawer
          entries={logEntries}
          open={logOpen}
          logFilePath={logFilePath}
          onToggle={() => setLogOpen((o) => !o)}
          onOpenLogFile={
            backend
              ? () => {
                  void qtInvoke(() => backend.openLogFile());
                }
              : undefined
          }
        />
      }
    />
  );
}
