import { NOT_REACHED } from "../api/types";

export function formatHash(value: string | null | undefined, keep = 10): string {
  if (!value) return "—";
  if (value.length <= keep * 2) return value;
  return `${value.slice(0, keep)}…${value.slice(-8)}`;
}

export function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KiB`;
  return `${(size / (1024 * 1024)).toFixed(2)} MiB`;
}

export function formatNumber(value: number | null | undefined, digits = 3): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  });
}

export function formatPercent(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value.toFixed(digits)}%`;
}

export function formatTimestamp(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toISOString().replace("T", " ").replace("Z", " UTC");
}

export function responseUnit(response: string): string {
  if (response === "u_max") return "mm";
  if (response === "sigma_max") return "N/mm²";
  if (response === "C") return "N·mm";
  return "";
}

export function variableUnit(variable: string): string {
  if (variable === "E") return "GPa";
  if (variable === "F") return "kN";
  if (variable.startsWith("A")) return "mm²";
  return "";
}

export function formatCrossing(value: string | null | undefined): string {
  if (!value || value === NOT_REACHED) return "Not reached within tested range";
  return `δ = ${value} (first observed grid crossing)`;
}

export function isReached(value: string | null | undefined): boolean {
  return Boolean(value) && value !== NOT_REACHED;
}

export function crossingSortValue(value: string | null | undefined): number {
  if (!isReached(value)) return Number.POSITIVE_INFINITY;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : Number.POSITIVE_INFINITY;
}
