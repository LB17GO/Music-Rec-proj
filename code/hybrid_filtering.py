import pandas as pd
from pathlib import Path
from content_based_filtering import recommend_similar_songs, get_all_song_features
from collaborative_filtering import recommend_top_n_tracks

# === CONFIG ===
# You can tune these weights
CONTENT_WEIGHT = 0.3
COLLAB_WEIGHT = 0.7

# === HELPER FUNCTIONS ===

import numpy as np
import scipy.sparse as sp

def add_new_user(user_liked_track_uris, interaction_matrix, uri_to_index):
    """
    Adds a new user to the interaction matrix based on liked track URIs.
    Only adds interactions for songs already in the dataset.
    
    Args:
        user_liked_track_uris (list of str): List of track URIs the user likes.
        interaction_matrix (scipy.sparse.csr_matrix): The current user-item interaction matrix.
        uri_to_index (dict): Mapping from track URI (string) to column index (int) in the matrix.

    Returns:
        updated_matrix (csr_matrix): Interaction matrix with the new user added.
        new_user_idx (int): The index of the new user in the matrix.
    """
    # Step 1: Create a new empty row
    n_items = interaction_matrix.shape[1]
    new_user_data = np.zeros(n_items)

    # Step 2: Fill in known liked songs
    for uri in user_liked_track_uris:
        track_id = uri.replace("spotify:track:", "")
        if track_id in uri_to_index:
            idx = uri_to_index[track_id]
            new_user_data[idx] = 1
        else:
            print(f"⚠️ Warning: Track {track_id} not found in dataset, skipping.")

    # Step 3: Append the new user row to the interaction matrix
    new_user_sparse = sp.csr_matrix(new_user_data.reshape(1, -1))
    updated_matrix = sp.vstack([interaction_matrix, new_user_sparse])

    new_user_idx = updated_matrix.shape[0] - 1  # New user's index

    return updated_matrix, new_user_idx


def normalize_scores(df, score_col):
    """Normalize scores to [0,1] range."""
    min_score = df[score_col].min()
    max_score = df[score_col].max()
    if max_score - min_score == 0:
        return df.assign(normalized_score=1.0)
    df['normalized_score'] = (df[score_col] - min_score) / (max_score - min_score)
    return df

def hybrid_recommend(selected_uris, top_n=10, interaction_matrix=None, uri_to_index=None, playlist_to_index=None):
    print("🔍 Running hybrid recommendation...")

    # --- Get content-based recommendations ---
    all_songs = get_all_song_features()  # Retrieve all song features
    content_recs = recommend_similar_songs(selected_uris, all_songs, top_n=50)
    content_recs = normalize_scores(content_recs, 'similarity')
    content_recs = content_recs[['track_uri', 'normalized_score']].rename(columns={'normalized_score': 'content_score'})

    # --- Get collaborative recommendations ---
    collaborative_recs_list = []
    for uri in selected_uris:
        try:
            collab_recs = recommend_top_n_tracks(uri.strip("spotify:track:"), n=50)
            for track_uri, score in collab_recs:
                collaborative_recs_list.append({'track_uri': track_uri, 'collab_score': score})
        except Exception as e:
            print(f"Warning: Collaborative filtering failed for {uri}: {e}")
    
    if collaborative_recs_list:
        collaborative_recs = pd.DataFrame(collaborative_recs_list)
        collaborative_recs = normalize_scores(collaborative_recs, 'collab_score')
        collaborative_recs = collaborative_recs[['track_uri', 'normalized_score']].rename(columns={'normalized_score': 'collab_score'})
    else:
        # Create an empty DataFrame with the expected structure
        collaborative_recs = pd.DataFrame(columns=['track_uri', 'collab_score'])

    # --- Handle new user (fallback to content-based and add to dataset) ---
    if not collaborative_recs.empty:
        # If collaborative filtering has failed for the user (or new user), we need to add them to the system
        print("⚠️ Collaborative filtering failed for some or all tracks, adding new user data...")

        # Add the new user to the dataset
        if playlist_to_index is not None and uri_to_index is not None and interaction_matrix is not None:
            interaction_matrix, playlist_to_index, new_user_id = add_new_user(selected_uris, interaction_matrix, uri_to_index, playlist_to_index)
        else:
            print("Error: Missing required data to add new user.")
    
    # --- Merge results ---
    merged = pd.merge(content_recs, collaborative_recs, on='track_uri', how='outer').fillna(0)

    # --- Weighted sum ---
    merged['hybrid_score'] = CONTENT_WEIGHT * merged['content_score'] + COLLAB_WEIGHT * merged['collab_score']

    # --- Sort and output top N ---
    final_recs = merged.sort_values(by='hybrid_score', ascending=False).head(top_n)
    return final_recs['track_uri'].tolist()



# === MAIN PROGRAM ===
if __name__ == "__main__":
    # Example: Pass some Spotify Track URIs
    track_uris = ["spotify:track:0NpvdCO506uO58D4AbKzki", "spotify:track:59lq75uFIqzUZcgZ4CbqFG", "spotify:track:6F5c58TMEs1byxUstkzVeM"]
    recommended_uris = hybrid_recommend(track_uris, top_n=10)
    print("\n🎯 Final Recommended Spotify URIs:")
    for uri in recommended_uris:
        print(f"https://open.spotify.com/track/{uri.strip('spotify:track:')}")
