# Extrapolation Protocol

Frozen Phase 2 protocol executed as `paper-a.phase2.v1`.

## Distance

For input `x` with training interval `[xmin, xmax]`:

- upper: `x = xmax + δ(xmax − xmin)`, `δ+ = (x − xmax)/(xmax − xmin)`
- lower: `x = xmin − δ(xmax − xmin)`, `δ− = (xmin − x)/(xmax − xmin)`

`δ ≥ 0` always. Direction is stored separately.

## Exact extremes at δ = 0.50

| Variable | Lower | Upper |
|----------|------:|------:|
| Ai (mm²) | 25 | 125 |
| E (GPa) | 160 | 240 |
| F (kN) | −3.5 | 14.5 |

Lower F is a reversed concentrated force under the frozen direction `(0, −1)`. That is a mathematical experiment, not a claim that the physical training load was bidirectional.

## Observation identity

One variable-wise observation is uniquely identified by `(seed, anchor_id, variable, direction, delta)`.

One combined observation is uniquely identified by `(seed, anchor_id, direction_a3, direction_f, delta_a3, delta_f)`.

Expected counts are computed from configuration:

- variable-wise: `n_anchors × 12 × 2 × 11 × n_models`
- combined: `n_anchors × 11 × 11 × 2 × 2 × n_models`

For the primary run: 132,000 and 242,000.

## Physical interpretation note

A median relative-error crossing at a listed δ is the first **tested** grid point where the anchor-wise median reached the analysis convention. It is not a universal validity boundary and must not be reported as one.
