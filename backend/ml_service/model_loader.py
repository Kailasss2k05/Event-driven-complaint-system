import os
import joblib
from sentence_transformers import SentenceTransformer

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

    # Load model packages
    category_package = joblib.load(category_path)
    priority_package = joblib.load(priority_path)

    category_model = category_package["model"]
    priority_model = priority_package["model"]

    # Load embedder name
    with open(embedding_path, "r") as f:
        embedder_name = f.read().strip()

    embedder = SentenceTransformer(embedder_name, device="cpu")

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
# Prediction Function
# ==============================
def predict_complaint(text: str):
    
    global models_ready

    if not models_ready:
        load_models()

    emb = embedder.encode([text], convert_to_numpy=True)

    category = category_model.predict(emb)[0]
    priority = priority_model.predict(emb)[0]

    department = DEPARTMENT_MAP.get(category, "General Department")

    return {
        "category": category,
        "priority": priority,
        "department": department
    }