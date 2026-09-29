import pandas as pd
from pathlib import Path
from db import init_db, get_conn

BASE_DIR = Path(__file__).resolve().parent
DATA = BASE_DIR / "dataset" / "railway_track_sensor_data.csv"
COLUMNS = [
    "section_id", "location", "latitude", "longitude", "timestamp",
    "vibration_mm_s", "acceleration_g", "temperature_c", "deformation_mm",
    "train_speed_kmh", "track_stress", "humidity_pct", "rainfall_mm",
    "wind_speed_kmh", "failure_probability", "failure_label"
]

def risk(p):
    if p <= 0.30: return "LOW"
    if p <= 0.60: return "MEDIUM"
    if p <= 0.80: return "HIGH"
    return "CRITICAL"

def seed():
    init_db()
    df = pd.read_csv(DATA, header=None, names=COLUMNS, parse_dates=["timestamp"])
    conn = get_conn()
    cur = conn.cursor()
    sections = df[["section_id","location","latitude","longitude"]].drop_duplicates()
    cur.executemany(
        "INSERT OR REPLACE INTO track_sections VALUES (?,?,?,?)",
        sections.itertuples(index=False, name=None)
    )
    # Seed latest 24 rows per section as dashboard history
    for sid, g in df.groupby("section_id"):
        latest = g.tail(24)
        for r in latest.itertuples(index=False):
            cur.execute("""INSERT INTO sensor_readings
                (section_id,timestamp,vibration,acceleration,temperature,deformation,
                 train_speed,track_stress,humidity,rainfall,wind_speed)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (r.section_id,r.timestamp,r.vibration_mm_s,r.acceleration_g,r.temperature_c,
                 r.deformation_mm,r.train_speed_kmh,r.track_stress,r.humidity_pct,
                 r.rainfall_mm,r.wind_speed_kmh))
    # Create one latest prediction per section from dataset's known synthetic target.
    for sid, g in df.groupby("section_id"):
        r = g.iloc[-1]
        p = float(r.failure_probability)
        cur.execute("""INSERT INTO predictions(section_id,timestamp,probability,risk,health_score)
                       VALUES (?,?,?,?,?)""",
                    (sid,r.timestamp,p,risk(p),max(0,100*(1-p))))
    conn.commit()
    conn.close()
    print("Database seeded.")

if __name__ == "__main__":
    seed()
