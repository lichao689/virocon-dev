"""
绘制海洋环境等值线（10年、50年、100年重现期）

使用 ViroCon 库基于 MarineDataGroupLimited 数据计算环境等值线
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from virocon import (
    GlobalHierarchicalModel,
    WeibullDistribution,
    LogNormalDistribution,
    DependenceFunction,
    IFORMContour,
    calculate_alpha,
    WidthOfIntervalSlicer,
)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# =============================================================================
# 1. 读取数据
# =============================================================================
data_path = "../data/Data-MarineDataGroupLimited/metocean_result.csv"
df = pd.read_csv(data_path, encoding='utf-8')

print(f"数据行数: {len(df)}")
print(f"数据列: {df.columns.tolist()}")

# 清理数据：移除 NaN 和非正值
df_clean = df[['有义波高', '峰值波周期', '10米风速']].dropna()
df_clean = df_clean[(df_clean['有义波高'] > 0) &
                    (df_clean['峰值波周期'] > 0) &
                    (df_clean['10米风速'] > 0)]

print(f"\n清理后数据行数: {len(df_clean)}")
print(df_clean.describe())

# =============================================================================
# 2. 定义联合分布模型 (Hs - Tp) - 使用 DNVGL 标准模型结构
# =============================================================================

def _power3(x, a, b, c):
    return a + b * x**c

def _exp3(x, a, b, c):
    return a + b * np.exp(c * x)

# 正确的 bounds 格式：每个参数一个 (lower, upper) 元组
bounds = [(0, None), (0, None), (None, None)]

power3 = DependenceFunction(_power3, bounds)
exp3 = DependenceFunction(_exp3, bounds)

dist_descriptions_hs_tp = [
    {
        "distribution": WeibullDistribution(),
        "intervals": WidthOfIntervalSlicer(width=0.5),
    },
    {
        "distribution": LogNormalDistribution(),
        "conditional_on": 0,
        "parameters": {"mu": power3, "sigma": exp3},
    },
]

# =============================================================================
# 3. 拟合模型
# =============================================================================
print("\n正在拟合 Hs-Tp 模型...")

model_hs_tp = GlobalHierarchicalModel(dist_descriptions_hs_tp)
data_hs_tp = df_clean[['有义波高', '峰值波周期']].values
model_hs_tp.fit(data_hs_tp)

print("Hs-Tp 模型拟合完成")
print(f"Hs (Weibull) 参数: alpha={model_hs_tp.distributions[0].alpha:.3f}, "
      f"beta={model_hs_tp.distributions[0].beta:.3f}, "
      f"gamma={model_hs_tp.distributions[0].gamma:.3f}")

# =============================================================================
# 4. 计算环境等值线
# =============================================================================
state_duration = 1  # 小时
return_periods = [10, 50, 100]  # 年
hours_per_year = 365.25 * 24

contours = {}
for rp in return_periods:
    alpha = calculate_alpha(state_duration, rp * hours_per_year)
    contour = IFORMContour(model_hs_tp, alpha)
    contours[rp] = contour
    print(f"{rp}年重现期: alpha = {alpha:.2e}")

# =============================================================================
# 5. 绘制等值线
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 8))

ax.scatter(df_clean['峰值波周期'], df_clean['有义波高'],
           s=1, alpha=0.3, c='gray', label='观测数据')

colors = ['blue', 'green', 'red']
for (rp, contour), color in zip(contours.items(), colors):
    coords = contour.coordinates
    ax.plot(coords[:, 1], coords[:, 0], color=color, linewidth=2,
            label=f'{rp}年重现期')

ax.set_xlabel('峰值波周期 Tp (s)', fontsize=12)
ax.set_ylabel('有义波高 Hs (m)', fontsize=12)
ax.set_title('海洋环境等值线 (Tp-Hs)', fontsize=14)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../output/env_contours_Tp_Hs.png', dpi=150, bbox_inches='tight')
print("\n等值线图已保存至 output/env_contours_Hs_Tp.png")

# =============================================================================
# 6. 风速-波高模型 (使用 DNVGL Hs-U 模型结构)
# =============================================================================
print("\n正在拟合风速-波高模型...")

# 使用 DNVGL 预定义模型结构
from virocon import get_DNVGL_Hs_U

dist_descriptions_u10_hs, fit_descriptions_u10_hs, _ = get_DNVGL_Hs_U()

# 注意：DNVGL 模型是 U-Hs，我们需要调整为 U10-Hs（风速-波高）
# 直接使用拟合数据
model_u10_hs = GlobalHierarchicalModel(dist_descriptions_u10_hs)
data_u10_hs = df_clean[['10米风速', '有义波高']].values
model_u10_hs.fit(data_u10_hs, fit_descriptions=fit_descriptions_u10_hs)

print("风速-波高模型拟合完成")

contours_u10_hs = {}
for rp in return_periods:
    alpha = calculate_alpha(state_duration, rp * hours_per_year)
    contour = IFORMContour(model_u10_hs, alpha)
    contours_u10_hs[rp] = contour

fig, ax = plt.subplots(figsize=(10, 8))

ax.scatter(df_clean['10米风速'], df_clean['有义波高'],
           s=1, alpha=0.1, c='gray', label='观测数据')

for (rp, contour), color in zip(contours_u10_hs.items(), colors):
    coords = contour.coordinates
    ax.plot(coords[:, 0], coords[:, 1], color=color, linewidth=2,
            label=f'{rp}年重现期')

ax.set_xlabel('10米风速 U10 (m/s)', fontsize=12)
ax.set_ylabel('有义波高 Hs (m)', fontsize=12)
ax.set_title('海洋环境等值线 (U10-Hs)', fontsize=14)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../output/env_contours_U10_Hs.png', dpi=150, bbox_inches='tight')
print("\n风速-波高等值线图已保存至 output/env_contours_U10_Hs.png")

# =============================================================================
# 7. 输出等值线坐标
# =============================================================================
print("\n" + "="*60)
print("等值线坐标数据 (Hs-Tp)")
print("="*60)

for rp in return_periods:
    coords = contours[rp].coordinates
    print(f"\n{rp}年重现期等值线 (共 {len(coords)} 个点):")
    print(f"  Hs 最大值: {coords[:, 0].max():.2f} m")
    print(f"  Tp 最大值: {coords[:, 1].max():.2f} s")

    coord_df = pd.DataFrame(coords, columns=['Hs_m', 'Tp_s'])
    coord_df.to_csv(f'../output/contour_{rp}yr_Hs_Tp.csv', index=False)
    print(f"  已保存至 output/contour_{rp}yr_Hs_Tp.csv")

print("\n完成!")
