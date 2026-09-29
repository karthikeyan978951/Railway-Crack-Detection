from pathlib import Path
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from datetime import datetime, timezone
import random
from db import init_db, get_conn
from model_utils import predict_sequence, risk_from_probability, action_for_risk
from weather import current_weather

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["SECRET_KEY"] = "rail-sight-demo"
CORS(app)

init_db()

def latest_rows(section_id, n=12):
    conn = get_conn()
    rows = conn.execute("""SELECT vibration,acceleration,temperature,deformation,
        train_speed,track_stress,humidity,rainfall,wind_speed,timestamp
        FROM sensor_readings WHERE section_id=? ORDER BY timestamp DESC LIMIT ?""",
        (section_id,n)).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]

def risk_counts():
    conn = get_conn()
    rows = conn.execute("SELECT risk, COUNT(*) c FROM predictions GROUP BY risk").fetchall()
    conn.close()
    d = {"LOW":0,"MEDIUM":0,"HIGH":0,"CRITICAL":0}
    for r in rows: d[r["risk"]] = r["c"]
    return d

@app.get("/")
def dashboard():
    return render_template("dashboard.html")

@app.get("/alerts")
def alerts():
    return render_template("alerts.html")

@app.get("/map")
def map_page():
    return render_template("map.html")

@app.get("/model")
def model_page():
    return render_template("model.html")

@app.get("/api/sections")
def sections():
    conn = get_conn()
    tracks = conn.execute("""
        SELECT t.*, p.probability, p.risk, p.health_score, p.timestamp
        FROM track_sections t
        LEFT JOIN predictions p ON p.id = (
            SELECT MAX(id) FROM predictions WHERE section_id=t.section_id
        )
        ORDER BY t.section_id
    """).fetchall()
    conn.close()
    return jsonify({"sections":[dict(x) for x in tracks], "counts":risk_counts()})

@app.get("/api/section/<section_id>")
def section_detail(section_id):
    conn = get_conn()
    track = conn.execute("SELECT * FROM track_sections WHERE section_id=?", (section_id,)).fetchone()
    preds = conn.execute("""SELECT * FROM predictions WHERE section_id=?
                            ORDER BY id DESC LIMIT 30""",(section_id,)).fetchall()
    readings = conn.execute("""SELECT * FROM sensor_readings WHERE section_id=?
                               ORDER BY id DESC LIMIT 30""",(section_id,)).fetchall()
    conn.close()
    if not track: return jsonify({"error":"section not found"}),404
    return jsonify({
        "track":dict(track),
        "predictions":[dict(x) for x in reversed(preds)],
        "readings":[dict(x) for x in reversed(readings)]
    })

@app.get("/api/weather/<section_id>")
def weather(section_id):
    conn = get_conn()
    row = conn.execute("SELECT latitude,longitude,location FROM track_sections WHERE section_id=?",(section_id,)).fetchone()
    conn.close()
    if not row: return jsonify({"error":"section not found"}),404
    try:
        w = current_weather(row["latitude"], row["longitude"])
        w["location"] = row["location"]
        return jsonify(w)
    except Exception as e:
        return jsonify({"error": "Weather API unavailable", "detail": str(e)}),502

@app.get("/api/metrics")
def metrics():
    import json, os
    metrics_path = BASE_DIR / "model" / "metrics.json"
    history_path = BASE_DIR / "model" / "training_history.json"
    if not metrics_path.exists():
        return jsonify({"error":"Train the model first"}),404
    with open(metrics_path) as f: m=json.load(f)
    if history_path.exists():
        with open(history_path) as f: m["history"]=json.load(f)
    return jsonify(m)

@app.get("/api/alerts")
def get_alerts():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    return jsonify({"alerts":[dict(x) for x in rows]})

@app.post("/api/simulate/<section_id>")
def simulate(section_id):
    conn = get_conn()
    track = conn.execute("SELECT * FROM track_sections WHERE section_id=?", (section_id,)).fetchone()
    if not track:
        conn.close(); return jsonify({"error":"section not found"}),404

    history = latest_rows(section_id, 11)
    # Generate an intentionally variable sensor reading for demo.
    latest = history[-1] if history else {
        "vibration":2.2,"acceleration":1.5,"temperature":30,
        "deformation":2.5,"train_speed":65,"track_stress":35,
        "humidity":60,"rainfall":0.1,"wind_speed":8
    }
    severity = request.json.get("severity","normal") if request.is_json else "normal"
    mult = {"normal":1.0,"high":1.45,"critical":1.9}.get(severity,1.0)
    reading = {
        "vibration": max(0.3, latest["vibration"]*mult + random.uniform(-0.2,0.35)),
        "acceleration": max(0.2, latest["acceleration"]*mult + random.uniform(-0.15,0.25)),
        "temperature": latest["temperature"] + random.uniform(-1,1),
        "deformation": max(0.2, latest["deformation"]*mult + random.uniform(-0.4,0.6)),
        "train_speed": max(20, latest["train_speed"] + random.uniform(-5,5)),
        "track_stress": min(100, max(10, latest["track_stress"]*mult + random.uniform(-3,5))),
        "humidity": min(99, max(20, latest["humidity"] + random.uniform(-3,5))),
        "rainfall": max(0, latest["rainfall"] + random.uniform(0,4 if severity!="normal" else 0.5)),
        "wind_speed": max(0, latest["wind_speed"] + random.uniform(-2,4)),
    }
    ts = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    cur.execute("""INSERT INTO sensor_readings
        (section_id,timestamp,vibration,acceleration,temperature,deformation,
         train_speed,track_stress,humidity,rainfall,wind_speed)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (section_id,ts,reading["vibration"],reading["acceleration"],reading["temperature"],
         reading["deformation"],reading["train_speed"],reading["track_stress"],
         reading["humidity"],reading["rainfall"],reading["wind_speed"]))
    conn.commit()
    conn.close()

    rows = latest_rows(section_id, 12)
    p = predict_sequence(rows)
    risk = risk_from_probability(p)
    health = round(max(0,100*(1-p)),1)
    conn = get_conn()
    conn.execute("""INSERT INTO predictions(section_id,timestamp,probability,risk,health_score)
                    VALUES (?,?,?,?,?)""",(section_id,ts,p,risk,health))
    if risk in ("HIGH","CRITICAL"):
        conn.execute("""INSERT INTO alerts(section_id,timestamp,probability,risk,status,recommended_action)
                        VALUES (?,?,?,?,?,?)""",
                     (section_id,ts,p,risk,"OPEN",action_for_risk(risk)))
    conn.commit(); conn.close()
    return jsonify({"section_id":section_id,"reading":reading,"probability":p,
                    "risk":risk,"health_score":health,"action":action_for_risk(risk)})

@app.post("/api/simulate")
def simulate_default():
    return simulate("TRK-001")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
