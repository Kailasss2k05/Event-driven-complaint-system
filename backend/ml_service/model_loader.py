import os
import re
import joblib
import threading
import time
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
loading_lock = threading.Lock()


# ==============================
# Load Models Function
# ==============================
def load_models():

    global category_model
    global priority_model
    global embedder
    global models_ready

    with loading_lock:
        # Skip if already loaded
        if models_ready:
            return

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
            device=os.getenv("MODEL_DEVICE", "cpu"),
            cache_folder="/tmp/sentence_transformers_cache",
            model_kwargs={'torch_dtype': 'float32'}
        )

        models_ready = True
        print("Models loaded successfully!")


def load_models_background():
    """Load models in a background thread without blocking startup."""
    thread = threading.Thread(target=load_models, daemon=True)
    thread.start()


def wait_for_models(timeout: int = 120) -> bool:
    """
    Wait for models to be loaded. Returns True if ready, False if timeout.
    Used by prediction endpoints to ensure models are available.
    """
    elapsed = 0
    while not models_ready and elapsed < timeout:
        time.sleep(0.1)
        elapsed += 0.1
    return models_ready


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
# Severity + Eisenhower Priority Detection
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


def _has_any_keyword(text_lower: str, keywords: list[str]) -> bool:
    return any(word in text_lower for word in keywords)


def detect_severity(text: str) -> str:
    text_lower = text.lower()
    for word in CRITICAL_WORDS:
        if word in text_lower:
            return "Critical"
    for word in MEDIUM_WORDS:
        if word in text_lower:
            return "Medium"
    return "Low"


def eisenhower_priority(text: str, severity: str, model_priority: str) -> tuple[str, str]:
    """
    Map complaint to an Eisenhower quadrant and existing priority scale.

    Quadrants:
    - Do First  (Urgent + Important)       -> CRITICAL
    - Schedule  (Not Urgent + Important)   -> HIGH
    - Delegate  (Urgent + Not Important)   -> MEDIUM
    - Eliminate (Not Urgent + Not Important) -> ML model fallback

    Urgency and importance are determined purely by keyword signals and
    detected severity. The ML model is NOT used to set is_urgent or
    is_important (doing so caused everything to collapse to CRITICAL
    because the model returns HIGH for many complaints).
    The ML model is only used as a tiebreaker in the Eliminate quadrant.
    """
    text_lower = text.lower()
    model_priority_upper = str(model_priority).upper()

    is_urgent = _has_any_keyword(text_lower, URGENT_WORDS)
    is_important = _has_any_keyword(text_lower, IMPORTANT_WORDS)

    # Detected severity is the strongest signal:
    # - Critical words (fire, gas leak, collapse, etc.) → urgent AND important
    # - Medium words (leakage, sewage, overflow, etc.) → urgent only
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

    # Eliminate quadrant: no strong keyword signals detected.
    # Fall back to the ML model's own prediction.
    if model_priority_upper in {"HIGH", "CRITICAL"}:
        return "ELIMINATE", "HIGH"
    if model_priority_upper in {"MEDIUM", "NORMAL"}:
        return "ELIMINATE", "MEDIUM"
    return "ELIMINATE", "LOW"


# ==============================
# Prediction Function
# ==============================
def predict_complaint(text: str):

    global models_ready

    if not models_ready:
        load_models()

    # Category prediction uses raw text.
    emb_category = embedder.encode([text], convert_to_numpy=True)
    category = category_model.predict(emb_category)[0]

    # ML model predicts priority from raw complaint text only.
    # No severity column is needed — the model learned urgency patterns
    # from complaint text during training.
    severity = detect_severity(text)
    emb_priority = embedder.encode([text.lower()], convert_to_numpy=True)
    model_priority = priority_model.predict(emb_priority)[0]

    # Eisenhower overlay uses keyword-detected severity + ML output
    # to determine the final quadrant and priority label.
    eisenhower_quadrant, priority = eisenhower_priority(text, severity, model_priority)

    department = DEPARTMENT_MAP.get(category, "General Department")

    return {
        "category": category,
        "priority": priority,
        "severity": severity,
        "department": department,
        "eisenhower_quadrant": eisenhower_quadrant,
        "priority_model_raw": str(model_priority).upper()
    }