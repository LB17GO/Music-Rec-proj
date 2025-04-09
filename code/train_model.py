import pandas as pd
from pathlib import Path
from scipy.sparse import csr_matrix, load_npz
import scipy
from implicit.als import AlternatingLeastSquares
import pickle


# Print version of scipy
print("Scipy version:", scipy.__version__)

# --- Get the parent directory and file path ---
try:
    parent_dir = Path(__file__).resolve().parent.parent
except NameError:
    parent_dir = Path.cwd().parent  # Use current working directory if __file__ is not available

# Path to the saved user-item matrix
user_item_matrix_path = parent_dir / "data" / "user_item_matrix.npz"

# Load the user-item matrix
user_item_matrix = load_npz(user_item_matrix_path)

print(f"User-item matrix loaded from: {user_item_matrix_path}")
print(f"Matrix shape: {user_item_matrix.shape}")

# --- Train the ALS model ---
model = AlternatingLeastSquares(factors=50, regularization=0.1, iterations=20)

# Train on the loaded user-item matrix
model.fit(user_item_matrix)

print("Model training complete.")

# Save model to a file
model_path = parent_dir / "data" / "als_model.pkl"
with open(model_path, "wb") as f:
    pickle.dump(model, f)

print(f"Model saved to {model_path}")




