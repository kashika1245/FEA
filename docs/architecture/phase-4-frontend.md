# Phase 4 frontend architecture

Stack: React 19, TypeScript, Vite 7, React Router 7, TanStack Query 5.

There is no large UI kit. Layout, tables, badges, and charts are local components. Charts are SVG polylines/rects over stored API points (no smoothing library).

```
frontend/src/
  api/          typed client
  lib/          formatters, status, profile series mapping
  components/   shell, charts, picker
  pages/        one route per research surface
```

State: URL `?experiment=` plus React Query caches. Jobs poll every 2s only while a non-terminal job exists.

Environment: `VITE_API_BASE_URL` optional. Default is same-origin `/api` via the Vite proxy to `127.0.0.1:8000`.
