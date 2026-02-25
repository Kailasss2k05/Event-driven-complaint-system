from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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