import pandas as pd
from pathlib import Path
from scipy.sparse import csr_matrix, load_npz
from implicit.als import AlternatingLeastSquares
import pickle
import json

# --- Define paths ---
try:
    parent_dir = Path(__file__).resolve().parent.parent
except NameError:
    parent_dir = Path.cwd().parent

model_path = parent_dir / "data" / "als_model.pkl"
matrix_path = parent_dir / "data" / "user_item_matrix.npz"
playlist_map_path = parent_dir / "data" / "playlist_id_map.json"
track_map_path = parent_dir / "data" / "track_id_map.json"

# --- Load components ---
user_item_matrix = load_npz(matrix_path)
with open(model_path, "rb") as f:
    model = pickle.load(f)
with open(playlist_map_path) as f:
    playlist_map = json.load(f)
with open(track_map_path) as f:
    track_map = json.load(f)

# Create reverse track mapping
reverse_track_map = {v: k for k, v in track_map.items()}

print("Model, matrix, and mappings loaded.")


def recommend_top_n_tracks(playlist_id, n=5):
    if playlist_id not in playlist_map:
        raise ValueError(f"Playlist ID '{playlist_id}' not found in mapping.")

    internal_user_id = playlist_map[playlist_id]

    if internal_user_id >= user_item_matrix.shape[0]:
        raise ValueError(f"Mapped user_id {internal_user_id} is out of bounds.")
    if user_item_matrix[internal_user_id].nnz == 0:
        raise ValueError(f"Playlist ID {playlist_id} has no liked songs.")

    user_vector = user_item_matrix[internal_user_id]
    user_vector = csr_matrix(user_vector.toarray())  # Ensure proper shape

    internal_song_ids, scores = model.recommend(
        userid=2,
        user_items=user_vector,
        N=n,
        filter_already_liked_items=True
    )

    recommended = []
    for internal_song_id, score in zip(internal_song_ids, scores):
        real_song_id = reverse_track_map.get(internal_song_id)
        recommended.append((real_song_id, score))

    return recommended

top_recs = recommend_top_n_tracks("1PwREqLT1uU8mbSavX9Hpm", n=5)
# Unpack recommendations outside the loop and print results
for i in range(len(top_recs)):
    #Print recommended song ids and scores
    print(f"Recommended song ID: {top_recs[i][0]}, Score: {top_recs[i][1]}")
    print(f"Recommended song link: https://open.spotify.com/track/{top_recs[i][0]}")






