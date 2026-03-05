import os
import re
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


# ==============================
# Language Detection & Translation
# ==============================
def translate_to_english(text: str) -> dict:
    """
    Detect language of text and translate to English if needed.
    Returns dict with: original, translated, language, was_translated
    """
    try:
        from langdetect import detect, LangDetectException
        try:
            lang = detect(text)
        except LangDetectException:
            lang = "en"

        if lang == "en":
            return {
                "original": text,
                "translated": text,
                "language": "en",
                "was_translated": False
            }

        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        return {
            "original": text,
            "translated": translated,
            "language": lang,
            "was_translated": True
        }
    except Exception as e:
        # Fallback: treat as English if translation fails
        print(f"Translation failed: {e}")
        return {
            "original": text,
            "translated": text,
            "language": "en",
            "was_translated": False
        }


# ==============================
# Extractive Summarization
# ==============================
def summarize_text(text: str, max_sentences: int = 2) -> str:
    """
    Extractive summarization using word frequency scoring.
    Returns a 1-2 sentence summary of the complaint.
    """
    # Split into sentences
    sentence_pattern = re.compile(r'(?<=[.!?])\s+')
    sentences = [s.strip() for s in sentence_pattern.split(text.strip()) if len(s.strip()) > 10]

    if len(sentences) <= max_sentences:
        return text.strip()

    # Stopwords (common words that don't add meaning)
    stopwords = {
        "the", "a", "an", "is", "it", "in", "on", "at", "to", "for",
        "of", "and", "or", "but", "not", "with", "this", "that", "was",
        "are", "be", "has", "have", "had", "by", "as", "from", "there",
        "which", "who", "i", "we", "my", "our", "your", "their", "its"
    }

    # Word frequency
    words = re.findall(r'\b[a-z]+\b', text.lower())
    freq = {}
    for w in words:
        if w not in stopwords:
            freq[w] = freq.get(w, 0) + 1

    # Score each sentence
    scores = []
    for s in sentences:
        s_words = re.findall(r'\b[a-z]+\b', s.lower())
        score = sum(freq.get(w, 0) for w in s_words if w not in stopwords)
        scores.append((score, s))

    # Pick top sentences in original order
    top = sorted(scores, key=lambda x: x[0], reverse=True)[:max_sentences]
    top_sentences = [s for _, s in top]
    # Return in original document order
    result = " ".join(s for s in sentences if s in top_sentences)
    return result.strip()

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