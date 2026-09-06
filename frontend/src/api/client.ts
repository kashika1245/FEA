import type { ApiErrorBody } from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string;

  constructor(status: number, code: string, message: string, requestId: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

export function apiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL;
  if (typeof raw === "string" && raw.trim()) {
    return raw.replace(/\/$/, "");
  }
  return "";
}

function requestId(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("X-Request-ID", requestId());
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "NETWORK", "Unable to connect to research API.", "");
  }
  if (!response.ok) {
    let code = "HTTP_ERROR";
    let message = `Request failed with status ${response.status}.`;
    let rid = response.headers.get("X-Request-ID") ?? "";
    try {
      const body = (await response.json()) as ApiErrorBody;
      code = body.error.code;
      message = body.error.message;
      rid = body.error.request_id;
    } catch {
      /* envelope unavailable */
    }
    throw new ApiError(response.status, code, publicMessage(response.status, code, message), rid);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export function publicMessage(status: number, code: string, backendMessage: string): string {
  if (status === 0) return "Unable to connect to research API.";
  if (status === 404) return "Experiment not found.";
  if (status === 409 && code === "JOB_ALREADY_RUNNING") {
    return "This experiment already has an active run.";
  }
  if (status === 409 && code === "EXPERIMENT_IMMUTABLE") {
    return "Frozen Phase 2 artefacts cannot be overwritten.";
  }
  if (status === 409) return backendMessage || "The request conflicts with current experiment state.";
  if (status === 422) return backendMessage || "The request failed validation.";
  if (status === 403) return backendMessage || "This operation is not permitted.";
  if (status >= 500) return "The research API reported an unexpected error.";
  return backendMessage;
}

export function queryString(params: Record<string, string | number | undefined | null>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}
