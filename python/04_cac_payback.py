"""
Consumer Revenue Intelligence — Step 04
CAC Payback Period Analysis

What this script does:
  Calculates how many months each acquisition channel takes to recover
  customer acquisition costs (CAC). This answers: "If we spend €X to acquire
  a customer, how many months until their cumulative revenue covers our cost?"

  Key outputs:
    - data/processed/cac_payback_summary.csv    (payback by channel)
    - data/processed/cac_payback_by_user.csv    (user-level payback data)
    - outputs/charts/cac_payback_by_channel.png (box plots + % never paid)
    - outputs/charts/cac_payback_curves.png     (cumulative revenue curves)

Run after: python3 python/03_ltv_modelling.py
Usage:     python3 python/04_cac_payback.py
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
OUTPUT_SUMM   = "data/processed/cac_payback_summary.csv"
OUTPUT_USER   = "data/processed/cac_payback_by_user.csv"
OUT_BOX       = "outputs/charts/cac_payback_by_channel.png"
OUT_CURVES    = "outputs/charts/cac_payback_curves.png"

os.makedirs("data/processed", exist_ok=True)
os.makedirs("outputs/charts", exist_ok=True)

BRAND_BLUE = "#1F4E79"
ACCENT_RED = "#D9534F"
MAX_MONTHS = 12
PAYBACK_BENCHMARK = 6

# ── Load data ─────────────────────────────────────────────────────────────────
df_users = pd.read_csv(INPUT_USERS)
df_ltv = pd.read_csv(INPUT_LTV)

df = df_users.merge(df_ltv[['user_id', 'ltv_eur']], on='user_id', how='left')
print(f"Loaded {len(df):,} users with LTV data")

# ── Calculate payback period for each user ────────────────────────────────────
def calculate_payback(row):
    monthly_rev = row['monthly_revenue_eur']
    cac = row['cpa_eur']
    months_active = min(row['months_active'], MAX_MONTHS)
    
    cumulative_rev = 0
    payback_month = MAX_MONTHS + 1
    
    for month in range(1, MAX_MONTHS + 1):
        if month <= months_active:
            cumulative_rev += monthly_rev
        
        if payback_month == MAX_MONTHS + 1 and cumulative_rev >= cac:
            payback_month = month
    
    return payback_month

print("\nCalculating payback periods for all users...")
df['payback_month'] = df.apply(calculate_payback, axis=1)
df['paid_back'] = df['payback_month'] <= MAX_MONTHS

# ── User-level payback file ───────────────────────────────────────────────────
payback_user = df[['user_id', 'acquisition_channel', 'tier', 'cpa_eur', 
                    'monthly_revenue_eur', 'months_active', 'payback_month', 'paid_back']].copy()
payback_user.to_csv(OUTPUT_USER, index=False)
print(f"User-level payback saved: {OUTPUT_USER}")

# ── Summary by channel ────────────────────────────────────────────────────────
channel_summary = df.groupby('acquisition_channel').agg(
    users             = ('user_id', 'count'),
    avg_payback       = ('payback_month', 'mean'),
    median_payback    = ('payback_month', 'median'),
    pct_paid_back     = ('paid_back', 'mean'),
    avg_cac           = ('cpa_eur', 'mean'),
    avg_months_active = ('months_active', 'mean'),
).round(2).reset_index()

never_paid = df[df['payback_month'] == MAX_MONTHS + 1].groupby('acquisition_channel').size()
channel_summary['never_paid_back'] = channel_summary['acquisition_channel'].map(never_paid).fillna(0).astype(int)
channel_summary['pct_never_paid'] = (channel_summary['never_paid_back'] / channel_summary['users'] * 100).round(1)

channel_summary = channel_summary.sort_values('avg_payback')
channel_summary.to_csv(OUTPUT_SUMM, index=False)
print(f"Payback summary saved: {OUTPUT_SUMM}")

# ── Calculate cumulative revenue curves ───────────────────────────────────────
def get_cumulative_curve(channel):
    channel_users = df[df['acquisition_channel'] == channel]
    cumulative_by_month = []
    
    for month in range(1, MAX_MONTHS + 1):
        active_mask = (channel_users['churned'] == 0) | (channel_users['months_active'] > month)
        active_users = channel_users[active_mask]
        
        if len(active_users) > 0:
            avg_rev = active_users['monthly_revenue_eur'].mean()
            cumulative = avg_rev * month
        else:
            cumulative = 0
        
        cumulative_by_month.append(cumulative)
    
    return cumulative_by_month

# ── Chart 1: Payback distribution by channel ──────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

order = channel_summary['acquisition_channel'].tolist()
palette = ["#1F4E79", "#2E75B6", "#5BA3D9", "#F0AD4E", "#D9534F"]

payback_data = df[df['payback_month'] <= MAX_MONTHS]
sns.boxplot(
    data=payback_data,
    x='acquisition_channel',
    y='payback_month',
    order=order,
    ax=axes[0],
    palette=palette[:len(order)],
    flierprops=dict(marker='o', markerfacecolor=ACCENT_RED, markersize=3, alpha=0.3)
)

axes[0].axhline(y=PAYBACK_BENCHMARK, color=ACCENT_RED, linestyle='--', alpha=0.7, linewidth=1.5)
axes[0].set_title('Payback Period by Channel', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Acquisition Channel', fontsize=11)
axes[0].set_ylabel('Months to Payback', fontsize=11)
axes[0].grid(axis='y', linestyle='--', alpha=0.3)

never_paid_pct = channel_summary.set_index('acquisition_channel')['pct_never_paid'].loc[order]
bars = axes[1].bar(never_paid_pct.index, never_paid_pct.values, 
                   color=ACCENT_RED, alpha=0.7, edgecolor='darkred', linewidth=1)
axes[1].set_title('Users Who Never Recovered CAC (12 months)', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Acquisition Channel', fontsize=11)
axes[1].set_ylabel('Percent of Users', fontsize=11)
axes[1].set_ylim(0, 100)

for bar, val in zip(bars, never_paid_pct.values):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                f'{val:.0f}%', ha='center', va='bottom', fontweight='bold', fontsize=10)

axes[1].grid(axis='y', linestyle='--', alpha=0.3)

plt.tight_layout()
plt.savefig(OUT_BOX, dpi=150, bbox_inches='tight')
plt.close()
print(f"Payback chart saved: {OUT_BOX}")

# ── Chart 2: Cumulative revenue curves ────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 7))

for idx, channel in enumerate(order):
    curve = get_cumulative_curve(channel)
    avg_cac = channel_summary[channel_summary['acquisition_channel'] == channel]['avg_cac'].values[0]
    months = range(1, MAX_MONTHS + 1)
    
    ax.plot(months, curve, marker='o', linewidth=2.5, markersize=5,
            color=palette[idx % len(palette)], label=f"{channel} (CAC: €{avg_cac:.0f})")
    ax.axhline(y=avg_cac, color=palette[idx % len(palette)], linestyle='--', alpha=0.5, linewidth=1)

ax.axvline(x=PAYBACK_BENCHMARK, color=ACCENT_RED, linestyle=':', alpha=0.7, linewidth=1.5)

ax.set_xlabel('Months Since Acquisition', fontsize=12)
ax.set_ylabel('Cumulative Revenue per User (€)', fontsize=12)
ax.set_title('CAC Payback Analysis: Cumulative Revenue by Channel', fontsize=13, fontweight='bold')
ax.legend(loc='upper left', fontsize=9)
ax.grid(axis='both', linestyle='--', alpha=0.3)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('€%.0f'))
ax.set_xticks(range(1, 13))
ax.set_xlim(0.5, 12.5)

plt.tight_layout()
plt.savefig(OUT_CURVES, dpi=150, bbox_inches='tight')
plt.close()
print(f"Payback curves saved: {OUT_CURVES}")

# ── Summary output ────────────────────────────────────────────────────────────
print("\n── CAC Payback by Acquisition Channel ───────────────────────────────")
print(channel_summary[['acquisition_channel', 'users', 'avg_payback', 
                         'median_payback', 'pct_never_paid', 'avg_cac']].to_string(index=False))

print("\n── Overall ───────────────────────────────────────────────────────────")
print(f"  Overall avg payback:     {df['payback_month'].mean():.1f} months")
print(f"  Users who paid back:     {df['paid_back'].sum():,} ({df['paid_back'].mean():.1%})")
print(f"  Users who never paid:    {(df['payback_month'] > MAX_MONTHS).sum():,}")
print("─────────────────────────────────────────────────────────────────────")
print("\nNext step: run python3 python/05_discount_sensitivity.py")