import os, json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

BASE_DIR = Path(__file__).resolve().parent
DATA = BASE_DIR / "dataset" / "railway_track_sensor_data.csv"
MODEL_DIR = BASE_DIR / "model"
os.makedirs(MODEL_DIR, exist_ok=True)

COLUMNS = [
    "section_id", "location", "latitude", "longitude", "timestamp",
    "vibration_mm_s", "acceleration_g", "temperature_c", "deformation_mm",
    "train_speed_kmh", "track_stress", "humidity_pct", "rainfall_mm",
    "wind_speed_kmh", "failure_probability", "failure_label"
]

FEATURES = [
    "vibration_mm_s", "acceleration_g", "temperature_c", "deformation_mm",
    "train_speed_kmh", "track_stress", "humidity_pct", "rainfall_mm", "wind_speed_kmh"
]
SEQ_LEN = 12

df = pd.read_csv(DATA, header=None, names=COLUMNS, parse_dates=["timestamp"])
df = df.sort_values(["section_id", "timestamp"]).reset_index(drop=True)

X_all, y_all = [], []
for sid, g in df.groupby("section_id"):
    vals = g[FEATURES].astype("float32").values
    labels = g["failure_label"].astype("float32").values
    if len(g) <= SEQ_LEN:
        continue
    for i in range(SEQ_LEN, len(g)):
        X_all.append(vals[i-SEQ_LEN:i])
        y_all.append(labels[i])

X = np.asarray(X_all, dtype="float32")
y = np.asarray(y_all, dtype="float32")

# Split by samples for a reproducible demo. For production, use time-based validation.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

scaler = StandardScaler()
scaler.fit(X_train.reshape(-1, X_train.shape[-1]))
X_train_s = scaler.transform(X_train.reshape(-1, X_train.shape[-1])).reshape(X_train.shape)
X_test_s = scaler.transform(X_test.reshape(-1, X_test.shape[-1])).reshape(X_test.shape)
joblib.dump(scaler, f"{MODEL_DIR}/scaler.joblib")

model = Sequential([
    LSTM(64, input_shape=(SEQ_LEN, len(FEATURES)), return_sequences=True),
    Dropout(0.20),
    LSTM(32),
    Dropout(0.20),
    Dense(16, activation="relu"),
    Dense(1, activation="sigmoid")
])
model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])

callbacks = [
    EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
    ModelCheckpoint(f"{MODEL_DIR}/railway_lstm.keras", monitor="val_loss", save_best_only=True)
]
history = model.fit(
    X_train_s, y_train,
    validation_split=0.20,
    epochs=30,
    batch_size=64,
    callbacks=callbacks,
    verbose=1
)

p = model.predict(X_test_s, verbose=0).ravel()
pred = (p >= 0.5).astype(int)
metrics = {
    "accuracy": float(accuracy_score(y_test, pred)),
    "precision": float(precision_score(y_test, pred, zero_division=0)),
    "recall": float(recall_score(y_test, pred, zero_division=0)),
    "f1": float(f1_score(y_test, pred, zero_division=0)),
    "roc_auc": float(roc_auc_score(y_test, p)),
    "sequence_length": SEQ_LEN,
    "features": FEATURES
}
with open(f"{MODEL_DIR}/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

with open(f"{MODEL_DIR}/training_history.json", "w") as f:
    json.dump({
        "loss": [float(x) for x in history.history["loss"]],
        "val_loss": [float(x) for x in history.history["val_loss"]],
        "accuracy": [float(x) for x in history.history["accuracy"]],
        "val_accuracy": [float(x) for x in history.history["val_accuracy"]]
    }, f, indent=2)

print(json.dumps(metrics, indent=2))
print("Saved model, scaler, metrics and training history under model/")
