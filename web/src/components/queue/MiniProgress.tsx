import type { ConversionStatusValue } from "@shared/bridge-contract";
import { isSuccessLike } from "./statusStyles";

const BAR: Partial<Record<ConversionStatusValue, string>> = {
  queued: "var(--mc-progress-queued)",
  processing: "#0b8af0",
  success: "var(--mc-progress-ok)",
  success_review: "#d18900",
  success_fallback: "#0b66c2",
  empty: "#a67d24",
  error: "#b00020",
  unsupported: "var(--mc-progress-queued)",
};

type MiniProgressProps = {
  value: number;
  status: ConversionStatusValue;
};

export function MiniProgress({ value, status }: MiniProgressProps) {
  const v = status === "processing" ? Math.max(0.04, value) : value;
  const pct = Math.round(Math.max(0, Math.min(1, v)) * 100);
  return (
    <div className="mini-progress" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
      <span className="mini-progress__fill" style={{ width: `${pct}%`, background: BAR[status] ?? "#0b8af0" }} />
    </div>
  );
}

export function progressHint(
  status: ConversionStatusValue,
  outputPath: string | null | undefined,
): string {
  if (status === "error") return "—";
  if (status === "empty") return "aucun .md";
  if (status === "unsupported") return "ignoré";
  if (isSuccessLike(status) && outputPath) {
    const name = outputPath.split("/").pop() ?? outputPath;
    return `→ ${name}`;
  }
  return "→ .md";
}
