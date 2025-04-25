import sqlite3
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler


DB_FILE = "music_recommender.sqlite"

# === CONNECT TO DB ===
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# === Search songs by name with artist included ===
def search_tracks_by_name(partial_name, limit=10):
    query = '''
        SELECT t.track_uri, t.track_name, GROUP_CONCAT(DISTINCT a.artist_name) AS artist_names
        FROM tracks t
        JOIN track_artists ta ON t.track_uri = ta.track_uri
        JOIN artists a ON ta.artist_uri = a.artist_uri
        WHERE t.track_name LIKE ?
        GROUP BY t.track_uri
        ORDER BY t.track_name ASC
        LIMIT ?
    '''
    param = f'%{partial_name}%'
    df = pd.read_sql_query(query, conn, params=(param, limit))
    df['artist_names'] = df['artist_names'].str.replace(',', ', ', regex=False)
    return df

# === Prompt user to search and select multiple songs ===
def select_multiple_songs():
    selected_uris = []
    selected_names = []

    print("\n🎵 Select multiple songs to base your recommendations on! 🎵")
    print("Type 'done' when you have finished selecting songs.\n")

    while True:
        search_term = input("\nSearch for a song or artist (or type 'done'): ").strip()
        if search_term.lower() == 'done':
            if len(selected_uris) == 0:
                print("You must select at least one song before finishing.")
                continue
            else:
                break

        matches = search_tracks_by_name(search_term)

        if matches.empty:
            print("No matches found. Try a different search term.")
            continue

        print("\nFound the following songs:")
        for i, row in matches.iterrows():
            print(f"{i+1}. {row['track_name']} — {row['artist_names']}")

        try:
            index = int(input("\nEnter the number of the song you'd like to add: ")) - 1
            if 0 <= index < len(matches):
                selected_uri = matches.iloc[index]['track_uri']
                selected_name = f"{matches.iloc[index]['track_name']} — {matches.iloc[index]['artist_names']}"
                selected_uris.append(selected_uri)
                selected_names.append(selected_name)
                print(f"✅ Added: {selected_name}")
            else:
                print("Invalid number. Try again.")
        except ValueError:
            print("Please enter a valid number.")

    return selected_uris, selected_names

# Get all songs and their features 
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

# Compute Cosine Similarity 
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

# MAIN PROGRAM 
def main():
    print("🎵 Welcome to the Music Recommender 🎵")

    all_songs = get_all_song_features()

    while True:
        selected_uris, selected_names = select_multiple_songs()
        print("\nYou selected:")
        for name in selected_names:
            print(f"- {name}")

        recommendations = recommend_similar_songs(selected_uris, all_songs)

        print("\n=== Recommended Songs ===")
        for i, row in recommendations.iterrows():
            print(f"{row['track_name']} — {row['artist_names']} (Similarity Score: {row['similarity']:.4f})")

main()
