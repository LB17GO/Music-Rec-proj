from scipy.sparse import save_npz
from pathlib import Path
from scipy.sparse import csr_matrix
import pandas as pd

# --- Load the data ---
try:
    parent_dir = Path(__file__).resolve().parent.parent
except NameError:
    parent_dir = Path.cwd().parent

csv_path = parent_dir / "data" / "user_data.csv"
user_data = pd.read_csv(csv_path)
print("Columns in CSV:", user_data.columns)

# --- Preprocess IDs and binary likes ---
user_data["user_id"] -= user_data["user_id"].min()
user_data["song_id"] -= user_data["song_id"].min()
user_data["liked"] = user_data["liked"].apply(lambda x: 1 if x != 0 else 0)

# --- Get matrix dimensions ---
num_users = user_data["user_id"].max() + 1
num_songs = user_data["song_id"].max() + 1

# --- Create user-item matrix with correct shape ---
user_item_matrix = csr_matrix(
    (user_data["liked"], (user_data["user_id"], user_data["song_id"])),
    shape=(num_users, num_songs)
)

# --- Ensure matrix is in CSR format ---
user_item_matrix = user_item_matrix.tocsr()

# --- Create item-user matrix for training ---
item_user_matrix = user_item_matrix.T.tocsr()

# Save the user-item matrix to a file (compressed .npz format)
save_path = parent_dir / "data" / "user_item_matrix.npz"
save_npz(save_path, user_item_matrix)

print(f"User-item matrix saved to: {save_path}")
