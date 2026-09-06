"""Publication-quality plots from stored observations. No smoothing."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyarrow.parquet as pq

from app.scientific.experiments.artifacts import ExperimentPaths
from app.scientific.surrogate.config import OUTPUT_NAMES


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "font.size": 10,
            "axes.grid": True,
            "grid.alpha": 0.25,
        }
    )


def write_interpolation_plots(paths: ExperimentPaths) -> list[Path]:
    _style()
    written: list[Path] = []
    for pred_path in sorted(paths.interpolation.glob("seed-*-predictions.parquet")):
        table = pq.read_table(pred_path)
        seed = pred_path.name.split("-")[1]
        fig, axes = plt.subplots(2, 3, figsize=(12, 7))
        for index, response in enumerate(OUTPUT_NAMES):
            fea = np.asarray(table.column(f"fea_{response}"))
            pred = np.asarray(table.column(f"predicted_{response}"))
            axes[0, index].scatter(fea, pred, s=8, alpha=0.45, linewidths=0)
            lo = float(min(fea.min(), pred.min()))
            hi = float(max(fea.max(), pred.max()))
            axes[0, index].plot([lo, hi], [lo, hi], color="black", linewidth=1)
            axes[0, index].set_title(f"{response} predicted vs FEA")
            axes[0, index].set_xlabel("FEA")
            axes[0, index].set_ylabel("MLP")
            residual = pred - fea
            axes[1, index].scatter(fea, residual, s=8, alpha=0.45, linewidths=0)
            axes[1, index].axhline(0.0, color="black", linewidth=1)
            axes[1, index].set_title(f"{response} residual")
            axes[1, index].set_xlabel("FEA")
            axes[1, index].set_ylabel("prediction - FEA")
        fig.suptitle(f"Interpolation competence, seed {seed}")
        fig.tight_layout()
        out = paths.interpolation / f"seed-{seed}-predicted-vs-fea.pdf"
        fig.savefig(out)
        fig.savefig(out.with_suffix(".png"))
        plt.close(fig)
        written.extend([out, out.with_suffix(".png")])
    return written


def write_profile_plots(paths: ExperimentPaths) -> list[Path]:
    _style()
    table = pq.read_table(paths.profiles / "profiles.parquet")
    rows = table.to_pylist()
    written: list[Path] = []
    variables = sorted({row["variable"] for row in rows}, key=lambda name: (name[0] != "A", name))
    seeds = sorted({int(row["seed"]) for row in rows})
    out_dir = paths.profiles / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    for variable in variables:
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), sharex=True)
        for axis, response in zip(axes, OUTPUT_NAMES, strict=True):
            for direction, color in (("lower", "#1f77b4"), ("upper", "#d62728")):
                subset = [
                    row
                    for row in rows
                    if row["variable"] == variable
                    and row["response"] == response
                    and row["direction"] == direction
                    and int(row["seed"]) == seeds[0]
                ]
                subset = sorted(subset, key=lambda row: float(row["delta"]))
                if not subset:
                    continue
                xs = [float(row["delta"]) for row in subset]
                ys = [float(row["median_relative_error_pct"]) for row in subset]
                q1 = [float(row["q1_relative_error_pct"]) for row in subset]
                q3 = [float(row["q3_relative_error_pct"]) for row in subset]
                axis.plot(xs, ys, marker="o", color=color, label=direction)
                axis.fill_between(xs, q1, q3, color=color, alpha=0.18, linewidth=0)
            axis.set_title(response)
            axis.set_xlabel(r"$\delta$")
            axis.set_ylabel("median relative error (%)")
            axis.legend(frameon=False)
        fig.suptitle(
            f"Variable-wise extrapolation profile: {variable} (seed {seeds[0]}, Q1-Q3 across anchors)"
        )
        fig.tight_layout()
        out = out_dir / f"profile-{variable}.pdf"
        fig.savefig(out)
        fig.savefig(out.with_suffix(".png"))
        plt.close(fig)
        written.extend([out, out.with_suffix(".png")])
    return written


def write_combined_heatmaps(paths: ExperimentPaths) -> list[Path]:
    _style()
    table = pq.read_table(paths.combined / "observations.parquet")
    rows = table.to_pylist()
    out_dir = paths.combined / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    seeds = sorted({int(row["seed"]) for row in rows})
    seed = seeds[0]
    for response in OUTPUT_NAMES:
        for direction_a3 in ("lower", "upper"):
            for direction_f in ("lower", "upper"):
                subset = [
                    row
                    for row in rows
                    if int(row["seed"]) == seed
                    and row["direction_a3"] == direction_a3
                    and row["direction_f"] == direction_f
                ]
                if not subset:
                    continue
                deltas_a3 = sorted({float(row["delta_a3"]) for row in subset})
                deltas_f = sorted({float(row["delta_f"]) for row in subset})
                grid = np.full((len(deltas_f), len(deltas_a3)), np.nan)
                buckets: dict[tuple[float, float], list[float]] = {}
                for row in subset:
                    key = (float(row["delta_a3"]), float(row["delta_f"]))
                    buckets.setdefault(key, []).append(float(row[f"relative_{response}_error"]))
                for i, delta_f in enumerate(deltas_f):
                    for j, delta_a3 in enumerate(deltas_a3):
                        values = buckets.get((delta_a3, delta_f))
                        if values:
                            grid[i, j] = float(np.median(values))
                fig, axis = plt.subplots(figsize=(5.2, 4.4))
                image = axis.imshow(
                    grid,
                    origin="lower",
                    aspect="auto",
                    extent=(min(deltas_a3), max(deltas_a3), min(deltas_f), max(deltas_f)),
                )
                axis.set_xlabel(r"$\delta_{A3}$")
                axis.set_ylabel(r"$\delta_{F}$")
                axis.set_title(
                    f"A3+F median RE {response} (%)\nA3 {direction_a3}, F {direction_f}, seed {seed}"
                )
                fig.colorbar(image, ax=axis, label="median relative error (%)")
                fig.tight_layout()
                out = out_dir / f"combined-{response}-{direction_a3}-{direction_f}.pdf"
                fig.savefig(out)
                fig.savefig(out.with_suffix(".png"))
                plt.close(fig)
                written.extend([out, out.with_suffix(".png")])
    return written
