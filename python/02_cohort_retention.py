"""
Consumer Revenue Intelligence — Step 02
Cohort Retention Analysis

What this script does:
  Groups users by the month they subscribed (their acquisition cohort),
  then tracks what percentage of each cohort is still active at months
  1, 2, 3, 6, and 12 after joining.

  This is the foundation of the entire project. LTV, CAC payback, and
  churn prediction all build on top of this retention picture.

  Key outputs:
    - data/processed/cohort_retention.csv   (retention table)
    - outputs/charts/cohort_heatmap.png     (retention heatmap)
    - outputs/charts/retention_curves.png   (line chart by cohort)

Run after: python/01_generate_users.py
Usage:
    python3 python/02_cohort_retention.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
INPUT_USERS  = "data/synthetic/users.csv"
OUTPUT_DATA  = "data/processed/cohort_retention.csv"
OUTPUT_HEAT  = "outputs/charts/cohort_heatmap.png"
OUTPUT_LINES = "outputs/charts/retention_curves.png"

os.makedirs("data/processed",   exist_ok=True)
os.makedirs("outputs/charts",   exist_ok=True)

OBSERVATION_MONTHS = [1, 2, 3, 6, 12]

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT_USERS, parse_dates=["subscription_start", "subscription_end"])
print(f"✓ Loaded {len(df):,} users")

# ── Build cohort retention table ──────────────────────────────────────────────
records = []

for cohort_month, group in df.groupby("cohort_month"):
    cohort_size = len(group)

    for m in OBSERVATION_MONTHS:
        # A user is "active" at month M if they subscribed AND either:
        #   (a) have not churned at all, OR
        #   (b) churned but their months_active > m
        active = group[
            (group["churned"] == 0) |
            (group["months_active"] > m)
        ]
        retention_rate = len(active) / cohort_size

        records.append({
            "cohort_month":   cohort_month,
            "observation_month": m,
            "cohort_size":    cohort_size,
            "active_users":   len(active),
            "retention_rate": round(retention_rate, 4),
        })

df_retention = pd.DataFrame(records)
df_retention.to_csv(OUTPUT_DATA, index=False)
print(f"✓ Retention table saved: {OUTPUT_DATA}")

# ── Pivot for heatmap ──────────────────────────────────────────────────────────
pivot = df_retention.pivot(
    index="cohort_month",
    columns="observation_month",
    values="retention_rate"
)
pivot.columns = [f"Month {m}" for m in pivot.columns]
pivot.index.name = "Cohort"

# ── Chart 1: Heatmap ──────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 7))

sns.heatmap(
    pivot,
    annot=True,
    fmt=".0%",
    cmap="Blues",
    linewidths=0.5,
    linecolor="white",
    vmin=0,
    vmax=1,
    ax=ax,
    cbar_kws={"label": "Retention Rate", "shrink": 0.8},
)

ax.set_title(
    "Cohort Retention Heatmap\nSubscription retention by acquisition month",
    fontsize=14, fontweight="bold", pad=16
)
ax.set_xlabel("Months Since Subscription", fontsize=11)
ax.set_ylabel("Acquisition Cohort", fontsize=11)
ax.tick_params(axis="x", rotation=0)
ax.tick_params(axis="y", rotation=0)

plt.tight_layout()
plt.savefig(OUTPUT_HEAT, dpi=150, bbox_inches="tight")
plt.close()
print(f"✓ Heatmap saved: {OUTPUT_HEAT}")

# ── Chart 2: Retention curves ─────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 6))

cohorts = df_retention["cohort_month"].unique()
palette = sns.color_palette("Blues_d", len(cohorts))

for idx, cohort in enumerate(sorted(cohorts)):
    subset = df_retention[df_retention["cohort_month"] == cohort].sort_values("observation_month")
    ax.plot(
        subset["observation_month"],
        subset["retention_rate"],
        marker="o",
        linewidth=1.8,
        markersize=5,
        color=palette[idx],
        alpha=0.85,
        label=cohort,
    )

# Average retention line
avg_retention = df_retention.groupby("observation_month")["retention_rate"].mean()
ax.plot(
    avg_retention.index,
    avg_retention.values,
    marker="D",
    linewidth=2.5,
    markersize=7,
    color="#1F4E79",
    linestyle="--",
    label="Average",
    zorder=5,
)

ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
ax.set_xticks(OBSERVATION_MONTHS)
ax.set_xlabel("Months Since Subscription", fontsize=11)
ax.set_ylabel("Retention Rate", fontsize=11)
ax.set_title(
    "Retention Curves by Acquisition Cohort",
    fontsize=14, fontweight="bold", pad=14
)
ax.legend(
    title="Cohort",
    bbox_to_anchor=(1.01, 1),
    loc="upper left",
    fontsize=8,
    title_fontsize=9,
)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.set_ylim(0, 1.05)

plt.tight_layout()
plt.savefig(OUTPUT_LINES, dpi=150, bbox_inches="tight")
plt.close()
print(f"✓ Retention curves saved: {OUTPUT_LINES}")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n── Retention Summary (average across all cohorts) ───────────")
avg = df_retention.groupby("observation_month")["retention_rate"].mean()
for month, rate in avg.items():
    print(f"  Month {month:>2}:  {rate:.1%} retained")

best_cohort  = pivot.mean(axis=1).idxmax()
worst_cohort = pivot.mean(axis=1).idxmin()
print(f"\n  Best cohort:   {best_cohort}")
print(f"  Worst cohort:  {worst_cohort}")
print("─────────────────────────────────────────────────────────────")
print("\nNext step: run python3 python/03_ltv_modelling.py")
