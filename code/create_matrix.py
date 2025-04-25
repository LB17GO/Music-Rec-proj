from pathlib import Path
from scipy.sparse import csr_matrix, save_npz
import pandas as pd
import json

# --- Load the data ---
try:
    parent_dir = Path(__file__).resolve().parent.parent
except NameError:
    parent_dir = Path.cwd().parent

csv_path = parent_dir / "data" / "playlist_track_dataset.csv"
user_data = pd.read_csv(csv_path)
print("Columns in CSV:", user_data.columns)

# Rename columns if needed
user_data.columns = ["playlist_id", "track_id"]

# --- Generate unique mappings ---
playlist_ids = user_data["playlist_id"].unique()
track_ids = user_data["track_id"].unique()

playlist_mapping = {pid: idx for idx, pid in enumerate(playlist_ids)}
track_mapping = {tid: idx for idx, tid in enumerate(track_ids)}

# Save the mappings
with open(parent_dir / "data" / "playlist_id_map.json", "w") as f:
    json.dump(playlist_mapping, f)
with open(parent_dir / "data" / "track_id_map.json", "w") as f:
    json.dump(track_mapping, f)

# --- Apply mappings ---
user_data["user_id"] = user_data["playlist_id"].map(playlist_mapping)
user_data["song_id"] = user_data["track_id"].map(track_mapping)

# Add implicit feedback value
user_data["liked"] = 1  # every (playlist, track) pair is considered a "like"

# --- Create user-item matrix ---
num_users = len(playlist_mapping)
num_songs = len(track_mapping)

user_item_matrix = csr_matrix(
    (user_data["liked"], (user_data["user_id"], user_data["song_id"])),
    shape=(num_users, num_songs)
)

# --- Save matrix ---
save_path = parent_dir / "data" / "user_item_matrix.npz"
save_npz(save_path, user_item_matrix)

print(f"User-item matrix saved to: {save_path}")
