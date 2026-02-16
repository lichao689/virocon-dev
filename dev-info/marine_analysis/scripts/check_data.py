#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml


METOCEAN_REQUIRED = ["valid_time", "10米风速", "有义波高", "峰值波周期"]
CURRENT_REQUIRED = ["index", "流速 （节）", "流向 - 去向"]


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def _missing_columns(df: pd.DataFrame, required: list[str]) -> list[str]:
    return [col for col in required if col not in df.columns]


def _numeric_stats(df: pd.DataFrame, columns: list[str]) -> dict:
    out = {}
    for col in columns:
        raw = df[col]
        raw_na = raw.isna()
        numeric = pd.to_numeric(raw, errors="coerce")
        non_numeric_count = int((~raw_na & numeric.isna()).sum())
        out[col] = {
            "na_count": int(raw_na.sum()),
            "na_rate": float(raw_na.mean()),
            "non_numeric_count": non_numeric_count,
            "min": (None if numeric.dropna().empty else float(numeric.min())),
            "max": (None if numeric.dropna().empty else float(numeric.max())),
        }
    return out


def _read_csv(path: Path, nrows: int | None) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", nrows=nrows)


def run(paths_file: Path, mode: str) -> tuple[dict, int]:
    cfg = _load_yaml(paths_file)
    metocean_path = Path(cfg["metocean_csv"])
    current_path = Path(cfg["current_csv"])

    errors = []
    if not metocean_path.is_file():
        errors.append(f"metocean_csv not found: {metocean_path}")
    if not current_path.is_file():
        errors.append(f"current_csv not found: {current_path}")
    if errors:
        return {
            "success": False,
            "mode": mode,
            "errors": errors,
            "paths": {"metocean_csv": str(metocean_path), "current_csv": str(current_path)},
        }, 1

    nrows = 5000 if mode == "quick" else None
    metocean_df = _read_csv(metocean_path, nrows=nrows)
    current_df = _read_csv(current_path, nrows=nrows)

    metocean_missing = _missing_columns(metocean_df, METOCEAN_REQUIRED)
    current_missing = _missing_columns(current_df, CURRENT_REQUIRED)
    if metocean_missing or current_missing:
        return {
            "success": False,
            "mode": mode,
            "errors": ["required columns missing"],
            "missing_columns": {
                "metocean_csv": metocean_missing,
                "current_csv": current_missing,
            },
        }, 1

    metocean_numeric_cols = [c for c in METOCEAN_REQUIRED if c != "valid_time"]
    current_numeric_cols = [c for c in CURRENT_REQUIRED if c != "index"]

    payload = {
        "success": True,
        "mode": mode,
        "paths": {"metocean_csv": str(metocean_path), "current_csv": str(current_path)},
        "metocean": {
            "rows_read": int(len(metocean_df)),
            "columns": list(metocean_df.columns),
            "required_columns_ok": True,
            "numeric_stats": _numeric_stats(metocean_df, metocean_numeric_cols),
        },
        "current": {
            "rows_read": int(len(current_df)),
            "columns": list(current_df.columns),
            "required_columns_ok": True,
            "numeric_stats": _numeric_stats(current_df, current_numeric_cols),
        },
    }
    return payload, 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate marine CSV data files.")
    parser.add_argument("--paths", required=True, help="Path to paths.yaml")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--quick", action="store_true", help="Read first 5000 rows")
    mode_group.add_argument("--full", action="store_true", help="Read full files")
    args = parser.parse_args()
    mode = "quick" if args.quick else "full"

    try:
        payload, exit_code = run(Path(args.paths), mode)
    except Exception as exc:  # pragma: no cover - explicit error path
        payload = {"success": False, "mode": mode, "error": f"{type(exc).__name__}: {exc}"}
        exit_code = 1

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
