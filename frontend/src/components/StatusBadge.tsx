import { statusLabel } from "../lib/status";

export function StatusBadge({ status }: { status: string | null | undefined }) {
  const tone = status === "completed" || status === "ok" || status === "true"
    ? "ok"
    : status === "failed"
      ? "bad"
      : status === "running" || status === "queued" || status === "cancel_requested"
        ? "warn"
        : "steel";
  return (
    <span className={`badge ${tone}`}>
      <span className="sr-only">Status:</span>
      {statusLabel(status)}
    </span>
  );
}
