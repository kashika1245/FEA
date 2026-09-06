import type { CombinedCell } from "../api/types";

export function Heatmap({
  cells,
  title,
}: {
  cells: CombinedCell[];
  title: string;
}) {
  const xs = [...new Set(cells.map((c) => c.delta_a3))].sort((a, b) => a - b);
  const ys = [...new Set(cells.map((c) => c.delta_f))].sort((a, b) => a - b);
  const lookup = new Map(cells.map((c) => [`${c.delta_a3}:${c.delta_f}`, c]));
  const values = cells.map((c) => c.median_relative_error_pct);
  const vmax = values.length ? Math.max(...values) : 1;
  const cell = 28;
  const pad = 48;
  const width = pad + xs.length * cell + 16;
  const height = pad + ys.length * cell + 16;
  return (
    <figure className="card">
      <figcaption>
        <strong>{title}</strong>
        <div className="provenance">
          Source: GET /api/v1/research/combined · median of stored relative errors at each grid node
        </div>
      </figcaption>
      <svg
        className="chart"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`${title}. ${cells.length} observed grid cells.`}
      >
        {ys.map((y, iy) =>
          xs.map((x, ix) => {
            const item = lookup.get(`${x}:${y}`);
            const fill = item ? color(item.median_relative_error_pct, vmax) : "#efe8da";
            return (
              <rect
                key={`${x}:${y}`}
                x={pad + ix * cell}
                y={height - pad - (iy + 1) * cell}
                width={cell - 1}
                height={cell - 1}
                fill={fill}
              >
                <title>
                  {item
                    ? `δ_A3=${x.toFixed(2)}, δ_F=${y.toFixed(2)}, median RE=${item.median_relative_error_pct.toFixed(3)}%, n=${item.n}`
                    : `δ_A3=${x.toFixed(2)}, δ_F=${y.toFixed(2)}, no stored cell`}
                </title>
              </rect>
            );
          }),
        )}
        {xs.map((x, ix) => (
          <text key={x} x={pad + ix * cell + 8} y={height - 16} fontSize="9">
            {x.toFixed(2)}
          </text>
        ))}
        {ys.map((y, iy) => (
          <text key={y} x={8} y={height - pad - iy * cell - 10} fontSize="9">
            {y.toFixed(2)}
          </text>
        ))}
        <text x={width / 2} y={height - 2} textAnchor="middle" fontSize="11">
          A3 extrapolation distance
        </text>
      </svg>
    </figure>
  );
}

function color(value: number, vmax: number): string {
  const t = Math.min(1, value / (vmax || 1));
  const r = Math.round(42 + t * 140);
  const g = Math.round(70 - t * 40);
  const b = Math.round(80 - t * 50);
  return `rgb(${r},${g},${b})`;
}
