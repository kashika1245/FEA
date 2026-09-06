# Phase 4 performance

- Production bundle ~307 kB JS / 96 kB gzip (Vite build 2026-09-05).
- Research reads request filtered Parquet slices (limit 200 default), not 132k observation files.
- Combined grid projects six columns and filters to one seed/direction pair before grouping.
- Job polling is 2 s and stops on terminal status; queries do not refetch on window focus.
- Experiment listing is one paginated request (limit 100).
