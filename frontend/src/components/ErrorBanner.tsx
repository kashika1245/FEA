import { ApiError } from "../api/client";

export function ErrorBanner({ error }: { error: unknown }) {
  if (!error) return null;
  const api = error instanceof ApiError ? error : null;
  return (
    <div className="alert" role="alert">
      <strong>{api ? titleFor(api.status) : "Request failed."}</strong>
      <div>{api ? api.message : "Unable to load research data."}</div>
      {api?.requestId ? <div className="mono">request {api.requestId}</div> : null}
    </div>
  );
}

function titleFor(status: number): string {
  if (status === 0) return "Unable to connect to research API.";
  if (status === 404) return "Experiment not found.";
  if (status === 409) return "Request conflict.";
  if (status === 422) return "Validation error.";
  if (status >= 500) return "Unexpected API error.";
  return "API error.";
}
