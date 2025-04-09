import pandas as pd
from pathlib import Path
from scipy.sparse import csr_matrix, load_npz
import scipy
from implicit.als import AlternatingLeastSquares
import pickle

# --- Get the parent directory and file path ---
try:
    parent_dir = Path(__file__).resolve().parent.parent
except NameError:
    parent_dir = Path.cwd().parent  # Use current working directory if __file__ is not available

model_path = parent_dir / "data" / "als_model.pkl"
# Path to the saved user-item matrix
user_item_matrix_path = parent_dir / "data" / "user_item_matrix.npz"

# Load the user-item matrix
user_item_matrix = load_npz(user_item_matrix_path)

# Load model from file
with open(model_path, "rb") as f:
    model = pickle.load(f)

print("Model loaded from saved file.")


def recommend_top_n_songs(user_id, n=5):
    if user_id >= user_item_matrix.shape[0]:
        raise ValueError(f"user_id {user_id} is out of bounds.")
    if user_item_matrix[user_id].nnz == 0:
        raise ValueError(f"user_id {user_id} has no liked songs.")

    # Create a 2D CSR matrix with only this user's interactions
    single_user_matrix = user_item_matrix[user_id]
    if not isinstance(single_user_matrix, csr_matrix):
        single_user_matrix = csr_matrix(single_user_matrix)

    # Fix: model.recommend expects the matrix to have shape (1, num_items)
    # But slicing returns shape (1, num_items) with shared backing — safer to copy
    single_user_matrix = csr_matrix(single_user_matrix.toarray())

    # Get top N recommendations for the user
    recommendations = model.recommend(
        userid=0,  # We’re only passing 1 row, so its index is 0
        user_items=single_user_matrix,
        N=n,
        filter_already_liked_items=True
    )

    return recommendations

# Example usage
example_user_id = 886379  # Set to the example user ID you're working with

# Get top 5 recommended songs for the example user
top_recs = recommend_top_n_songs(example_user_id, n=5)


print("Raw recommendations:", top_recs)
print("Type of first element:", type(top_recs[0]))


# Unpack recommendations outside the loop and print results
rec_song_ids = top_recs[0]
rec_song_scores = top_recs[1]
for i in range(len(rec_song_ids)):
    #Print recommended song ids and scores
    print(f"Recommended song ID: {rec_song_ids[i]}, Score: {rec_song_scores[i]}")




