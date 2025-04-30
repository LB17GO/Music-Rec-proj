import pandas as pd
from pathlib import Path
from content_based_filtering import recommend_similar_songs, get_all_song_features
from collaborative_filtering import recommend_top_n_tracks
from pathlib import Path
import create_matrix
import train_model
import sys
import os
sys.stdout.reconfigure(line_buffering=True)
import json

#constants
USER_DATA = str(Path(__file__).resolve().parent / "../data/playlist_track_dataset.csv")
CONTENT_WEIGHT = 0.3
COLLAB_WEIGHT = 0.7

# === HELPER FUNCTIONS ===

import numpy as np
import scipy.sparse as sp

def add_new_user(user_id, liked_tracks):
    #print("Adding new user to dataset...")
    for track in liked_tracks:
        #Add user id and track id to user_data.csv
        with open(USER_DATA, 'a') as f:
            f.write(f"{user_id},{track}\n")



def normalize_scores(df, score_col):
    """Normalize scores to [0,1] range."""
    min_score = df[score_col].min()
    max_score = df[score_col].max()
    if max_score - min_score == 0:
        return df.assign(normalized_score=1.0)
    df['normalized_score'] = (df[score_col] - min_score) / (max_score - min_score)
    return df

def hybrid_recommend(user_id, selected_uris, top_n=10, uri_to_index=None, playlist_to_index=None):
    #print("🔍 Running hybrid recommendation...")

    # --- Get content-based recommendations ---
    all_songs = get_all_song_features()  # Retrieve all song features
    content_recs = recommend_similar_songs(selected_uris, all_songs, top_n=50)
    content_recs = normalize_scores(content_recs, 'similarity')
    content_recs = content_recs[['track_uri', 'normalized_score']].rename(columns={'normalized_score': 'content_score'})

    # --- Get collaborative recommendations ---
    collaborative_recs_list = []
    for uri in selected_uris:
        #print(collaborative_recs_list)
        try:
            collab_recs = recommend_top_n_tracks(uri.strip("spotify:track:"), n=50)
            for track_uri, score in collab_recs:
                collaborative_recs_list.append({'track_uri': track_uri, 'collab_score': score})
        except Exception as e:
            pass
            #print(f"Warning: Collaborative filtering failed for {uri}: {e}")
    
    if collaborative_recs_list:
        #print("Collaborative recommendations found.")
        collaborative_recs = pd.DataFrame(collaborative_recs_list)
        collaborative_recs = normalize_scores(collaborative_recs, 'collab_score')
        collaborative_recs = collaborative_recs[['track_uri', 'normalized_score']].rename(columns={'normalized_score': 'collab_score'})
        # --- Merge results ---
        merged = pd.merge(content_recs, collaborative_recs, on='track_uri', how='outer').fillna(0)

        # --- Weighted sum ---
        merged['hybrid_score'] = CONTENT_WEIGHT * merged['content_score'] + COLLAB_WEIGHT * merged['collab_score']

        # --- Sort and output top N ---
        final_recs = merged.sort_values(by='hybrid_score', ascending=False).head(top_n)
        
    else:
        #print("⚠️ Collaborative filtering failed for some or all tracks, adding new user data...")

        # Add the new user to the dataset
        add_new_user(user_id, selected_uris)
        create_matrix.main()
        train_model.main()
        final_recs = content_recs.sort_values(by='content_score', ascending=False).head(top_n)
        
    return final_recs['track_uri'].tolist()
        
    



# === MAIN PROGRAM ===
if __name__ == "__main__":
    user_id = "new_user"

    # Construct path relative to script location
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(BASE_DIR, '..', 'Website', 'data', 'web_top_songs.csv')

    try:
        df = pd.read_csv(csv_path)
        track_uris = ["spotify:track:" + tid for tid in df['id'].tolist()]

        recommended_uris = hybrid_recommend(user_id, track_uris, top_n=10)
        clean_ids = [uri.replace("spotify:track:", "") for uri in recommended_uris]

        print(json.dumps(clean_ids))  # ✅ Final JSON output for Node.js

    except Exception as e:
        print(f"Recommendation error: {str(e)}", file=sys.stderr)
        sys.exit(1)

#print("running hybrid")