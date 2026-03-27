"""
Consumer Revenue Intelligence — Step 00
Spotify Data Collection

What this script does:
  1. Authenticates with Spotify using Client Credentials (no user login needed)
  2. Pulls ~5,000 tracks across 20 music genres
  3. Fetches audio features for every track (energy, danceability, valence, etc.)
  4. Saves two clean CSVs to data/raw/:
       - spotify_tracks.csv      (track metadata + popularity)
       - spotify_audio_features.csv (audio feature vectors)

Run this once. It takes ~5–10 minutes due to Spotify rate limits.
Output is the foundation for all downstream analysis.

Usage:
    python python/00_spotify_fetch.py
"""

import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

# ── Load credentials ─────────────────────────────────────────────────────────
load_dotenv()
CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise EnvironmentError(
        "Missing Spotify credentials.\n"
        "1. Copy .env.example to .env\n"
        "2. Fill in your SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET\n"
        "3. Re-run this script."
    )

# ── Genres to collect ────────────────────────────────────────────────────────
# 20 genres that represent real subscription listener segments
GENRES = [
    "pop", "rock", "hip-hop", "electronic", "r-n-b",
    "indie", "jazz", "classical", "latin", "country",
    "metal", "reggae", "soul", "alternative", "folk",
    "dance", "blues", "punk", "ambient", "k-pop"
]

TRACKS_PER_GENRE = 250   # Spotify returns max 50 per search call → 5 calls per genre
OUTPUT_DIR       = "data/raw"

# ── Auth: Client Credentials flow ────────────────────────────────────────────
def get_access_token():
    """Exchange client credentials for a Bearer token. Valid for 1 hour."""
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    print("✓ Authenticated with Spotify API")
    return token


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ── Search for tracks by genre ────────────────────────────────────────────────
def fetch_tracks_for_genre(genre, token, limit=250):
    """
    Search Spotify for tracks in a given genre.
    Returns a list of track dicts (id, name, artist, popularity, etc.)
    """
    tracks   = []
    per_call = 50   # Spotify max per request
    offsets  = range(0, limit, per_call)

    for offset in offsets:
        url    = "https://api.spotify.com/v1/search"
        params = {
            "q":      f"genre:{genre}",
            "type":   "track",
            "limit":  per_call,
            "offset": offset,
            "market": "FR",          # France — relevant for target companies
        }
        resp = requests.get(url, headers=auth_header(token), params=params)

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 5))
            time.sleep(retry_after)
            resp = requests.get(url, headers=auth_header(token), params=params)

        if resp.status_code != 200:
            break

        items = resp.json().get("tracks", {}).get("items", [])
        if not items:
            break

        for item in items:
            if not item:
                continue
            tracks.append({
                "track_id":       item["id"],
                "track_name":     item["name"],
                "artist_id":      item["artists"][0]["id"] if item["artists"] else None,
                "artist_name":    item["artists"][0]["name"] if item["artists"] else None,
                "album_name":     item["album"]["name"],
                "release_date":   item["album"]["release_date"],
                "popularity":     item["popularity"],
                "duration_ms":    item["duration_ms"],
                "explicit":       item["explicit"],
                "genre":          genre,
                "market":         "FR",
            })

        time.sleep(0.2)   # Be polite to the API

    return tracks


# ── Fetch audio features for a batch of track IDs ────────────────────────────
def fetch_audio_features(track_ids, token):
    """
    Fetch audio feature vectors for up to 100 tracks per call.
    Returns a list of feature dicts.
    """
    features = []
    batch_size = 100

    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i : i + batch_size]
        url   = "https://api.spotify.com/v1/audio-features"
        resp  = requests.get(url, headers=auth_header(token), params={"ids": ",".join(batch)})

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 5))
            time.sleep(retry_after)
            resp = requests.get(url, headers=auth_header(token), params={"ids": ",".join(batch)})

        if resp.status_code != 200:
            continue

        for feat in resp.json().get("audio_features", []):
            if feat:
                features.append({
                    "track_id":          feat["id"],
                    "danceability":      feat["danceability"],      # 0–1: how suitable for dancing
                    "energy":            feat["energy"],            # 0–1: intensity & activity
                    "valence":           feat["valence"],           # 0–1: musical positiveness
                    "tempo":             feat["tempo"],             # BPM
                    "loudness":          feat["loudness"],          # dB
                    "acousticness":      feat["acousticness"],      # 0–1
                    "instrumentalness":  feat["instrumentalness"],  # 0–1
                    "liveness":          feat["liveness"],          # 0–1: live performance signal
                    "speechiness":       feat["speechiness"],       # 0–1: spoken word ratio
                    "key":               feat["key"],               # musical key 0–11
                    "mode":              feat["mode"],              # 1=major, 0=minor
                    "time_signature":    feat["time_signature"],
                    "duration_ms":       feat["duration_ms"],
                })

        time.sleep(0.1)

    return features


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    token = get_access_token()

    # 1. Collect tracks across all genres
    print(f"\nCollecting tracks across {len(GENRES)} genres...")
    all_tracks = []

    for genre in tqdm(GENRES, desc="Genres"):
        genre_tracks = fetch_tracks_for_genre(genre, token, limit=TRACKS_PER_GENRE)
        all_tracks.extend(genre_tracks)
        time.sleep(0.5)

    df_tracks = pd.DataFrame(all_tracks)
    df_tracks.drop_duplicates(subset="track_id", inplace=True)
    df_tracks.reset_index(drop=True, inplace=True)

    print(f"\n✓ Collected {len(df_tracks):,} unique tracks across {len(GENRES)} genres")

    # 2. Fetch audio features for all tracks
    print("\nFetching audio features...")
    track_ids    = df_tracks["track_id"].tolist()
    all_features = fetch_audio_features(track_ids, token)
    df_features  = pd.DataFrame(all_features)

    print(f"✓ Audio features retrieved for {len(df_features):,} tracks")

    # 3. Save to CSV
    tracks_path   = os.path.join(OUTPUT_DIR, "spotify_tracks.csv")
    features_path = os.path.join(OUTPUT_DIR, "spotify_audio_features.csv")

    df_tracks.to_csv(tracks_path, index=False)
    df_features.to_csv(features_path, index=False)

    print(f"\n✓ Saved: {tracks_path}")
    print(f"✓ Saved: {features_path}")

    # 4. Quick summary
    print("\n── Dataset Summary ──────────────────────────")
    print(f"Total tracks:          {len(df_tracks):,}")
    print(f"Unique artists:        {df_tracks['artist_id'].nunique():,}")
    print(f"Genres covered:        {df_tracks['genre'].nunique()}")
    print(f"Avg track popularity:  {df_tracks['popularity'].mean():.1f} / 100")
    print(f"Tracks with features:  {len(df_features):,}")
    print("─────────────────────────────────────────────")
    print("\nNext step: run python/01_generate_users.py")


if __name__ == "__main__":
    main()
