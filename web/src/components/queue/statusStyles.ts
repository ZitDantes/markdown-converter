import type { ConversionStatusValue } from "@shared/bridge-contract";

export type StatusVisual = { fg: string; bg: string; dot: string };

const LIGHT: Record<string, StatusVisual> = {
  queued: { fg: "#5c6370", bg: "rgba(120,130,145,0.14)", dot: "#9aa3b2" },
  processing: { fg: "#0b66c2", bg: "rgba(11,102,194,0.13)", dot: "#0b66c2" },
  success: { fg: "#1f8a4c", bg: "rgba(31,138,76,0.13)", dot: "#1f8a4c" },
  success_review: { fg: "#b06a00", bg: "rgba(176,106,0,0.14)", dot: "#d18900" },
  success_fallback: { fg: "#0b66c2", bg: "rgba(11,102,194,0.13)", dot: "#0b66c2" },
  empty: { fg: "#7a5400", bg: "rgba(122,84,0,0.14)", dot: "#a67d24" },
  error: { fg: "#b00020", bg: "rgba(176,0,32,0.13)", dot: "#b00020" },
  unsupported: { fg: "#6b7280", bg: "rgba(107,114,128,0.13)", dot: "#9aa3b2" },
} as unknown as Record<string, StatusVisual>;

const DARK: Record<string, StatusVisual> = {
  queued: { fg: "#a9b2c0", bg: "rgba(160,170,190,0.16)", dot: "#a9b2c0" },
  processing: { fg: "#7eb3ff", bg: "rgba(126,179,255,0.18)", dot: "#7eb3ff" },
  success: { fg: "#7adc9d", bg: "rgba(122,220,157,0.18)", dot: "#7adc9d" },
  success_review: { fg: "#f5c97b", bg: "rgba(245,201,123,0.18)", dot: "#f5c97b" },
  success_fallback: { fg: "#7eb3ff", bg: "rgba(126,179,255,0.18)", dot: "#7eb3ff" },
  empty: { fg: "#e8b860", bg: "rgba(232,184,96,0.16)", dot: "#e8b860" },
  error: { fg: "#ff8a80", bg: "rgba(255,138,128,0.18)", dot: "#ff8a80" },
  unsupported: { fg: "#a9b2c0", bg: "rgba(160,170,190,0.16)", dot: "#a9b2c0" },
};

export function statusVisual(status: ConversionStatusValue, isDark: boolean): StatusVisual {
  const map = isDark ? DARK : LIGHT;
  return map[status] ?? map.queued;
}

export function isSuccessLike(status: ConversionStatusValue): boolean {
  return (
    status === "success" ||
    status === "success_review" ||
    status === "success_fallback"
  );
}

export function isUnsupportedLike(status: ConversionStatusValue): boolean {
  return status === "unsupported";
}
