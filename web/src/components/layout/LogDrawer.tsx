import { useEffect, useMemo, useRef, useState } from "react";
import {
  countByFilter,
  filterLogEntries,
  logLineClass,
  logPrefix,
  type LogEntry,
  type LogFilter,
} from "../../lib/logJournal";

type LogDrawerProps = {
  entries: LogEntry[];
  open: boolean;
  onToggle: () => void;
  onOpenLogFile?: () => void;
  logFilePath?: string | null;
};

const FILTER_OPTIONS: { id: LogFilter; label: string }[] = [
  { id: "all", label: "Tout" },
  { id: "info", label: "Info" },
  { id: "warn", label: "Warn" },
  { id: "error", label: "Error" },
];

export function LogDrawer({ entries, open, onToggle, onOpenLogFile, logFilePath }: LogDrawerProps) {
  const [filter, setFilter] = useState<LogFilter>("all");
  const logEndRef = useRef<HTMLDivElement>(null);
  const counts = useMemo(() => countByFilter(entries), [entries]);
  const visible = useMemo(() => filterLogEntries(entries, filter), [entries, filter]);

  useEffect(() => {
    if (open) {
      logEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [open, entries.length, filter]);

  return (
    <section className={`log-drawer${open ? " log-drawer--open" : ""}`} aria-label="Journal">
      <div className="log-drawer__header">
        <button
          type="button"
          className="log-drawer__toggle"
          onClick={onToggle}
          aria-expanded={open}
        >
          <span className="log-drawer__chevron" aria-hidden>
            {open ? "▾" : "▸"}
          </span>
          <span>Journal</span>
          <span className="log-drawer__count">
            {entries.length} entrée{entries.length !== 1 ? "s" : ""}
          </span>
        </button>
        {open && (
          <div className="log-drawer__header-tools">
            <div className="log-drawer__filters" role="tablist" aria-label="Filtrer le journal">
              {FILTER_OPTIONS.map(({ id, label }) => (
                <button
                  key={id}
                  type="button"
                  role="tab"
                  aria-selected={filter === id}
                  className={`log-drawer__filter${filter === id ? " log-drawer__filter--active" : ""}`}
                  onClick={() => setFilter(id)}
                >
                  {label} ({counts[id]})
                </button>
              ))}
            </div>
            {onOpenLogFile && (
              <button type="button" className="log-drawer__open-file" onClick={onOpenLogFile}>
                Ouvrir le fichier de log
              </button>
            )}
          </div>
        )}
      </div>
      {open && (
        <div className="log-drawer__body">
          {logFilePath && (
            <p className="log-drawer__path" title={logFilePath}>
              Fichier de log : {logFilePath}
            </p>
          )}
          <pre className="log-drawer__log" aria-live="polite">
            {visible.length > 0 ? (
              visible.map((entry, i) => (
                <div key={`${i}-${entry.message.slice(0, 24)}`} className={logLineClass(entry.level)}>
                  <span className="log-line__prefix">{logPrefix(entry.level)}</span>
                  {entry.message}
                </div>
              ))
            ) : (
              <span className="log-drawer__empty">Aucun message pour ce filtre.</span>
            )}
            <div ref={logEndRef} />
          </pre>
        </div>
      )}
    </section>
  );
}
