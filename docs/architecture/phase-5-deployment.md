# Phase 5 deployment boundary

The research API is a **trusted-network** service.

Protected:

- Artifact path confinement and opaque IDs
- Frozen Phase 2 immutability
- Input validation and generic error bodies
- Single-job lock and cooperative cancel
- CORS allow-list (no `*`)

Not protected:

- Identity of the caller
- Per-user authorization
- Internet exposure without a reverse proxy
- Sliding-window abuse control (counter is process-lifetime)

Deploy `uvicorn` behind an authenticated reverse proxy, VPN, or equivalent host firewall. Do not advertise this as a multi-user SaaS.
