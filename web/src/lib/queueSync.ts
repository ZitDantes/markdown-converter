import type {
  ConversionFinishedEvent,
  ConversionStatusValue,
  ConversionSummaryDto,
  FileQueueItem,
  QueueState,
  WebBackendBridge,
} from "@shared/bridge-contract";
import { parseJson, qtInvoke } from "@shared/bridge-contract";

const TERMINAL: ConversionStatusValue[] = [
  "success",
  "success_review",
  "success_fallback",
  "error",
  "empty",
  "unsupported",
];

export function pathKey(sourcePath: string): string {
  return sourcePath;
}

export function parseJsonValue<T>(raw: string | T): T {
  if (typeof raw === "string") {
    return parseJson<T>(raw);
  }
  return raw;
}

export function isTerminalStatus(status: ConversionStatusValue): boolean {
  return TERMINAL.includes(status);
}

export function computeBatchPercent(state: QueueState): number {
  if (state.items.length === 0) return 0;
  const sum = state.items.reduce((acc, item) => acc + item.progressPercent, 0);
  return Math.max(0, Math.min(1, sum / state.items.length));
}

const SUCCESS: ConversionStatusValue[] = ["success", "success_review", "success_fallback"];

export function countConversionResults(items: FileQueueItem[]): {
  ok: number;
  err: number;
} {
  let ok = 0;
  let err = 0;
  for (const item of items) {
    if (SUCCESS.includes(item.status)) {
      ok += 1;
    } else if (item.status === "error" || item.status === "empty") {
      err += 1;
    }
  }
  return { ok, err };
}

/**
 * Fusionne les enregistrements du résumé de conversion dans l'état de file actuel.
 */
export function mergeSummaryIntoQueue(
  queue: QueueState,
  summary: ConversionSummaryDto,
): QueueState {
  const byPath = new Map(summary.records.map((r) => [pathKey(r.sourcePath), r]));
  const merged: FileQueueItem[] = queue.items.map((item) => {
    const hit = byPath.get(pathKey(item.sourcePath));
    return hit ?? item;
  });
  for (const rec of summary.records) {
    const key = pathKey(rec.sourcePath);
    if (!merged.some((i) => pathKey(i.sourcePath) === key)) {
      merged.push(rec);
    }
  }
  return { ...queue, items: merged };
}

export function parseConversionFinishedPayload(
  raw: string | ConversionFinishedEvent,
): ConversionFinishedEvent {
  return parseJsonValue<ConversionFinishedEvent>(raw);
}

/**
 * Attend la fin du lot en interrogeant ``getQueueState`` (fiable sous WebEngine).
 * Les signaux ``conversionFinished`` / ``conversionFailed`` peuvent accélérer la fin
 * si le navigateur les reçoit ; le polling reste la source de vérité pour l’UI.
 */
export async function waitForConversionIdle(
  backend: WebBackendBridge,
  onUpdate: (state: QueueState) => void,
  options?: { intervalMs?: number; timeoutMs?: number },
): Promise<QueueState> {
  const intervalMs = options?.intervalMs ?? 200;
  const maxWaitMs = options?.timeoutMs ?? 300_000;
  const hasSignals =
    Boolean(backend.conversionFinished?.connect) &&
    Boolean(backend.conversionFailed?.connect);

  if (!hasSignals) {
    return pollQueueUntilIdle(backend, onUpdate, { intervalMs, maxWaitMs });
  }

  return new Promise((resolve, reject) => {
    let settled = false;
    let pollTimer: ReturnType<typeof setInterval> | null = null;

    const finish = (state: QueueState) => {
      if (settled) return;
      settled = true;
      if (pollTimer !== null) {
        window.clearInterval(pollTimer);
      }
      window.clearTimeout(safetyTimer);
      finishedSignal.disconnect?.(onFinished);
      failedSignal.disconnect?.(onFailed);
      resolve(state);
    };

    const pollOnce = () => {
      void qtInvoke(() => backend.getQueueState())
        .then((raw) => {
          if (settled) return;
          const state = parseJsonValue<QueueState>(raw);
          onUpdate(state);
          const anyTerminal = state.items.some((i) => isTerminalStatus(i.status));
          const stillRunning = state.items.some(
            (i) => i.status === "queued" || i.status === "processing",
          );
          if (anyTerminal && !stillRunning && state.items.length > 0) {
            finish(state);
          }
        })
        .catch(reject);
    };

    pollOnce();
    pollTimer = window.setInterval(pollOnce, intervalMs);

    const safetyTimer = window.setTimeout(() => {
      if (settled) return;
      void pollQueueUntilIdle(backend, onUpdate, { intervalMs, maxWaitMs: 5_000 })
        .then(finish)
        .catch(reject);
    }, maxWaitMs);

    const finishedSignal = backend.conversionFinished!;
    const failedSignal = backend.conversionFailed!;
    const onFinished = () => pollOnce();
    const onFailed = () => pollOnce();
    finishedSignal.connect(onFinished);
    failedSignal.connect(onFailed);
  });
}

/**
 * Interroge ``getQueueState`` jusqu'à la fin du lot (repli de secours).
 */
export async function pollQueueUntilIdle(
  backend: WebBackendBridge,
  onUpdate: (state: QueueState) => void,
  options?: { intervalMs?: number; maxWaitMs?: number },
): Promise<QueueState> {
  const intervalMs = options?.intervalMs ?? 200;
  const maxWaitMs = options?.maxWaitMs ?? 300_000;
  const started = Date.now();
  let last: QueueState | null = null;

  while (Date.now() - started < maxWaitMs) {
    const raw = await qtInvoke(() => backend.getQueueState());
    const state = parseJsonValue<QueueState>(raw);
    last = state;
    onUpdate(state);

    const anyTerminal = state.items.some((i) => isTerminalStatus(i.status));
    const stillRunning = state.items.some(
      (i) => i.status === "queued" || i.status === "processing",
    );
    if (anyTerminal && !stillRunning) {
      return state;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  if (last) {
    return last;
  }
  const raw = await qtInvoke(() => backend.getQueueState());
  const state = parseJsonValue<QueueState>(raw);
  onUpdate(state);
  return state;
}
