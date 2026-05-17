import type { QtWebChannelSignal, WebBackendBridge } from "@shared/bridge-contract";

const REQUIRED_SIGNAL_NAMES = [
  "logEmitted",
  "progressUpdated",
  "queueUpdated",
  "conversionFinished",
  "conversionFailed",
  "dropOverlayVisible",
  "pathsAdded",
] as const;

type RequiredBackendSignalName = (typeof REQUIRED_SIGNAL_NAMES)[number];

function isQWebChannelReady(): boolean {
  return typeof (globalThis as { QWebChannel?: unknown }).QWebChannel !== "undefined";
}

/** Attend que ``qwebchannel.js`` (Qt) ait défini ``QWebChannel`` global. */
export function waitForQWebChannelScript(timeoutMs = 10_000): Promise<void> {
  if (isQWebChannelReady()) {
    return Promise.resolve();
  }
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + timeoutMs;
    const tick = () => {
      if (isQWebChannelReady()) {
        resolve();
        return;
      }
      if (Date.now() >= deadline) {
        reject(new Error("QWebChannel : délai d’attente du script Qt dépassé."));
        return;
      }
      window.setTimeout(tick, 16);
    };
    tick();
  });
}

export function assertBackendSignals(backend: WebBackendBridge): void {
  const missing: string[] = [];
  for (const name of REQUIRED_SIGNAL_NAMES) {
    const signal = backend[name] as QtWebChannelSignal<(...args: never[]) => void> | undefined;
    if (!signal?.connect) {
      missing.push(name);
    }
  }
  if (missing.length > 0) {
    throw new Error(
      `Signaux QWebChannel manquants sur « backend » : ${missing.join(", ")}`,
    );
  }
}

export function connectBackendSignal<T extends RequiredBackendSignalName>(
  backend: WebBackendBridge,
  name: T,
  handler: NonNullable<WebBackendBridge[T]> extends QtWebChannelSignal<infer C>
    ? C
    : never,
): void {
  const signal = backend[name] as QtWebChannelSignal<(...args: never[]) => void> | undefined;
  if (!signal?.connect) {
    throw new Error(`Signal QWebChannel « ${name} » indisponible.`);
  }
  signal.connect(handler as (...args: never[]) => void);
}
