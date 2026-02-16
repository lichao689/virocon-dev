# virocon-dev 独立分析环境配置实施方案

> 目标：仅使用现有 `virocon` 代码，不修改其原始源码；分析程序放在独立目录，环境可复现、低风险。

## 1. 总体原则

1. 保持 `virocon` 源码只读使用：`/Users/lichao/codes/_github/virocon-dev/virocon`
2. 所有分析脚本与配置集中在：`/Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis`
3. 数据输入目录固定：`/Users/lichao/codes/_github/virocon-dev/datasets/Data-MarineDataGroupLimited`
4. 结果输出目录固定：`/Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/output`
5. Python 环境与 `base` 隔离，避免污染全局环境。

## 2. 目录结构（独立分析工程）

在仓库中创建以下结构：

```text
/Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/
  README.md
  requirements.lock.txt
  configs/
    paths.yaml
    runtime.yaml
  scripts/
    check_env.py
    check_data.py
    smoke_iform.py
  output/
    .gitkeep
```

说明：

- `scripts/check_env.py`：验证 `virocon` 与分析依赖是否可导入，并确认导入路径来源于本地仓库。
- `scripts/check_data.py`：验证主数据文件存在且可读取。
- `scripts/smoke_iform.py`：进行最小 `GlobalHierarchicalModel + IFORMContour` 功能烟测，输出到 `output/`。

## 3. 环境创建与依赖安装

推荐环境名：`virocon-lab`。

```bash
conda create -n virocon-lab python=3.13 -y
conda activate virocon-lab

python -m pip install --upgrade pip
python -m pip install -e /Users/lichao/codes/_github/virocon-dev
python -m pip install pandas openpyxl matplotlib seaborn jupyter
```

依赖锁定：

```bash
python -m pip freeze > /Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/requirements.lock.txt
```

## 4. 配置文件建议

### 4.1 `configs/paths.yaml`

```yaml
repo_root: /Users/lichao/codes/_github/virocon-dev
input_dir: /Users/lichao/codes/_github/virocon-dev/datasets/Data-MarineDataGroupLimited
output_dir: /Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/output
metocean_csv: /Users/lichao/codes/_github/virocon-dev/datasets/Data-MarineDataGroupLimited/metocean_result.csv
current_csv: /Users/lichao/codes/_github/virocon-dev/datasets/Data-MarineDataGroupLimited/current_result.csv
```

### 4.2 `configs/runtime.yaml`

```yaml
timezone: UTC
return_period_years: [1, 50, 100]
state_duration_hours: 1
workflow: "先体检，后风浪，再纳入流"
```

## 5. 验证步骤（必须执行）

### 5.1 环境验证

```bash
python -c "import virocon,inspect; print(virocon.__version__); print(inspect.getfile(virocon))"
python -c "import pandas,openpyxl,matplotlib,seaborn; print('deps ok')"
```

验收标准：

- `inspect.getfile(virocon)` 指向 `/Users/lichao/codes/_github/virocon-dev/virocon/__init__.py`
- 依赖导入成功。

### 5.2 数据验证

```bash
python /Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/scripts/check_data.py
```

验收标准：

- 成功读取：
  - `/Users/lichao/codes/_github/virocon-dev/datasets/Data-MarineDataGroupLimited/metocean_result.csv`
  - `/Users/lichao/codes/_github/virocon-dev/datasets/Data-MarineDataGroupLimited/current_result.csv`

### 5.3 功能烟测

```bash
python /Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis/scripts/smoke_iform.py
```

验收标准：

- 能调用 `GlobalHierarchicalModel` 与 `IFORMContour`。
- 在 `output/` 下生成轮廓坐标或图件。

## 6. 运行约束（防止误改源码）

1. 日常开发与运行仅在 `/Users/lichao/codes/_github/virocon-dev/dev-info/marine_analysis` 下进行。
2. 不在 `/Users/lichao/codes/_github/virocon-dev/virocon` 下创建/编辑文件。
3. 所有分析结果只写到 `output/`。
4. 每次运行后执行：

```bash
git -C /Users/lichao/codes/_github/virocon-dev status --short
```

仅允许看到 `dev-info/marine_analysis` 内新增或变更；若出现 `virocon/` 变更，立即停止并回滚。

## 7. API/代码边界

1. 不修改 `virocon` 公共 API。
2. 不修改 `/Users/lichao/codes/_github/virocon-dev/virocon` 任意模块。
3. 仅新增独立分析脚本与配置文件。

## 8. 风险与应对

1. **网络受限导致 conda/pip 安装失败**：切换单位镜像源或使用离线 wheel。
2. **环境漂移**：必须维护 `requirements.lock.txt`。
3. **误写入源码目录**：通过 `git status` 自检门禁。

## 9. 默认假设

1. 路线：先体检，后风浪，再纳入流。
2. 时间口径：UTC。
3. 返回期：1/50/100 年。
