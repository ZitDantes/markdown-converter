import {
  BACKEND_OBJECT_NAME,
  type ProgressEvent,
  type QueueState,
  type WebBackendBridge,
  parseJson,
  qtInvoke,
} from "@shared/bridge-contract";

export type { QueueState, ProgressEvent, WebBackendBridge };

declare const QWebChannel: new (
  transport: unknown,
  callback: (channel: { objects: Record<string, WebBackendBridge> }) => void,
) => void;

export async function connectBackend(): Promise<WebBackendBridge> {
  if (typeof qt === "undefined") {
    throw new Error("QWebChannel indisponible (hors WebEngine ?)");
  }

  return new Promise((resolve, reject) => {
    new QWebChannel(qt.webChannelTransport, (channel) => {
      const backend = channel.objects[BACKEND_OBJECT_NAME];
      if (!backend) {
        reject(new Error(`Objet « ${BACKEND_OBJECT_NAME} » absent du pont`));
        return;
      }
      resolve(backend);
    });
  });
}

export async function fetchQueueState(backend: WebBackendBridge): Promise<QueueState> {
  const raw = await qtInvoke(() => backend.getQueueState());
  return parseJson<QueueState>(raw);
}

export async function pingBackend(backend: WebBackendBridge, message: string): Promise<string> {
  return qtInvoke(() => backend.ping(message));
}
