# Phase 5 frontend audit

## Security search (source)

| Pattern | Result |
| --- | --- |
| `dangerouslySetInnerHTML` | None |
| `innerHTML` / `eval` / `new Function` / `document.write` | None |
| `localStorage` / `sessionStorage` | None |
| Artifact download | `encodeURIComponent` on opaque IDs |
| Experiment ID in URL | query param, selected from API list |

## Scientific UX defects fixed

Missing threshold cells are no longer labeled “Not reached”. IQR bands are not drawn on the wrong metric. Seeds are a closed list.

## Loading / errors

Pages show skeletons while loading and `ErrorBanner` on API failure. Overview hashes come from `/research/summary`. Jobs poll only while non-terminal and never invent a percentage.

## Visualization

Profile polylines connect stored δ only. Combined heatmap leaves missing cells unfilled (cream) and titles them “no stored cell”. Color scale is normalized to the **current grid maximum** — a visual convenience, not a shared scientific scale across filters.

## Accessibility

Automated axe-core was **not** a prior project dependency. Phase 5 added heading/label Playwright checks and a researcher walkthrough. Full axe CI is still optional. Keyboard: native `<select>`, `<button>`, `<a>`, and tables. Charts have `role="img"` and an `aria-label` plus `.sr-only` text.

Contrast and reduced-motion: source uses a static academic palette; no `prefers-reduced-motion` stylesheet was added (non-blocking; charts are not animated).

## Performance

Production JS bundle ~309 kB / ~96 kB gzip. Research pages request filtered Parquet slices (limit ≤ 2000), not 132k/242k raw rows. Combined endpoint aggregates on the server. Jobs poll every 2 s only when active.
