# Phase 4 forensic audit

## Frontend scan

No production `TODO`/`FIXME`/`NotImplemented`, no mock scientific JSON, no `console.log` in `src/`, no `dangerouslySetInnerHTML`, no pickle/eval.

Default seed `20260905` is a control default matching the frozen seed list, not a fabricated metric.

Architecture constants on the interpolation page (12→128→128→128→3) are the frozen Phase 2 definition, labeled as such.

## Scientific scan

Displayed profile/threshold/asymmetry/interpolation/combined values are API fields or median-of-stored-relative-errors for the combined grid (same aggregation used in Phase 2 reports).

Phase 1 hash and Phase 2 counts are read from artefacts via the API, not hardcoded into charts.
