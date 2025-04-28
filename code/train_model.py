import pandas as pd
from pathlib import Path
from scipy.sparse import load_npz
import scipy
from implicit.als import AlternatingLeastSquares
import pickle
import json

def main():
    # Print version of scipy
    print("Scipy version:", scipy.__version__)

    # --- Get paths ---
    try:
        parent_dir = Path(__file__).resolve().parent.parent
    except NameError:
        parent_dir = Path.cwd().parent

    matrix_path = parent_dir / "data" / "user_item_matrix.npz"
    model_path = parent_dir / "data" / "als_model.pkl"

    # --- Load matrix ---
    user_item_matrix = load_npz(matrix_path)
    print(f"Matrix loaded. Shape: {user_item_matrix.shape}")

    # --- Train ALS model ---
    model = AlternatingLeastSquares(factors=50, regularization=0.1, iterations=20)
    model.fit(user_item_matrix)
    print("ALS training complete.")

    # --- Save model ---
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"Model saved to {model_path}")

main()