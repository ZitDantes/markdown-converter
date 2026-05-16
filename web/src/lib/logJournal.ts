/** Journal de conversion — aligné sur ``ui_qt_journal`` / ``ui.LEVEL_*``. */

export type LogLevel = "INFO" | "WARNING" | "ERROR" | "OK" | "UNKNOWN";

export type LogEntry = {
  level: LogLevel;
  message: string;
};

export type LogFilter = "all" | "info" | "warn" | "error";

const LEVEL_PREFIX: Record<LogLevel, string> = {
  INFO: "[INFO] ",
  WARNING: "[WARN] ",
  ERROR: "[ERROR] ",
  OK: "[OK] ",
  UNKNOWN: "",
};

export function normalizeLogLevel(raw: string): LogLevel {
  const u = raw.trim().toUpperCase();
  if (u === "WARN" || u === "WARNING") return "WARNING";
  if (u === "INFO") return "INFO";
  if (u === "ERROR") return "ERROR";
  if (u === "OK") return "OK";
  return "UNKNOWN";
}

export function parseLogLine(raw: string): LogEntry {
  const m = raw.match(/^\[(INFO|WARNING|WARN|ERROR|OK)\]\s*(.*)$/i);
  if (m) {
    return { level: normalizeLogLevel(m[1]), message: m[2] };
  }
  return { level: "UNKNOWN", message: raw };
}

export function logPrefix(level: LogLevel): string {
  return LEVEL_PREFIX[level] ?? "";
}

export function countByFilter(entries: LogEntry[]): Record<LogFilter, number> {
  const counts: Record<LogFilter, number> = {
    all: entries.length,
    info: 0,
    warn: 0,
    error: 0,
  };
  for (const e of entries) {
    if (e.level === "INFO" || e.level === "OK") counts.info += 1;
    if (e.level === "WARNING") counts.warn += 1;
    if (e.level === "ERROR") counts.error += 1;
  }
  return counts;
}

export function filterLogEntries(entries: LogEntry[], filter: LogFilter): LogEntry[] {
  if (filter === "all") return entries;
  if (filter === "info") {
    return entries.filter((e) => e.level === "INFO" || e.level === "OK");
  }
  if (filter === "warn") {
    return entries.filter((e) => e.level === "WARNING");
  }
  return entries.filter((e) => e.level === "ERROR");
}

export function logLineClass(level: LogLevel): string {
  if (level === "WARNING") return "log-line log-line--warn";
  if (level === "ERROR") return "log-line log-line--error";
  if (level === "OK") return "log-line log-line--ok";
  return "log-line log-line--info";
}
