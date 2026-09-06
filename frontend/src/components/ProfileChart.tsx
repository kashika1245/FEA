import type { SeriesPoint } from "../lib/profiles";

interface Props {
  title: string;
  yLabel: string;
  lower: SeriesPoint[];
  upper: SeriesPoint[];
  compare: boolean;
  showIqrBand?: boolean;
}

export function ProfileChart({ title, yLabel, lower, upper, compare, showIqrBand = false }: Props) {
  const series = compare ? [...lower, ...upper] : lower;
  const width = 720;
  const height = 360;
  const pad = { l: 64, r: 16, t: 28, b: 48 };
  const xs = series.map((p) => p.delta);
  const ys = series.flatMap((p) => [p.median, p.q1, p.q3]).filter((v) => Number.isFinite(v));
  const x0 = 0;
  const x1 = 0.5;
  const y0 = ys.length ? Math.min(0, ...ys) : 0;
  const y1 = ys.length ? Math.max(...ys) * 1.05 : 1;
  const sx = (x: number) => pad.l + ((x - x0) / (x1 - x0)) * (width - pad.l - pad.r);
  const sy = (y: number) => pad.t + (1 - (y - y0) / (y1 - y0 || 1)) * (height - pad.t - pad.b);
  const path = (points: SeriesPoint[]) =>
    points.map((p, i) => `${i === 0 ? "M" : "L"} ${sx(p.delta)} ${sy(p.median)}`).join(" ");
  const band = (points: SeriesPoint[]) => {
    if (points.length < 2) return "";
    const top = points.map((p, i) => `${i === 0 ? "M" : "L"} ${sx(p.delta)} ${sy(p.q3)}`);
    const bottom = [...points].reverse().map((p) => `L ${sx(p.delta)} ${sy(p.q1)}`);
    return `${top.join(" ")} ${bottom.join(" ")} Z`;
  };
  const summary = series.length
    ? `Stored profile points from δ ${xs[0]?.toFixed(2)} to ${xs[xs.length - 1]?.toFixed(2)}. Values are API medians; the polyline is not smoothed.`
    : "No profile points for the current filters.";
  return (
    <figure className="card">
      <figcaption>
        <strong>{title}</strong>
        <div className="provenance">
          Source: GET /api/v1/research/profiles · no visual interpolation between missing δ
        </div>
      </figcaption>
      <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={summary}>
        <text x={width / 2} y={18} textAnchor="middle" fontSize="13">
          {title}
        </text>
        <text x={width / 2} y={height - 8} textAnchor="middle" fontSize="12">
          Extrapolation distance δ
        </text>
        <text
          x={16}
          y={height / 2}
          textAnchor="middle"
          fontSize="12"
          transform={`rotate(-90 16 ${height / 2})`}
        >
          {yLabel}
        </text>
        {[0, 0.1, 0.2, 0.3, 0.4, 0.5].map((tick) => (
          <g key={tick}>
            <line
              x1={sx(tick)}
              x2={sx(tick)}
              y1={pad.t}
              y2={height - pad.b}
              stroke="#ddd4c4"
            />
            <text x={sx(tick)} y={height - pad.b + 18} textAnchor="middle" fontSize="11">
              {tick.toFixed(2)}
            </text>
          </g>
        ))}
        {showIqrBand && lower.length > 1 ? (
          <path d={band(lower)} fill="rgba(30,77,123,0.12)" />
        ) : null}
        {lower.length ? <path d={path(lower)} fill="none" stroke="#1e4d7b" strokeWidth="2" /> : null}
        {compare && upper.length ? (
          <path d={path(upper)} fill="none" stroke="#9a3412" strokeWidth="2" />
        ) : null}
        {lower.map((p) => (
          <circle key={`l-${p.seed}-${p.delta}`} cx={sx(p.delta)} cy={sy(p.median)} r="3" fill="#1e4d7b">
            <title>
              {`Direction: lower\nδ: ${p.delta.toFixed(2)}\nMedian: ${p.median.toFixed(3)}\nIQR (relative %): ${p.q1.toFixed(3)}–${p.q3.toFixed(3)}\nSeed: ${p.seed}`}
            </title>
          </circle>
        ))}
        {compare
          ? upper.map((p) => (
              <circle key={`u-${p.seed}-${p.delta}`} cx={sx(p.delta)} cy={sy(p.median)} r="3" fill="#9a3412">
                <title>
                  {`Direction: upper\nδ: ${p.delta.toFixed(2)}\nMedian: ${p.median.toFixed(3)}\nIQR (relative %): ${p.q1.toFixed(3)}–${p.q3.toFixed(3)}\nSeed: ${p.seed}`}
                </title>
              </circle>
            ))
          : null}
      </svg>
      <p className="sr-only">{summary}</p>
      <p className="provenance">
        Blue = lower{compare ? "; rust = upper" : ""}. The shaded band is the stored
        relative-error IQR across anchors and is drawn only when that metric is selected.
      </p>
    </figure>
  );
}
