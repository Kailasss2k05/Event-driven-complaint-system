import os
import joblib
from sentence_transformers import SentenceTransformer


# ==============================
# 1. Paths
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "..", "saved_models")

CATEGORY_DIR = os.path.join(MODELS_DIR, "Category")
PRIORITY_DIR = os.path.join(MODELS_DIR, "Priority")


# ==============================
# 2. Load Models
# ==============================

category_package = joblib.load(
    os.path.join(CATEGORY_DIR, "category_model.pkl")
)

priority_package = joblib.load(
    os.path.join(PRIORITY_DIR, "priority_model.pkl")
)

category_model = category_package["model"]
priority_model = priority_package["model"]


embedder = SentenceTransformer("all-mpnet-base-v2")

print("\nModels loaded successfully")


# ==============================
# 3. Severity Auto Detection
# ==============================

CRITICAL_WORDS = [
    "fire", "electric", "shock",
    "accident", "collapse",
    "open manhole", "gas leak"
]

MEDIUM_WORDS = [
    "leakage", "sewage",
    "damaged road", "overflow"
]


def detect_severity(text):

    text = text.lower()

    for word in CRITICAL_WORDS:
        if word in text:
            return "Critical"

    for word in MEDIUM_WORDS:
        if word in text:
            return "Medium"

    return "Low"


# ==============================
# 4. Safety Override
# ==============================

def safety_priority_override(text, predicted_priority):

    text = text.lower()

    for word in CRITICAL_WORDS:
        if word in text:
            return "High"

    return predicted_priority


# ==============================
# 5. Testing Loop
# ==============================

while True:

    text = input("\nEnter complaint (type exit to stop): ")

    if text.lower() == "exit":
        break

    # Category Prediction
    emb_category = embedder.encode([text])
    category = category_model.predict(emb_category)[0]

    # Auto Severity
    severity = detect_severity(text)

    # Priority Prediction
    priority_input = text.lower() + " " + severity.lower()
    emb_priority = embedder.encode([priority_input])

    priority = priority_model.predict(emb_priority)[0]
    priority = safety_priority_override(text, priority)

    print("\nPrediction Result")
    print("-------------------")
    print("Category :", category)
    print("Priority :", priority)