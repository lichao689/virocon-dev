#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from virocon import (
    DependenceFunction,
    GlobalHierarchicalModel,
    IFORMContour,
    LogNormalDistribution,
    WeibullDistribution,
    WidthOfIntervalSlicer,
    calculate_alpha,
)


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def _prepare_data(
    csv_path: Path,
    primary_var: str,
    secondary_var: str,
    max_rows: int,
    random_seed: int,
) -> tuple[pd.DataFrame, int]:
    raw_df = pd.read_csv(csv_path, encoding="utf-8-sig", usecols=[primary_var, secondary_var])
    raw_rows = len(raw_df)
    clean_df = raw_df.copy()
    clean_df[primary_var] = pd.to_numeric(clean_df[primary_var], errors="coerce")
    clean_df[secondary_var] = pd.to_numeric(clean_df[secondary_var], errors="coerce")
    clean_df = clean_df.dropna(subset=[primary_var, secondary_var])
    clean_df = clean_df[(clean_df[primary_var] > 0) & (clean_df[secondary_var] > 0)]

    if len(clean_df) > max_rows:
        clean_df = clean_df.sample(n=max_rows, random_state=random_seed)

    if clean_df.empty:
        raise ValueError("No valid samples remain after preprocessing.")

    return clean_df.reset_index(drop=True), raw_rows


def _build_model() -> GlobalHierarchicalModel:
    def power3(x, a, b, c):
        x_pos = np.where(x >= 0, x, np.nan)
        return a + b * x_pos**c

    def exp3(x, a, b, c):
        x_pos = np.where(x >= 0, x, np.nan)
        return a + b * np.exp(c * x_pos)

    bounds = [(0, None), (0, None), (None, None)]
    power_dep = DependenceFunction(power3, bounds)
    exp_dep = DependenceFunction(exp3, bounds)

    dist_description_0 = {
        "distribution": WeibullDistribution(),
        "intervals": WidthOfIntervalSlicer(width=0.5),
    }
    dist_description_1 = {
        "distribution": LogNormalDistribution(),
        "conditional_on": 0,
        "parameters": {"mu": power_dep, "sigma": exp_dep},
    }
    return GlobalHierarchicalModel([dist_description_0, dist_description_1])


def _plot_contour(
    sample_df: pd.DataFrame,
    coordinates: np.ndarray,
    primary_var: str,
    secondary_var: str,
    out_path: Path,
) -> None:
    plot_df = sample_df
    if len(plot_df) > 5000:
        plot_df = plot_df.sample(n=5000, random_state=42)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(
        plot_df[primary_var].to_numpy(),
        plot_df[secondary_var].to_numpy(),
        s=6,
        alpha=0.2,
        color="#4c78a8",
        label="sample",
    )
    ax.plot(
        coordinates[:, 0],
        coordinates[:, 1],
        color="#e45756",
        linewidth=2.0,
        label="IFORM contour (50y)",
    )
    ax.set_xlabel("Primary variable")
    ax.set_ylabel("Secondary variable")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def run(paths_file: Path, runtime_file: Path) -> tuple[dict, int]:
    paths_cfg = _load_yaml(paths_file)
    runtime_cfg = _load_yaml(runtime_file)

    metocean_csv = Path(paths_cfg["metocean_csv"])
    output_dir = Path(paths_cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    primary_var = runtime_cfg["smoke_primary_var"]
    secondary_var = runtime_cfg["smoke_secondary_var"]
    max_rows = int(runtime_cfg["smoke_max_rows"])
    random_seed = int(runtime_cfg["smoke_random_seed"])
    n_points = int(runtime_cfg["smoke_n_points"])
    state_duration_hours = float(runtime_cfg["state_duration_hours"])

    sample_df, raw_rows = _prepare_data(
        metocean_csv, primary_var, secondary_var, max_rows, random_seed
    )
    data_2d = sample_df[[primary_var, secondary_var]].to_numpy()

    model = _build_model()
    model.fit(data_2d)

    # Smoke test uses a fixed 50-year contour target by plan.
    alpha = calculate_alpha(state_duration_hours, 50)
    contour = IFORMContour(model, alpha, n_points=n_points)
    coordinates = contour.coordinates

    coords_csv = output_dir / "iform_wind10_hs_coords.csv"
    plot_png = output_dir / "iform_wind10_hs_plot.png"
    pd.DataFrame(coordinates, columns=[primary_var, secondary_var]).to_csv(
        coords_csv, index=False
    )
    _plot_contour(sample_df, coordinates, primary_var, secondary_var, plot_png)

    payload = {
        "success": True,
        "sample": {
            "raw_rows_read": int(raw_rows),
            "rows_used": int(len(sample_df)),
            "primary_var": primary_var,
            "secondary_var": secondary_var,
        },
        "alpha": float(alpha),
        "contour_points": int(coordinates.shape[0]),
        "maxima": {
            primary_var: float(np.nanmax(coordinates[:, 0])),
            secondary_var: float(np.nanmax(coordinates[:, 1])),
        },
        "output": {"coords_csv": str(coords_csv), "plot_png": str(plot_png)},
    }
    return payload, 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run minimal IFORM smoke test on marine data.")
    parser.add_argument("--paths", required=True, help="Path to paths.yaml")
    parser.add_argument("--runtime", required=True, help="Path to runtime.yaml")
    args = parser.parse_args()

    try:
        payload, exit_code = run(Path(args.paths), Path(args.runtime))
    except Exception as exc:  # pragma: no cover - explicit error path
        payload = {"success": False, "error": f"{type(exc).__name__}: {exc}"}
        exit_code = 1

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
