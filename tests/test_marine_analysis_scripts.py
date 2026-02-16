import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path("/Users/lichao/codes/_github/virocon-dev")
MARINE_ROOT = REPO_ROOT / "dev-info" / "marine_analysis"
SCRIPTS_ROOT = MARINE_ROOT / "scripts"
PATHS_YAML = MARINE_ROOT / "configs" / "paths.yaml"
RUNTIME_YAML = MARINE_ROOT / "configs" / "runtime.yaml"


def _run(script_name, *args):
    cmd = [sys.executable, str(SCRIPTS_ROOT / script_name), *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _parse_json(stdout):
    return json.loads(stdout)


def test_check_env_script():
    result = _run("check_env.py", "--paths", str(PATHS_YAML))
    assert result.returncode == 0, result.stdout + result.stderr
    payload = _parse_json(result.stdout)
    assert payload["success"] is True
    assert "python_version" in payload
    assert "virocon_version" in payload


def test_check_data_quick_script():
    result = _run("check_data.py", "--paths", str(PATHS_YAML), "--quick")
    assert result.returncode == 0, result.stdout + result.stderr
    payload = _parse_json(result.stdout)
    assert payload["success"] is True
    assert payload["mode"] == "quick"
    assert "metocean" in payload
    assert "current" in payload


def test_smoke_iform_script_outputs():
    result = _run(
        "smoke_iform.py",
        "--paths",
        str(PATHS_YAML),
        "--runtime",
        str(RUNTIME_YAML),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = _parse_json(result.stdout)
    assert payload["success"] is True
    coords_path = Path(payload["output"]["coords_csv"])
    plot_path = Path(payload["output"]["plot_png"])
    assert coords_path.exists()
    assert plot_path.exists()
