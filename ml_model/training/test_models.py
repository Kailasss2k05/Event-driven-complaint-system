import os
import joblib
from sentence_transformers import SentenceTransformer

# ==============================
# Paths
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "..", "saved_models")

CATEGORY_DIR = os.path.join(MODELS_DIR, "Category")
PRIORITY_DIR = os.path.join(MODELS_DIR, "Priority")

# ==============================
# Load Models
# ==============================
category_model = joblib.load(
    os.path.join(CATEGORY_DIR, "category_model.pkl")
)

priority_model = joblib.load(
    os.path.join(PRIORITY_DIR, "priority_model.pkl")
)

# Load transformer directly
embedder = SentenceTransformer("all-MiniLM-L6-v2")

print("\n Models loaded successfully")

# ==============================
# Testing Loop
# ==============================
while True:

    text = input("\nEnter complaint (type exit to stop): ")

    if text.lower() == "exit":
        break

    emb = embedder.encode([text])

    category = category_model.predict(emb)[0]
    priority = priority_model.predict(emb)[0]

    print("\nPrediction Result")
    print("-------------------")
    print("Category :", category)
    print("Priority :", priority)