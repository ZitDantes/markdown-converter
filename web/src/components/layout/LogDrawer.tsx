import { useMemo, useState } from "react";

type LogLine = { text: string; level?: string };

type LogDrawerProps = {
  lines: string[];
  open: boolean;
  onToggle: () => void;
};

function parseLine(raw: string): LogLine {
  const m = raw.match(/^\[(INFO|WARN|ERROR|OK)\]\s*(.*)$/i);
  if (m) return { level: m[1].toLowerCase(), text: m[2] };
  return { text: raw };
}

export function LogDrawer({ lines, open, onToggle }: LogDrawerProps) {
  const [filter, setFilter] = useState<"all" | "info" | "warn" | "error">("all");
  const parsed = useMemo(() => lines.map(parseLine), [lines]);

  const filtered = parsed.filter((l) => {
    if (filter === "all") return true;
    if (filter === "info") return !l.level || l.level === "info" || l.level === "ok";
    return l.level === filter;
  });

  return (
    <section className={`log-drawer${open ? " log-drawer--open" : ""}`}>
      <button type="button" className="log-drawer__toggle" onClick={onToggle} aria-expanded={open}>
        <span className="log-drawer__chevron" aria-hidden>{open ? "▾" : "▸"}</span>
        Journal · {lines.length} entrée{lines.length !== 1 ? "s" : ""}
      </button>
      {open && (
        <div className="log-drawer__body">
          <div className="log-drawer__filters" role="tablist" aria-label="Filtrer le journal">
            {(
              [
                ["all", "Tout"],
                ["info", "Info"],
                ["warn", "Warn"],
                ["error", "Error"],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={filter === id}
                className={`log-drawer__filter${filter === id ? " log-drawer__filter--active" : ""}`}
                onClick={() => setFilter(id)}
              >
                {label}
              </button>
            ))}
          </div>
          <pre className="log-drawer__log">
            {filtered.length > 0
              ? filtered.map((l, i) => (
                  <div key={i} className={l.level ? `log-line log-line--${l.level}` : "log-line"}>
                    {l.text}
                  </div>
                ))
              : "—"}
          </pre>
        </div>
      )}
    </section>
  );
}
