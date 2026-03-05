from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from . import model_loader


# ==============================
# Lifespan (replaces deprecated on_event)
# ==============================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    model_loader.load_models()
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(
    title="ML Service",
    version="1.0.0",
    lifespan=lifespan
)


# ==============================
# Request Model
# ==============================
class Complaint(BaseModel):
    complaint: str

class TranslateRequest(BaseModel):
    text: str

class SummarizeRequest(BaseModel):
    text: str
    max_sentences: Optional[int] = 2


# ==============================
# Health Check
# ==============================
@app.get("/")
def home():
    if not model_loader.models_ready:
        return {"status": "Model loading..."}
    return {"status": "ML Service Ready"}


# ==============================
# Prediction Endpoint
# ==============================
@app.post("/predict")
def predict(data: Complaint):

    if not model_loader.models_ready:
        raise HTTPException(
            status_code=503,
            detail="Model loading, try again in a few seconds"
        )

    try:
        return model_loader.predict_complaint(data.complaint)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


# ==============================
# Translation Endpoint
# ==============================
@app.post("/translate")
def translate(data: TranslateRequest):
    """Detect language and translate complaint text to English."""
    try:
        result = model_loader.translate_to_english(data.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


# ==============================
# Summarization Endpoint
# ==============================
@app.post("/summarize")
def summarize(data: SummarizeRequest):
    """Generate an extractive summary of the complaint text."""
    try:
        summary = model_loader.summarize_text(data.text, data.max_sentences)
        return {
            "summary": summary,
            "original_length": len(data.text),
            "summary_length": len(summary)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")