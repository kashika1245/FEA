import type { JobStatus } from "../api/types";

export const TERMINAL_STATUSES: readonly JobStatus[] = ["completed", "failed", "cancelled"];

export function isTerminal(status: string | null | undefined): boolean {
  return status === "completed" || status === "failed" || status === "cancelled";
}

export function statusLabel(status: string | null | undefined): string {
  if (!status) return "Unknown";
  return status.replaceAll("_", " ");
}

export function experimentKind(experimentId: string): string {
  if (experimentId.startsWith("paper-a.phase2.")) return "Frozen Phase 2";
  if (experimentId.startsWith("paper-a.phase3.")) return "Phase 3 run";
  return "Experiment";
}
