import os
import joblib
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

# ==============================
# Global Variables
# ==============================
category_model = None
priority_model = None
embedder = None
models_ready = False


# ==============================
# Load Models Function
# ==============================
def load_models():

    global category_model
    global priority_model
    global embedder
    global models_ready

    print("Loading ML models...")

    BASE_DIR = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )

    category_path = os.path.join(
        BASE_DIR,
        "ml_model",
        "saved_models",
        "Category",
        "category_model.pkl"
    )

    priority_path = os.path.join(
        BASE_DIR,
        "ml_model",
        "saved_models",
        "Priority",
        "priority_model.pkl"
    )

    embedding_path = os.path.join(
        BASE_DIR,
        "ml_model",
        "saved_models",
        "Category",
        "embedding.txt"
    )

    # Validate that model files exist
    for path, name in [
        (category_path, "Category model"),
        (priority_path, "Priority model"),
        (embedding_path, "Embedding config")
    ]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{name} not found at {path}. "
                "Run the training scripts first."
            )

    # Load model packages
    category_package = joblib.load(category_path)
    priority_package = joblib.load(priority_path)

    category_model = category_package["model"]
    priority_model = priority_package["model"]

    # Load embedder name
    with open(embedding_path, "r") as f:
        embedder_name = f.read().strip()

    embedder = SentenceTransformer(
        embedder_name,
        device=os.getenv("MODEL_DEVICE")
    )

    # Warmup (removes first prediction delay)
    embedder.encode(["warmup"])

    models_ready = True
    print("Models loaded successfully!")

DEPARTMENT_MAP = {

    # Engineering Department
    "Road Issues": "Engineering Department",
    "Drainage & Buildings": "Engineering Department",
    "Street Lighting & Electrical Works": "Engineering Department",
    "Public Infrastructure Maintenance": "Engineering Department",
    "Building Permits & Violations": "Engineering Department",
    "Water Supply Infrastructure": "Engineering Department",

    # Health Department
    "Solid Waste Management": "Health Department",
    "Public Health & Sanitation": "Health Department",
    "Vector Control & Disease Prevention": "Health Department",
    "Biomedical & Hazardous Waste": "Health Department",
    "Food Safety & Hygiene": "Health Department",
    "Public Toilet & Washroom Maintenance": "Health Department",
    "Animal & Stray Control": "Health Department",

    # Revenue Department
    "Property Tax": "Revenue Department",
    "Other Taxes": "Revenue Department",
    "Trade License & Renewal": "Revenue Department",
    "Advertisement & Hoarding Permissions": "Revenue Department",
    "Birth & Death Certificates": "Revenue Department",
    "Land & Ownership Records": "Revenue Department",
    "Online Payment & Portal Issues": "Revenue Department"
}

# ==============================
# Severity Detection
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


def detect_severity(text: str) -> str:
    text_lower = text.lower()
    for word in CRITICAL_WORDS:
        if word in text_lower:
            return "Critical"
    for word in MEDIUM_WORDS:
        if word in text_lower:
            return "Medium"
    return "Low"


def safety_priority_override(text: str, predicted_priority: str) -> str:
    text_lower = text.lower()
    for word in CRITICAL_WORDS:
        if word in text_lower:
            return "High"
    return predicted_priority


# ==============================
# Prediction Function
# ==============================
def predict_complaint(text: str):
    
    global models_ready

    if not models_ready:
        load_models()

    # Category prediction uses raw text
    emb_category = embedder.encode([text], convert_to_numpy=True)
    category = category_model.predict(emb_category)[0]

    # Priority prediction uses text + severity (matches training data format)
    severity = detect_severity(text)
    priority_input = text.lower() + " " + severity
    emb_priority = embedder.encode([priority_input], convert_to_numpy=True)
    priority = priority_model.predict(emb_priority)[0]
    priority = safety_priority_override(text, priority)

    department = DEPARTMENT_MAP.get(category, "General Department")

    return {
        "category": category,
        "priority": priority,
        "department": department
    }