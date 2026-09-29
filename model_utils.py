import os, json, joblib
from pathlib import Path
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "railway_lstm.keras"
SCALER_PATH = BASE_DIR / "model" / "scaler.joblib"
FEATURES = [
    "vibration", "acceleration", "temperature", "deformation",
    "train_speed", "track_stress", "humidity", "rainfall", "wind_speed"
]
SEQ_LEN = 12

_model = None
_scaler = None

def load_artifacts():
    global _model, _scaler
    if _model is None:
        if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
            raise FileNotFoundError("Model not found. Run: python train_model.py")
        _model = load_model(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)
    return _model, _scaler

def predict_sequence(rows):
    model, scaler = load_artifacts()
    frame = pd.DataFrame(rows)[FEATURES].astype(float)
    if len(frame) < SEQ_LEN:
        raise ValueError(f"Need at least {SEQ_LEN} sequential readings.")
    x = frame.tail(SEQ_LEN).values.astype("float32")
    x = scaler.transform(x).reshape(1, SEQ_LEN, len(FEATURES))
    p = float(model.predict(x, verbose=0).ravel()[0])
    return p

def risk_from_probability(p):
    if p <= 0.30: return "LOW"
    if p <= 0.60: return "MEDIUM"
    if p <= 0.80: return "HIGH"
    return "CRITICAL"

def action_for_risk(risk):
    return {
        "LOW": "Continue routine monitoring.",
        "MEDIUM": "Schedule condition review and monitor trend.",
        "HIGH": "Inspect vibration, deformation and rail alignment.",
        "CRITICAL": "Immediate physical inspection and safety assessment required."
    }[risk]
