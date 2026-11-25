import React from "react";

const STYLES: Record<string, string> = {
  critical: "bg-danger-container text-on-danger-container border-danger/30",
  high: "bg-warning-container text-on-warning-container border-warning/30",
  medium: "bg-info-container text-on-info-container border-info/30",
  low: "bg-success-container text-on-success-container border-success/30",
};

const DOT_STYLES: Record<string, string> = {
  critical: "bg-danger",
  high: "bg-warning",
  medium: "bg-info",
  low: "bg-success",
};

export function RiskBadge({ level }: { level: string }) {
  const key = (level || "low").toLowerCase();
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-[11px] font-medium uppercase tracking-wider ${
        STYLES[key] || STYLES.low
      }`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${DOT_STYLES[key] || DOT_STYLES.low}`} />
      {key}
    </span>
  );
}
