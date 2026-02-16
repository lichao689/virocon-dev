# Marine Analysis Workspace

This folder hosts an isolated marine analysis workspace for `virocon-dev`.

## Scope

- Keep `/Users/lichao/codes/_github/virocon-dev/virocon` read-only.
- Put all analysis scripts and configs under this folder.
- Read data only from `/Users/lichao/codes/_github/virocon-dev/data/Data-MarineDataGroupLimited`.
- Write outputs only to `/Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/output`.

## Quick Start

1. Create and prepare conda environment:

```bash
conda create -n virocon-lab python=3.13 -y
conda activate virocon-lab
python -m pip install --upgrade pip
python -m pip install -e /Users/lichao/codes/_github/virocon-dev
python -m pip install pyyaml openpyxl seaborn jupyter
```

2. Run validation scripts:

```bash
python /Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/scripts/check_env.py \
  --paths /Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/configs/paths.yaml

python /Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/scripts/check_data.py \
  --paths /Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/configs/paths.yaml --quick

python /Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/scripts/check_data.py \
  --paths /Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/configs/paths.yaml --full

python /Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/scripts/smoke_iform.py \
  --paths /Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/configs/paths.yaml \
  --runtime /Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/configs/runtime.yaml
```

3. Check repository cleanliness:

```bash
git -C /Users/lichao/codes/_github/virocon-dev status --short
```

