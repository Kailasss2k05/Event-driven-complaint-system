from fastapi import FastAPI
from pydantic import BaseModel
import threading
import time

import model_loader

app = FastAPI()


# ==============================
# Request Model
# ==============================
class Complaint(BaseModel):
    complaint: str


# ==============================
# Startup Event
# ==============================
@app.on_event("startup")
def startup_event():
    model_loader.load_models()

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
        return {"status": "Model loading, try again in a few seconds"}

    return model_loader.predict_complaint(data.complaint)