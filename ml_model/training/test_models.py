import os
import joblib
from sentence_transformers import SentenceTransformer

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "..", "saved_models")

CATEGORY_DIR = os.path.join(MODELS_DIR, "Category")
PRIORITY_DIR = os.path.join(MODELS_DIR, "Priority")

# Load Models
category_model = joblib.load(
    os.path.join(CATEGORY_DIR, "category_model.pkl")
)

priority_model = joblib.load(
    os.path.join(PRIORITY_DIR, "priority_model.pkl")
)

embedder = SentenceTransformer("all-mpnet-base-v2")
print("\nModels loaded successfully")

# Safety Keywords
DANGER_WORDS = [
    "electric", "shock", "fire",
    "accident", "danger",
    "collapse", "open manhole",
    "sewage overflow", "gas leak"
]

def safety_priority_override(text, predicted_priority):
    text = text.lower()

    for word in DANGER_WORDS:
        if word in text:
            return "High"

    return predicted_priority


while True:

    text = input("\nEnter complaint (type exit to stop): ")

    if text.lower() == "exit":
        break

    emb_category = embedder.encode([text])
    category = category_model.predict(emb_category)[0]

    severity = input("Enter Severity (Low/Medium/Critical): ")

    priority_input = text.lower() + " " + severity.lower()
    emb_priority = embedder.encode([priority_input])

    priority = priority_model.predict(emb_priority)[0]

    priority = safety_priority_override(text, priority)

    print("\nPrediction Result")
    print("-------------------")
    print("Category :", category)
    print("Priority :", priority)