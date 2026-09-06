# Phase 4 security

- No `dangerouslySetInnerHTML`.
- Artifact downloads use opaque IDs from the API, URL-encoded.
- `VITE_API_BASE_URL` is an origin prefix only; no secrets in source.
- API errors are mapped; 500s do not show tracebacks.
- CORS is an explicit origin list, never `*`.
- No credentials stored in localStorage.
- Scientific modules were not modified.
