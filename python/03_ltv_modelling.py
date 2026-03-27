"""
Consumer Revenue Intelligence — Step 03
Customer Lifetime Value (LTV) Modelling

What this script does:
  Calculates how much revenue the average customer generates over their
  lifetime, broken down by acquisition channel, subscription tier, and
  genre preference.

  LTV here is the OBSERVED lifetime value — total revenue generated from
  subscription start to either churn or the analysis cutoff date. This is
  distinct from predicted LTV (which comes later in the churn model).

  Key outputs:
    - data/processed/ltv_summary.csv        (LTV by channel and tier)
    - data/processed/ltv_by_user.csv        (user-level LTV with all attributes)
    - outputs/charts/ltv_by_channel.png     (bar chart: LTV vs CPA by channel)
    - outputs/charts/ltv_curves.png         (LTV accumulation over time)
    - outputs/charts/ltv_by_tier.png        (LTV distribution by tier)

  The key commercial question answered here:
    Which acquisition channels produce the most valuable customers —
    not just the most customers?

Run after: python3 python/02_cohort_retention.py
Usage:     python3 python/03_ltv_modelling.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Paths ─────────────────────────────────────────────────────────────────────
INPUT_USERS   = "data/synthetic/users.csv"
OUTPUT_USER   = "data/processed/ltv_by_user.csv"
OUTPUT_SUMM   = "data/processed/ltv_summary.csv"
OUT_CHANNEL   = "outputs/charts/ltv_by_channel.png"
OUT_CURVES    = "outputs/charts/ltv_curves.png"
OUT_TIER      = "outputs/charts/ltv_by_tier.png"

os.makedirs("data/processed", exist_ok=True)
os.makedirs("outputs/charts", exist_ok=True)

BRAND_BLUE  = "#1F4E79"
ACCENT_BLUE = "#2E75B6"
PALETTE     = ["#1F4E79", "#2E75B6", "#5BA3D9", "#9DC3E6", "#BDD7EE"]

# ── Load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT_USERS)
print(f"✓ Loaded {len(df):,} users")

# total_revenue_eur is already calculated in 01_generate_users.py
# (monthly_revenue × months_active). We use it directly as observed LTV.
df["ltv_eur"] = df["total_revenue_eur"]

# LTV:CAC ratio — the most important unit economics metric
# A healthy subscription business targets LTV:CAC > 3
df["ltv_cac_ratio"] = df["ltv_eur"] / df["cpa_eur"].replace(0, np.nan)

# ── Save user-level LTV file ──────────────────────────────────────────────────
df.to_csv(OUTPUT_USER, index=False)
print(f"✓ User-level LTV saved: {OUTPUT_USER}")

# ── Summary by channel ────────────────────────────────────────────────────────
channel_summary = df.groupby("acquisition_channel").agg(
    users           = ("user_id",        "count"),
    avg_ltv         = ("ltv_eur",        "mean"),
    median_ltv      = ("ltv_eur",        "median"),
    avg_cpa         = ("cpa_eur",        "mean"),
    avg_ltv_cac     = ("ltv_cac_ratio",  "mean"),
    churn_rate      = ("churned",        "mean"),
    avg_months      = ("months_active",  "mean"),
).round(2).reset_index()

channel_summary["net_value"] = (channel_summary["avg_ltv"] - channel_summary["avg_cpa"]).round(2)
channel_summary = channel_summary.sort_values("avg_ltv", ascending=False)

# Summary by tier
tier_summary = df.groupby("tier").agg(
    users       = ("user_id",       "count"),
    avg_ltv     = ("ltv_eur",       "mean"),
    avg_cpa     = ("cpa_eur",       "mean"),
    avg_ltv_cac = ("ltv_cac_ratio", "mean"),
    churn_rate  = ("churned",       "mean"),
    avg_months  = ("months_active", "mean"),
).round(2).reset_index()

# Combined summary
ltv_summary = pd.concat([
    channel_summary.assign(segment_type="channel", segment=channel_summary["acquisition_channel"]),
    tier_summary.assign(segment_type="tier", segment=tier_summary["tier"]),
], ignore_index=True)

ltv_summary.to_csv(OUTPUT_SUMM, index=False)
print(f"✓ LTV summary saved: {OUTPUT_SUMM}")

# ── Chart 1: LTV vs CPA by channel ───────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 6))

channels  = channel_summary["acquisition_channel"].tolist()
avg_ltv   = channel_summary["avg_ltv"].tolist()
avg_cpa   = channel_summary["avg_cpa"].tolist()
net_value = channel_summary["net_value"].tolist()
x         = np.arange(len(channels))
width     = 0.32

bars_ltv = ax.bar(x - width/2, avg_ltv, width, label="Avg LTV (€)", color=ACCENT_BLUE, alpha=0.9)
bars_cpa = ax.bar(x + width/2, avg_cpa, width, label="Avg CPA (€)", color="#9DC3E6", alpha=0.9)

# Net value labels on LTV bars
for bar, nv in zip(bars_ltv, net_value):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 1.5,
        f"Net: €{nv:.0f}",
        ha="center", va="bottom", fontsize=8.5, color=BRAND_BLUE, fontweight="bold"
    )

ax.set_xticks(x)
ax.set_xticklabels(channels, fontsize=10)
ax.set_ylabel("Amount (€)", fontsize=11)
ax.set_title(
    "Average LTV vs. Cost of Acquisition by Channel\nNet value = LTV − CPA",
    fontsize=13, fontweight="bold", pad=14
)
ax.legend(fontsize=10)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.set_ylim(0, max(avg_ltv) * 1.18)

# LTV:CAC ratio annotation
for i, (ratio, ch) in enumerate(zip(channel_summary["avg_ltv_cac"], channels)):
    ax.text(
        i, -max(avg_ltv) * 0.07,
        f"LTV:CAC = {ratio:.1f}x",
        ha="center", va="top", fontsize=8, color="#555555"
    )

plt.tight_layout()
plt.savefig(OUT_CHANNEL, dpi=150, bbox_inches="tight")
plt.close()
print(f"✓ LTV by channel chart saved: {OUT_CHANNEL}")

# ── Chart 2: LTV accumulation curves over active months ──────────────────────
fig, ax = plt.subplots(figsize=(11, 6))

for idx, (channel, group) in enumerate(df.groupby("acquisition_channel")):
    # Average cumulative LTV at each month milestone
    month_points = range(1, 13)
    curve = []
    for m in month_points:
        # Users still active at month m: either not churned, or months_active > m
        active_at_m = group[(group["churned"] == 0) | (group["months_active"] > m)]
        avg_rev_at_m = active_at_m["monthly_revenue_eur"].mean() * m if len(active_at_m) > 0 else 0
        curve.append(avg_rev_at_m)

    ax.plot(
        list(month_points), curve,
        marker="o", linewidth=2, markersize=5,
        color=PALETTE[idx % len(PALETTE)],
        label=channel
    )

ax.set_xlabel("Months Since Subscription", fontsize=11)
ax.set_ylabel("Avg Cumulative Revenue per User (€)", fontsize=11)
ax.set_title(
    "LTV Accumulation Over Time by Acquisition Channel",
    fontsize=13, fontweight="bold", pad=14
)
ax.legend(fontsize=9, title="Channel", title_fontsize=9)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("€%.0f"))
ax.set_xticks(range(1, 13))

plt.tight_layout()
plt.savefig(OUT_CURVES, dpi=150, bbox_inches="tight")
plt.close()
print(f"✓ LTV curves saved: {OUT_CURVES}")

# ── Chart 3: LTV distribution by tier ────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))

tier_order = ["annual", "monthly", "free_trial"]
tier_data  = [df[df["tier"] == t]["ltv_eur"].values for t in tier_order]
tier_labels = ["Annual\n(€7.99/mo)", "Monthly\n(€9.99/mo)", "Free Trial\n(€0)"]

bp = ax.boxplot(
    tier_data,
    labels=tier_labels,
    patch_artist=True,
    medianprops=dict(color="white", linewidth=2),
    whiskerprops=dict(color=BRAND_BLUE),
    capprops=dict(color=BRAND_BLUE),
    flierprops=dict(marker="o", color=ACCENT_BLUE, alpha=0.3, markersize=3),
)

colors = [BRAND_BLUE, ACCENT_BLUE, "#9DC3E6"]
for patch, color in zip(bp["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.85)

# Add avg LTV annotations
for i, tier in enumerate(tier_order):
    avg = df[df["tier"] == tier]["ltv_eur"].mean()
    ax.text(i + 1, avg + 2, f"Avg: €{avg:.0f}", ha="center", fontsize=9,
            color="white" if i < 2 else BRAND_BLUE, fontweight="bold")

ax.set_ylabel("Observed LTV (€)", fontsize=11)
ax.set_title(
    "LTV Distribution by Subscription Tier",
    fontsize=13, fontweight="bold", pad=14
)
ax.grid(axis="y", linestyle="--", alpha=0.3)

plt.tight_layout()
plt.savefig(OUT_TIER, dpi=150, bbox_inches="tight")
plt.close()
print(f"✓ LTV by tier chart saved: {OUT_TIER}")

# ── Print summary ─────────────────────────────────────────────────────────────
print("\n── LTV by Acquisition Channel ───────────────────────────────")
print(channel_summary[["acquisition_channel", "users", "avg_ltv", "avg_cpa",
                         "net_value", "avg_ltv_cac", "churn_rate"]].to_string(index=False))

print("\n── LTV by Tier ──────────────────────────────────────────────")
print(tier_summary[["tier", "users", "avg_ltv", "avg_cpa",
                     "avg_ltv_cac", "churn_rate", "avg_months"]].to_string(index=False))

print("\n── Overall ───────────────────────────────────────────────────")
print(f"  Overall avg LTV:        €{df['ltv_eur'].mean():.2f}")
print(f"  Overall avg CPA:        €{df['cpa_eur'].mean():.2f}")
print(f"  Overall avg LTV:CAC:    {df['ltv_cac_ratio'].mean():.1f}x")
print(f"  Users with LTV:CAC > 3: {(df['ltv_cac_ratio'] > 3).sum():,} ({(df['ltv_cac_ratio'] > 3).mean():.1%})")
print("─────────────────────────────────────────────────────────────")
print("\nNext step: run python3 python/04_cac_payback.py")
