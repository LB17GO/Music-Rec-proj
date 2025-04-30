import sqlite3
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from pathlib import Path

# === CONFIG ===
DB_FILE = str(Path(__file__).resolve().parent / "../data/music_recommender.sqlite")

# === CONNECT TO DB ===
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# === Get song names from URIs ===
def get_song_names_from_uris(uris):
    placeholders = ', '.join(['?'] * len(uris))
    query = f'''
        SELECT t.track_uri, t.track_name, GROUP_CONCAT(DISTINCT a.artist_name) AS artist_names
        FROM tracks t
        JOIN track_artists ta ON t.track_uri = ta.track_uri
        JOIN artists a ON ta.artist_uri = a.artist_uri
        WHERE t.track_uri IN ({placeholders})
        GROUP BY t.track_uri
    '''
    df = pd.read_sql_query(query, conn, params=uris)
    df['artist_names'] = df['artist_names'].str.replace(',', ', ', regex=False)
    return df

# === Get all songs and their features ===
def get_all_song_features():
    query = '''
        SELECT t.track_uri, t.track_name,
               GROUP_CONCAT(DISTINCT a.artist_name) AS artist_names,
               af.danceability, af.energy, af.key, af.loudness, af.mode,
               af.speechiness, af.acousticness, af.instrumentalness, af.liveness,
               af.valence, af.tempo, af.time_signature
        FROM tracks t
        JOIN audio_features af ON t.track_uri = af.track_uri
        JOIN track_artists ta ON t.track_uri = ta.track_uri
        JOIN artists a ON ta.artist_uri = a.artist_uri
        GROUP BY t.track_uri
    '''
    df = pd.read_sql_query(query, conn)
    df['artist_names'] = df['artist_names'].str.replace(',', ', ', regex=False)
    return df

# === Compute Cosine Similarity ===
def recommend_similar_songs(selected_song_uris, all_songs_df, top_n=5):
    feature_columns = [
        'danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness',
        'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature'
    ]

    selected_songs = all_songs_df[all_songs_df['track_uri'].isin(selected_song_uris)]
    rest_songs = all_songs_df[~all_songs_df['track_uri'].isin(selected_song_uris)]

    selected_features = selected_songs[feature_columns].to_numpy()
    rest_features = rest_songs[feature_columns].to_numpy()

    # Normalize features
    scaler = MinMaxScaler()
    rest_features = scaler.fit_transform(rest_features)
    selected_features = scaler.transform(selected_features)

    # Average selected songs' features into a single vector
    averaged_features = np.mean(selected_features, axis=0).reshape(1, -1)

    similarities = cosine_similarity(averaged_features, rest_features)[0]

    rest_songs = rest_songs.copy()
    rest_songs['similarity'] = similarities
    recommendations = rest_songs.sort_values(by='similarity', ascending=False).head(top_n)

    return recommendations

# === MAIN PROGRAM ===
def main(selected_uris):
    #print("🎵 Welcome to the Music Recommender 🎵")
    all_songs = get_all_song_features()

    selected_df = get_song_names_from_uris(selected_uris)

    #if selected_df.empty:
        #print("❌ None of the selected track URIs were found in the database.")
        #return

    #print("\nYou selected:")
    #for _, row in selected_df.iterrows():
        #print(f"- {row['track_name']} — {row['artist_names']}")

    recommendations = recommend_similar_songs(selected_uris, all_songs)

    #print("\n=== Recommended Songs ===")
    #for _, row in recommendations.iterrows():
        #print(f"{row['track_name']} — {row['artist_names']} (Similarity Score: {row['similarity']:.4f})")


# === Example Usage ===
if __name__ == "__main__":
    # Replace with real track URIs from your DB
    track_uris = ["spotify:track:0NpvdCO506uO58D4AbKzki", "spotify:track:59lq75uFIqzUZcgZ4CbqFG", "spotify:track:6F5c58TMEs1byxUstkzVeM"]
    main(track_uris)
