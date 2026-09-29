# RailSight — LSTM-Based Railway Track Failure Prediction and Early Warning System

A college AIML prototype for sequential railway track-condition monitoring. It uses an LSTM deep neural network, a persistent SQLite database, a Flask API, Tamil Nadu track locations, a Tamil Nadu risk map, weather API integration, model-performance charts, and automatic HIGH/CRITICAL alerts.

## Important scope

This is an AI-assisted research/college prototype. It does **not** certify railway safety or replace official inspection systems.

The included dataset is **synthetic demonstration data**, not real railway sensor data.

## Features

- LSTM time-series binary failure-risk prediction
- 18 Tamil Nadu track sections
- 9 model features: vibration, acceleration, temperature, deformation, train speed, stress, humidity, rainfall, wind speed
- Risk bands: LOW, MEDIUM, HIGH, CRITICAL
- Track health score
- Sensor simulation
- Automatic HIGH/CRITICAL alerts
- Predictive maintenance recommendation
- Tamil Nadu map using Leaflet/OpenStreetMap
- Live weather lookup through Open-Meteo
- Model performance page
- SQLite persistent database
- Flask REST-style endpoints

## Setup (Windows)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python train_model.py
python seed_db.py
python app.py
```

Open http://127.0.0.1:5000

## Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python train_model.py
python seed_db.py
python app.py
```

## Demo flow

1. Open Overview.
2. Open Tamil Nadu Map.
3. Open Model Performance to show LSTM metrics.
4. Go to Alert History.
5. Click "Simulate critical condition".
6. Return to Alert History and show the generated alert.
7. Use the weather endpoint from the map/track workflow.

## API endpoints

- `GET /api/sections`
- `GET /api/section/TRK-001`
- `GET /api/weather/TRK-001`
- `GET /api/alerts`
- `GET /api/metrics`
- `POST /api/simulate/TRK-001`

## Dataset

`dataset/railway_track_sensor_data.csv` contains synthetic sequential readings for 18 Tamil Nadu sections. It is intended for development/demo and must not be presented as real railway sensor data.

## Model

The training script creates sequences of 12 readings and trains:

LSTM(64) → Dropout → LSTM(32) → Dropout → Dense(16) → Sigmoid

The scaler and trained Keras model are saved in `model/`.
