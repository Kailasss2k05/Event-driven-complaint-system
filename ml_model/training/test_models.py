import os
import joblib

# ==============================
# 1. Paths
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODELS_DIR = os.path.join(
    BASE_DIR,
    "..",
    "saved_models"
)

# ==============================
# 2. Load Models
# ==============================

category_model = joblib.load(
    os.path.join(MODELS_DIR, "category_model.pkl")
)

embedder = joblib.load(
    os.path.join(MODELS_DIR, "transformer_embedder.pkl")
)

print("\nModel Classes:", category_model.classes_)

# ==============================
# 3. Prediction Loop
# ==============================

while True:

    user_input = input("\nEnter complaint (type exit to stop): ")

    if user_input.lower() == "exit":
        break

    X_emb = embedder.encode([user_input])

    category_pred = category_model.predict(X_emb)[0]

    print("\nPrediction Result")
    print("Category :", category_pred)