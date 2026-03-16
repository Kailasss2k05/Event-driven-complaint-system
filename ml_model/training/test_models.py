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
# 3. Severity + Eisenhower Priority Detection
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

URGENT_WORDS = [
    "urgent", "immediately", "immediate", "asap", "right now", "today",
    "danger", "dangerous", "risk", "emergency", "critical", "blocked"
]

IMPORTANT_WORDS = [
    "hospital", "school", "children", "elderly", "public safety",
    "drinking water", "contamination", "disease", "injury", "accident",
    "main road", "high traffic", "community"
]


def has_any_keyword(text, keywords):
    return any(word in text for word in keywords)


def detect_severity(text):

    text = text.lower()

    for word in CRITICAL_WORDS:
        if word in text:
            return "Critical"

    for word in MEDIUM_WORDS:
        if word in text:
            return "Medium"

    return "Low"


def eisenhower_priority(text, severity, model_priority):

    text = text.lower()
    model_priority = str(model_priority).upper()

    is_urgent = has_any_keyword(text, URGENT_WORDS)
    is_important = has_any_keyword(text, IMPORTANT_WORDS)

    if severity == "Critical":
        is_urgent = True
        is_important = True
    elif severity == "Medium":
        is_urgent = True

    if is_urgent and is_important:
        return "DO_FIRST", "CRITICAL"
    if (not is_urgent) and is_important:
        return "SCHEDULE", "HIGH"
    if is_urgent and (not is_important):
        return "DELEGATE", "MEDIUM"

    # Eliminate quadrant: fall back to ML model.
    if model_priority in {"HIGH", "CRITICAL"}:
        return "ELIMINATE", "HIGH"
    if model_priority in {"MEDIUM", "NORMAL"}:
        return "ELIMINATE", "MEDIUM"
    return "ELIMINATE", "LOW"


# ==============================
# 4. Testing Loop
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

    # Priority Prediction — text only, no severity column needed
    emb_priority = embedder.encode([text.lower()])

    model_priority = priority_model.predict(emb_priority)[0]
    quadrant, priority = eisenhower_priority(text, severity, model_priority)

    print("\nPrediction Result")
    print("-------------------")
    print("Category :", category)
    print("Severity :", severity)
    print("Quadrant :", quadrant)
    print("Model Priority :", str(model_priority).upper())
    print("Final Priority :", priority)