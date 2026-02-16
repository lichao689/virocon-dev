#!/usr/bin/env python3
import argparse
import importlib
import inspect
import json
import platform
import sys
from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def _check_imports(module_names: list[str]) -> tuple[dict, dict]:
    statuses = {}
    imported = {}
    for name in module_names:
        try:
            imported[name] = importlib.import_module(name)
            statuses[name] = {"ok": True}
        except Exception as exc:  # pragma: no cover - explicit error path
            statuses[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return statuses, imported


def run(paths_file: Path) -> tuple[dict, int]:
    config = _load_yaml(paths_file)
    repo_root = Path(config["repo_root"]).resolve()

    module_names = ["virocon", "numpy", "pandas", "scipy", "sklearn", "matplotlib", "yaml"]
    imports, imported_modules = _check_imports(module_names)

    virocon_module = imported_modules.get("virocon")
    virocon_file = None
    virocon_version = None
    source_in_repo = False
    if virocon_module is not None:
        virocon_file = str(Path(inspect.getfile(virocon_module)).resolve())
        virocon_version = getattr(virocon_module, "__version__", "unknown")
        source_in_repo = repo_root in Path(virocon_file).parents

    success = all(item["ok"] for item in imports.values()) and source_in_repo
    payload = {
        "success": success,
        "python_version": platform.python_version(),
        "virocon_version": virocon_version,
        "virocon_file": virocon_file,
        "repo_root": str(repo_root),
        "source_in_repo": source_in_repo,
        "imports": imports,
    }
    return payload, (0 if success else 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate marine analysis Python environment.")
    parser.add_argument("--paths", required=True, help="Path to paths.yaml")
    args = parser.parse_args()

    try:
        payload, exit_code = run(Path(args.paths))
    except Exception as exc:  # pragma: no cover - explicit error path
        payload = {"success": False, "error": f"{type(exc).__name__}: {exc}"}
        exit_code = 1

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
