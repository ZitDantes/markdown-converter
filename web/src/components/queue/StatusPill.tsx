import type { ConversionStatusValue } from "@shared/bridge-contract";
import { statusVisual } from "./statusStyles";

type StatusPillProps = {
  status: ConversionStatusValue;
  label: string;
  isDark: boolean;
};

export function StatusPill({ status, label, isDark }: StatusPillProps) {
  const m = statusVisual(status, isDark);
  return (
    <span className="status-pill" style={{ color: m.fg, background: m.bg }}>
      <span className="status-pill__dot" style={{ background: m.dot }} aria-hidden />
      {label}
    </span>
  );
}
