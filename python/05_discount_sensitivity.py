"""
Consumer Revenue Intelligence — Step 05
Discount Sensitivity & Acquisition ROI

What this script does:
  Models the impact of promotional discounts on customer profitability.
  Answers: "If we offer a discount to acquire customers, at what point
  does the offer destroy margin rather than drive growth?"

  For each acquisition channel, we simulate:
    - Discount depths from 0% to 100% in 5% increments
    - The resulting effective monthly revenue
    - The breakeven point where LTV:CAC falls below 3 (industry benchmark)
    - The point where LTV < CAC (negative ROI)

  Key outputs:
    - data/processed/discount_sensitivity.csv   (breakeven tables)
    - outputs/charts/discount_breakeven.png     (breakeven by channel)
    - outputs/charts/discount_ltv_curves.png    (LTV vs discount depth)
    - outputs/charts/discount_heatmap.png       (profitability by segment)

Run after: python3 python/04_cac_payback.py
Usage:     python3 python/05_discount_sensitivity.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Paths ─────────────────────────────────────────────────────────────────────
INPUT_USERS   = "data/synthetic/users.csv"
INPUT_LTV     = "data/processed/ltv_by_user.csv"
OUTPUT_SUMM   = "data/processed/discount_sensitivity.csv"
OUT_BREAK     = "outputs/charts/discount_breakeven.png"
OUT_CURVES    = "outputs/charts/discount_ltv_curves.png"
OUT_HEAT      = "outputs/charts/discount_heatmap.png"

os.makedirs("data/processed", exist_ok=True)
os.makedirs("outputs/charts", exist_ok=True)

BRAND_BLUE = "#1F4E79"
ACCENT_RED = "#D9534F"
PALETTE = ["#1F4E79", "#2E75B6", "#5BA3D9", "#F0AD4E", "#D9534F"]

DISCOUNT_DEPTHS = np.arange(0, 1.01, 0.05)
LTV_CAC_BENCHMARK = 3
MAX_MONTHS = 12

# ── Load data ─────────────────────────────────────────────────────────────────
df_users = pd.read_csv(INPUT_USERS)
df_ltv = pd.read_csv(INPUT_LTV)

# Merge and create ltv_cac_ratio if it doesn't exist
df = df_users.merge(df_ltv[['user_id', 'ltv_eur']], on='user_id', how='left')
df['ltv_cac_ratio'] = df['ltv_eur'] / df['cpa_eur'].replace(0, np.nan)
print(f"Loaded {len(df):,} users with LTV data")

# ── Discount simulation function ──────────────────────────────────────────────
def simulate_discount_impact(df_segment, segment_name, original_monthly_rev, avg_months, cac):
    results = []
    
    for discount in DISCOUNT_DEPTHS:
        effective_monthly = original_monthly_rev * (1 - discount)
        ltv = effective_monthly * avg_months
        ltv_cac = ltv / cac if cac > 0 else float('inf')
        
        below_benchmark = ltv_cac < LTV_CAC_BENCHMARK
        unprofitable = ltv < cac
        
        results.append({
            'segment': segment_name,
            'discount_pct': round(discount * 100, 1),
            'effective_monthly_rev': round(effective_monthly, 2),
            'ltv': round(ltv, 2),
            'ltv_cac_ratio': round(ltv_cac, 1),
            'below_benchmark': below_benchmark,
            'unprofitable': unprofitable
        })
    
    return pd.DataFrame(results)

# ── Prepare channel-level aggregates ─────────────────────────────────────────
channel_summary = df.groupby('acquisition_channel').agg(
    avg_monthly_rev = ('monthly_revenue_eur', 'mean'),
    avg_months = ('months_active', 'mean'),
    avg_cac = ('cpa_eur', 'mean'),
    current_ltv_cac = ('ltv_cac_ratio', 'mean')
).reset_index()

print("\nSimulating discount impact across channels...")
all_results = []
for _, row in channel_summary.iterrows():
    segment_df = df[df['acquisition_channel'] == row['acquisition_channel']]
    results = simulate_discount_impact(
        segment_df,
        row['acquisition_channel'],
        row['avg_monthly_rev'],
        row['avg_months'],
        row['avg_cac']
    )
    all_results.append(results)

df_discount = pd.concat(all_results, ignore_index=True)

# ── Find breakeven points ─────────────────────────────────────────────────────
breakeven_points = []
for channel in channel_summary['acquisition_channel'].unique():
    channel_data = df_discount[df_discount['segment'] == channel]
    
    below_bench = channel_data[channel_data['below_benchmark']]
    breakeven_bench = below_bench['discount_pct'].min() if len(below_bench) > 0 else 100
    
    unprofitable = channel_data[channel_data['unprofitable']]
    breakeven_loss = unprofitable['discount_pct'].min() if len(unprofitable) > 0 else 100
    
    current_ratio = channel_summary[channel_summary['acquisition_channel'] == channel]['current_ltv_cac'].values[0]
    
    breakeven_points.append({
        'channel': channel,
        'current_ltv_cac': current_ratio,
        'max_discount_benchmark': breakeven_bench,
        'max_discount_profitable': breakeven_loss,
        'safety_margin': breakeven_bench - breakeven_loss
    })

df_breakeven = pd.DataFrame(breakeven_points)
df_breakeven = df_breakeven.sort_values('max_discount_benchmark', ascending=False)
df_breakeven.to_csv(OUTPUT_SUMM, index=False)
print(f"Discount sensitivity summary saved: {OUTPUT_SUMM}")

# ── Chart 1: Breakeven by channel ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))

channels = df_breakeven['channel'].tolist()
benchmark_breakeven = df_breakeven['max_discount_benchmark'].tolist()
profitable_breakeven = df_breakeven['max_discount_profitable'].tolist()
current_ltv_cac = df_breakeven['current_ltv_cac'].tolist()

x = np.arange(len(channels))
width = 0.35

bars_bench = ax.bar(x - width/2, benchmark_breakeven, width, 
                     label='Breakeven (LTV:CAC < 3)', color=ACCENT_RED, alpha=0.7)
bars_profit = ax.bar(x + width/2, profitable_breakeven, width,
                      label='Unprofitable (LTV < CAC)', color=PALETTE[3], alpha=0.7)

for bars in [bars_bench, bars_profit]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.0f}%', ha='center', va='bottom', fontsize=9)

ax.set_xticks(x)
ax.set_xticklabels(channels, fontsize=10, rotation=45, ha='right')
ax.set_ylabel('Maximum Discount Before Breakeven (%)', fontsize=11)
ax.set_xlabel('Acquisition Channel', fontsize=11)
ax.set_title('Discount Sensitivity by Acquisition Channel', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.4)
ax.set_ylim(0, 110)

for i, ratio in enumerate(current_ltv_cac):
    ax.text(i, -8, f'LTV:CAC = {ratio:.1f}x', 
            ha='center', va='top', fontsize=8, color='#555555')

plt.tight_layout()
plt.savefig(OUT_BREAK, dpi=150, bbox_inches='tight')
plt.close()
print(f"Breakeven chart saved: {OUT_BREAK}")

# ── Chart 2: LTV vs Discount depth curves ────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 6))

for idx, channel in enumerate(channels):
    channel_data = df_discount[df_discount['segment'] == channel]
    ax.plot(
        channel_data['discount_pct'],
        channel_data['ltv'],
        marker='o',
        linewidth=2,
        markersize=4,
        label=channel,
        color=PALETTE[idx % len(PALETTE)]
    )
    
    breakeven_discount = df_breakeven[df_breakeven['channel'] == channel]['max_discount_benchmark'].values[0]
    breakeven_ltv = channel_data[channel_data['discount_pct'] == breakeven_discount]['ltv'].values
    if len(breakeven_ltv) > 0:
        ax.scatter(breakeven_discount, breakeven_ltv[0], 
                   s=80, color='red', zorder=5, edgecolors='white', linewidth=1.5)

for idx, row in channel_summary.iterrows():
    ax.axhline(y=row['avg_cac'], color=PALETTE[idx % len(PALETTE)], 
               linestyle='--', alpha=0.4, linewidth=1)

ax.set_xlabel('Discount Depth (%)', fontsize=11)
ax.set_ylabel('Observed LTV (€)', fontsize=11)
ax.set_title('LTV Degradation at Different Discount Depths', fontsize=13, fontweight='bold')
ax.legend(fontsize=9, title='Channel')
ax.grid(axis='y', linestyle='--', alpha=0.4)
ax.xaxis.set_major_formatter(mticker.PercentFormatter())
ax.set_xlim(0, 100)

plt.tight_layout()
plt.savefig(OUT_CURVES, dpi=150, bbox_inches='tight')
plt.close()
print(f"LTV curves saved: {OUT_CURVES}")

# ── Chart 3: Profitability heatmap ───────────────────────────────────────────
pivot_data = df_discount.pivot(
    index='segment',
    columns='discount_pct',
    values='ltv_cac_ratio'
)

fig, ax = plt.subplots(figsize=(12, 6))

sns.heatmap(
    pivot_data,
    annot=True,
    fmt='.1f',
    cmap='RdYlGn_r',
    center=3,
    vmin=0,
    vmax=6,
    ax=ax,
    cbar_kws={'label': 'LTV:CAC Ratio'},
    linewidths=0.5,
    linecolor='white'
)

ax.set_title('Profitability Heatmap: LTV:CAC Ratio by Channel and Discount', fontsize=13, fontweight='bold')
ax.set_xlabel('Discount Depth (%)', fontsize=11)
ax.set_ylabel('Acquisition Channel', fontsize=11)
ax.set_xticklabels([f'{int(x)}%' for x in pivot_data.columns], rotation=45)

plt.tight_layout()
plt.savefig(OUT_HEAT, dpi=150, bbox_inches='tight')
plt.close()
print(f"Profitability heatmap saved: {OUT_HEAT}")

# ── Print summary ─────────────────────────────────────────────────────────────
print("\n── Discount Sensitivity by Channel ─────────────────────────────────")
print(df_breakeven[['channel', 'current_ltv_cac', 'max_discount_benchmark', 
                     'max_discount_profitable']].to_string(index=False))

print("\n── Overall ─────────────────────────────────────────────────────────")
print(f"  Industry benchmark LTV:CAC:      {LTV_CAC_BENCHMARK}x")
print(f"  Channels with healthy buffer:     {(df_breakeven['max_discount_benchmark'] >= 50).sum()}")
print(f"  Channels with low buffer:         {(df_breakeven['max_discount_benchmark'] < 30).sum()}")
print("─────────────────────────────────────────────────────────────────────")
print("\nNext step: run python3 python/06_churn_prediction.py")