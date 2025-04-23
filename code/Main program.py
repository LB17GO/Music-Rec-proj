import sqlite3
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# === CONFIG ===
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

    # Optional formatting: adds a space after each comma
    df['artist_names'] = df['artist_names'].str.replace(',', ', ', regex=False)

    return df



# === Prompt user to search and select a song ===
def select_song_by_search():
    while True:
        search_term = input("\nSearch for a song or artist (partial searches are fine): ").strip()
        matches = search_tracks_by_name(search_term)

        if matches.empty:
            print("No matches found. Try a different search term.")
            continue

        print("\nFound the following songs:")
        for i, row in matches.iterrows():
            print(f"{i+1}. {row['track_name']} — {row['artist_names']}")

        try:
            index = int(input("\nEnter the number of the song you'd like to use: ")) - 1
            if 0 <= index < len(matches):
                selected_uri = matches.iloc[index]['track_uri']
                selected_name = matches.iloc[index]['track_name']
                selected_artist = matches.iloc[index]['artist_names']
                return selected_uri, f"{selected_name} — {selected_artist}"
            else:
                print("Invalid number. Try again.")
        except ValueError:
            print("Please enter a valid number.")


# === Get features for all songs ===
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
def recommend_similar_songs(selected_song_uri, all_songs_df, top_n=5):
    feature_columns = [
        'danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness',
        'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo', 'time_signature'
    ]
    
    selected_song = all_songs_df[all_songs_df['track_uri'] == selected_song_uri]
    rest_songs = all_songs_df[all_songs_df['track_uri'] != selected_song_uri]

    selected_features = selected_song[feature_columns].to_numpy()
    rest_features = rest_songs[feature_columns].to_numpy()

    similarities = cosine_similarity(selected_features, rest_features)[0]

    rest_songs = rest_songs.copy()
    rest_songs['similarity'] = similarities
    recommendations = rest_songs.sort_values(by='similarity', ascending=False).head(top_n)

    return recommendations[['track_name', 'artist_names', 'similarity']]


# === MAIN PROGRAM ===
def main():
    while True:
        print("🎵 Welcome to the Music Recommender 🎵")
        
        selected_uri, selected_name = select_song_by_search()
        print(f"\nYou selected: {selected_name}")

        all_songs = get_all_song_features()
        recommendations = recommend_similar_songs(selected_uri, all_songs)

        print("\n=== Recommended Songs ===")
        for i, row in recommendations.iterrows():
            print(f"{row['track_name']} — {row['artist_names']} (Similarity Score: {row['similarity']:.4f})")
    
main()
