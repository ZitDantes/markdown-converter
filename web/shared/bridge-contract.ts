/**
 * Contrat pont WebChannel v0 (PLO-45).
 * Miroir de `bridge_contract/models.py` — voir docs/adr/0001-contrat-pont-webchannel-js-python.md
 */

export const SCHEMA_VERSION = "0" as const;
export const BACKEND_OBJECT_NAME = "backend" as const;

export type SchemaVersion = typeof SCHEMA_VERSION;

/** Valeurs alignées sur `converter.ConversionStatus` */
export type ConversionStatusValue =
  | "success"
  | "success_review"
  | "success_fallback"
  | "error"
  | "unsupported"
  | "empty"
  | "processing"
  | "queued";

export interface FileQueueItem {
  sourcePath: string;
  status: ConversionStatusValue;
  /** Libellé français fourni par Python (PLO-33) */
  statusLabel: string;
  progressPercent: number;
  outputPath?: string | null;
  message?: string | null;
}

export interface QueueState {
  schemaVersion: SchemaVersion;
  items: FileQueueItem[];
  outputDir: string | null;
  canStartConversion: boolean;
}

export interface ProgressEvent {
  schemaVersion: SchemaVersion;
  fileIndex: number;
  fileTotal: number;
  fileLabel: string;
  batchPercent: number;
}

export interface ConversionSummaryDto {
  schemaVersion: SchemaVersion;
  startedAt: string;
  finishedAt: string;
  outputDir: string;
  records: FileQueueItem[];
  unsupportedSkipped: string[];
  warnings: string[];
}

export interface ConversionFinishedEvent {
  schemaVersion: SchemaVersion;
  summary: ConversionSummaryDto;
}

/** `true` = mode Standard (secours autorisé), `false` = Strict (PLO-40) */
export interface StartConversionCommand {
  schemaVersion?: SchemaVersion;
  useConversionFallback: boolean;
}

export interface AckResult {
  schemaVersion: SchemaVersion;
  ok: boolean;
  message?: string | null;
}

export interface PickFilesResult {
  schemaVersion: SchemaVersion;
  paths: string[];
  cancelled: boolean;
}

export interface PickFolderResult {
  schemaVersion: SchemaVersion;
  path: string | null;
  cancelled: boolean;
}

export interface SetOutputDirResult {
  schemaVersion: SchemaVersion;
  ok: boolean;
  outputDir: string | null;
  errorMessage?: string | null;
}

export interface ClearQueueResult {
  schemaVersion: SchemaVersion;
  clearedCount: number;
}

/**
 * Appels @Slot Qt 6 : retour souvent une Promise.
 * Usage : `await qtInvoke(() => backend.pickFiles())` puis `JSON.parse`.
 */
export type QtInvokeResult<T> = T | Promise<T>;

export function qtInvoke<T>(callable: () => QtInvokeResult<T>): Promise<T> {
  const value = callable();
  if (value && typeof (value as Promise<T>).then === "function") {
    return value as Promise<T>;
  }
  return Promise.resolve(value);
}

export function parseJson<T>(raw: string): T {
  return JSON.parse(raw) as T;
}

/** Objet exposé par QWebChannel (méthodes = commandes, propriétés = signaux) */
export interface WebBackendBridge {
  ping(message: string): QtInvokeResult<string>;
  pickFiles(): QtInvokeResult<string>;
  pickFolder(): QtInvokeResult<string>;
  setOutputDir(path: string): QtInvokeResult<string>;
  getQueueState(): QtInvokeResult<string>;
  clearQueue(): QtInvokeResult<string>;
  startConversion(commandJson: string): QtInvokeResult<string>;
  cancelConversion(): QtInvokeResult<string>;

  logEmitted?: { connect(cb: (level: string, message: string) => void): void };
  progressUpdated?: { connect(cb: (progressJson: string) => void): void };
  queueUpdated?: { connect(cb: (queueJson: string) => void): void };
  conversionFinished?: { connect(cb: (summaryJson: string) => void): void };
  conversionFailed?: { connect(cb: (message: string) => void): void };
}
