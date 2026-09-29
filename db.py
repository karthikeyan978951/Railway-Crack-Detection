import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB = BASE_DIR / "railway.db"

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS track_sections (
        section_id TEXT PRIMARY KEY,
        location TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sensor_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        vibration REAL,
        acceleration REAL,
        temperature REAL,
        deformation REAL,
        train_speed REAL,
        track_stress REAL,
        humidity REAL,
        rainfall REAL,
        wind_speed REAL
    );

    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        probability REAL NOT NULL,
        risk TEXT NOT NULL,
        health_score REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        probability REAL NOT NULL,
        risk TEXT NOT NULL,
        status TEXT NOT NULL,
        recommended_action TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()
