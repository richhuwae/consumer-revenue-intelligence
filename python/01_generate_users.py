"""
Consumer Revenue Intelligence — Step 01
Synthetic User & Subscription Generation

What this script does:
  Generates a realistic synthetic user base of 10,000 subscribers whose
  listening behaviour is grounded in REAL Spotify track data.

  Each user gets:
    - A dominant genre preference (drawn from actual Spotify genre distribution)
    - A preferred audio profile (derived from genre-characteristic parameters)
    - A subscription tier (free trial, monthly, annual)
    - An acquisition channel (Paid Social, Organic, Referral, Paid Search, Direct)
    - A cost-per-acquisition (CPA) based on channel
    - Monthly revenue (ARPU) based on tier
    - A churn probability driven by their listening behaviour
    - A subscription start date and (if churned) end date

  Why synthetic? Spotify does not expose real user subscription data via its
  public API. The tracks and audio features are 100% real Spotify data.
  The user layer is generated using realistic business assumptions — the same
  approach used in industry when modelling new products without historical data.

Note on audio features: Spotify deprecated the /audio-features endpoint for
new apps in late 2024. Genre-characteristic audio profiles (energy, valence,
danceability) are therefore generated synthetically using realistic per-genre
parameters. All track metadata (genre, popularity, explicit, duration) comes
from real Spotify API data via 00_spotify_fetch.py.

Run after: python/00_spotify_fetch.py
Output:    data/synthetic/users.csv

Usage:
    python python/01_generate_users.py
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ── Config ───────────────────────────────────────────────────────────────────
np.random.seed(42)   # Reproducibility

N_USERS      = 10_000
START_DATE   = datetime(2023, 1, 1)   # Subscription cohort window start
END_DATE     = datetime(2024, 6, 30)  # Cohort window end
CUTOFF_DATE  = datetime(2024, 12, 31) # Analysis cutoff (when we observe)

INPUT_TRACKS = "data/raw/spotify_tracks.csv"
OUTPUT_DIR   = "data/synthetic"

# ── Genre audio profiles ──────────────────────────────────────────────────────
# Realistic energy / valence / danceability ranges per genre.
# Used in place of Spotify audio features API (deprecated for new apps, 2024).
GENRE_PROFILES = {
    "pop":         {"energy": (0.65, 0.85), "valence": (0.55, 0.80), "danceability": (0.65, 0.85)},
    "rock":        {"energy": (0.70, 0.90), "valence": (0.35, 0.60), "danceability": (0.45, 0.65)},
    "hip-hop":     {"energy": (0.60, 0.80), "valence": (0.40, 0.70), "danceability": (0.70, 0.90)},
    "electronic":  {"energy": (0.75, 0.95), "valence": (0.45, 0.75), "danceability": (0.70, 0.90)},
    "r-n-b":       {"energy": (0.45, 0.70), "valence": (0.40, 0.70), "danceability": (0.60, 0.80)},
    "indie":       {"energy": (0.45, 0.70), "valence": (0.35, 0.65), "danceability": (0.45, 0.65)},
    "jazz":        {"energy": (0.30, 0.55), "valence": (0.40, 0.70), "danceability": (0.40, 0.65)},
    "classical":   {"energy": (0.15, 0.45), "valence": (0.25, 0.55), "danceability": (0.20, 0.45)},
    "latin":       {"energy": (0.65, 0.85), "valence": (0.60, 0.85), "danceability": (0.70, 0.90)},
    "country":     {"energy": (0.50, 0.75), "valence": (0.50, 0.75), "danceability": (0.50, 0.70)},
    "metal":       {"energy": (0.85, 0.98), "valence": (0.20, 0.45), "danceability": (0.30, 0.55)},
    "reggae":      {"energy": (0.40, 0.65), "valence": (0.55, 0.80), "danceability": (0.60, 0.80)},
    "soul":        {"energy": (0.40, 0.65), "valence": (0.45, 0.70), "danceability": (0.50, 0.70)},
    "alternative": {"energy": (0.55, 0.80), "valence": (0.30, 0.60), "danceability": (0.45, 0.65)},
    "folk":        {"energy": (0.25, 0.50), "valence": (0.35, 0.65), "danceability": (0.35, 0.55)},
    "dance":       {"energy": (0.75, 0.95), "valence": (0.55, 0.80), "danceability": (0.75, 0.95)},
    "blues":       {"energy": (0.35, 0.60), "valence": (0.25, 0.55), "danceability": (0.40, 0.60)},
    "punk":        {"energy": (0.80, 0.95), "valence": (0.30, 0.55), "danceability": (0.40, 0.60)},
    "ambient":     {"energy": (0.10, 0.35), "valence": (0.20, 0.50), "danceability": (0.20, 0.40)},
    "k-pop":       {"energy": (0.65, 0.88), "valence": (0.55, 0.80), "danceability": (0.65, 0.88)},
}
DEFAULT_PROFILE = {"energy": (0.50, 0.70), "valence": (0.40, 0.65), "danceability": (0.50, 0.70)}

# ── Subscription tiers ────────────────────────────────────────────────────────
TIERS = {
    "free_trial":  {"monthly_revenue": 0.00, "weight": 0.15},
    "monthly":     {"monthly_revenue": 9.99, "weight": 0.55},
    "annual":      {"monthly_revenue": 7.99, "weight": 0.30},   # billed annually, lower monthly equiv
}

# ── Acquisition channels ──────────────────────────────────────────────────────
# CPA = cost per acquisition (EUR). Realistic digital subscription benchmarks.
CHANNELS = {
    "Paid Social":    {"cpa_mean": 18, "cpa_std": 4,  "weight": 0.30},
    "Organic Search": {"cpa_mean":  6, "cpa_std": 2,  "weight": 0.25},
    "Referral":       {"cpa_mean":  4, "cpa_std": 1,  "weight": 0.15},
    "Paid Search":    {"cpa_mean": 22, "cpa_std": 5,  "weight": 0.20},
    "Direct":         {"cpa_mean":  2, "cpa_std": 1,  "weight": 0.10},
}

# ── Churn base rates by tier ──────────────────────────────────────────────────
# Monthly probability of churning (industry-realistic for streaming services)
CHURN_BASE = {
    "free_trial": 0.55,   # High — most trial users don't convert
    "monthly":    0.07,   # ~7% monthly churn = ~58% annual retention
    "annual":     0.02,   # Low — committed for a year
}

# ── Audio feature → churn modifiers ──────────────────────────────────────────
# Users whose listening profile correlates with higher engagement churn less
# These multipliers are applied to the base churn rate
def churn_modifier_from_audio(avg_energy, avg_valence, avg_danceability, sessions_per_month):
    """
    Simulate the effect of listening behaviour on churn probability.

    High-energy, positive, danceable listeners = more engaged = lower churn.
    Low session count = disengaged = higher churn.
    """
    modifier = 1.0

    # Engaged listeners (high energy + positive mood) churn less
    engagement_score = (avg_energy + avg_valence + avg_danceability) / 3
    if engagement_score > 0.65:
        modifier *= 0.75   # 25% less likely to churn
    elif engagement_score < 0.35:
        modifier *= 1.35   # 35% more likely to churn

    # Session frequency is the strongest predictor
    if sessions_per_month >= 20:
        modifier *= 0.60
    elif sessions_per_month >= 10:
        modifier *= 0.85
    elif sessions_per_month < 5:
        modifier *= 1.50

    return modifier


# ── Helper: random date between two dates ─────────────────────────────────────
def random_date(start, end):
    delta = (end - start).days
    return start + timedelta(days=np.random.randint(0, delta))


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load real Spotify track data
    if not os.path.exists(INPUT_TRACKS):
        raise FileNotFoundError(
            "Spotify track data not found. Run python/00_spotify_fetch.py first."
        )

    df = pd.read_csv(INPUT_TRACKS)
    print(f"✓ Loaded {len(df):,} tracks from Spotify")

    # Genre distribution from real Spotify data
    genre_dist = df["genre"].value_counts(normalize=True)
    genres     = genre_dist.index.tolist()
    genre_probs = genre_dist.values.tolist()

    # Tier and channel configs
    tier_names    = list(TIERS.keys())
    tier_weights  = [TIERS[t]["weight"] for t in tier_names]
    chan_names    = list(CHANNELS.keys())
    chan_weights  = [CHANNELS[c]["weight"] for c in chan_names]

    print(f"\nGenerating {N_USERS:,} synthetic users...")

    users = []

    for i in range(N_USERS):
        # Assign genre preference (from real Spotify genre distribution)
        genre = np.random.choice(genres, p=genre_probs)

        # Audio profile from genre characteristic ranges
        profile      = GENRE_PROFILES.get(genre, DEFAULT_PROFILE)
        avg_energy       = np.random.uniform(*profile["energy"])
        avg_valence      = np.random.uniform(*profile["valence"])
        avg_danceability = np.random.uniform(*profile["danceability"])

        # Avg popularity from real tracks in that genre
        genre_tracks = df[df["genre"] == genre]
        avg_popularity = genre_tracks["popularity"].mean() if len(genre_tracks) > 0 else 50
        avg_tempo = 120.0  # neutral default (features endpoint unavailable)

        # Sessions per month: Poisson distributed (realistic streaming behaviour)
        sessions_per_month = max(1, int(np.random.poisson(lam=12)))

        # Tier and channel
        tier    = np.random.choice(tier_names, p=tier_weights)
        channel = np.random.choice(chan_names, p=chan_weights)

        # CPA: draw from channel distribution (clipped at 0)
        cpa = max(0.5, np.random.normal(
            CHANNELS[channel]["cpa_mean"],
            CHANNELS[channel]["cpa_std"]
        ))

        # Monthly revenue
        monthly_revenue = TIERS[tier]["monthly_revenue"]

        # Subscription start date
        start_date = random_date(START_DATE, END_DATE)

        # Churn probability per month
        base_churn   = CHURN_BASE[tier]
        modifier     = churn_modifier_from_audio(avg_energy, avg_valence, avg_danceability, sessions_per_month)
        monthly_churn_prob = min(0.95, base_churn * modifier)

        # Simulate month-by-month survival until cutoff or churn
        churned   = False
        end_date  = None
        months_active = 0
        current_date  = start_date

        while current_date <= CUTOFF_DATE:
            months_active += 1
            if np.random.random() < monthly_churn_prob:
                churned  = True
                end_date = current_date
                break
            current_date += timedelta(days=30)

        # Total revenue generated
        total_revenue = monthly_revenue * months_active

        users.append({
            "user_id":             f"U{i+1:06d}",
            "genre_preference":    genre,
            "avg_energy":          round(avg_energy, 3),
            "avg_valence":         round(avg_valence, 3),
            "avg_danceability":    round(avg_danceability, 3),
            "avg_tempo":           round(avg_tempo, 1),
            "sessions_per_month":  sessions_per_month,
            "tier":                tier,
            "acquisition_channel": channel,
            "cpa_eur":             round(cpa, 2),
            "monthly_revenue_eur": monthly_revenue,
            "subscription_start":  start_date.strftime("%Y-%m-%d"),
            "subscription_end":    end_date.strftime("%Y-%m-%d") if end_date else None,
            "months_active":       months_active,
            "total_revenue_eur":   round(total_revenue, 2),
            "churned":             int(churned),
            "monthly_churn_prob":  round(monthly_churn_prob, 4),
            "cohort_month":        start_date.strftime("%Y-%m"),
        })

    df_users = pd.DataFrame(users)

    # Save
    output_path = os.path.join(OUTPUT_DIR, "users.csv")
    df_users.to_csv(output_path, index=False)
    print(f"✓ Saved: {output_path}")

    # Summary
    print("\n── User Base Summary ─────────────────────────────────")
    print(f"Total users:              {len(df_users):,}")
    print(f"Churned:                  {df_users['churned'].sum():,} ({df_users['churned'].mean()*100:.1f}%)")
    print(f"Avg months active:        {df_users['months_active'].mean():.1f}")
    print(f"Avg monthly revenue:      €{df_users['monthly_revenue_eur'].mean():.2f}")
    print(f"Avg CPA:                  €{df_users['cpa_eur'].mean():.2f}")
    print(f"Avg total revenue/user:   €{df_users['total_revenue_eur'].mean():.2f}")
    print(f"\nTier breakdown:")
    print(df_users["tier"].value_counts().to_string())
    print(f"\nChannel breakdown:")
    print(df_users["acquisition_channel"].value_counts().to_string())
    print("──────────────────────────────────────────────────────")
    print("\nNext step: run python/02_cohort_retention.py")


if __name__ == "__main__":
    main()
