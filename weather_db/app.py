from flask import Flask, jsonify
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "weather.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS weather_forecast (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_code TEXT,
        area_name TEXT,
        date TEXT,
        weather TEXT,
        created_at TEXT,
        UNIQUE(area_code, date)
    )
""")
    conn.commit()
    conn.close()

@app.route("/fetch/<area_code>")
def fetch_weather(area_code):
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"
    data = requests.get(url).json()

    area_name = data[0]["timeSeries"][0]["areas"][0]["area"]["name"]
    weathers = data[0]["timeSeries"][0]["areas"][0]["weathers"]
    dates = data[0]["timeSeries"][0]["timeDefines"]

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    for date, weather in zip(dates, weathers):
        cur.execute("""
            INSERT OR IGNORE INTO weather_forecast
            (area_code, area_name, date, weather, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            area_code,
            area_name,
            date,
            weather,
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()

    return jsonify({"message": "saved", "area": area_name})

@app.route("/weather/<area_code>")
def get_weather(area_code):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT date, weather
        FROM weather_forecast
        WHERE area_code = ?
        ORDER BY date
    """, (area_code,))
    rows = cur.fetchall()
    conn.close()

    return jsonify([
        {"date": r[0], "weather": r[1]} for r in rows
    ])

if __name__ == "__main__":
    init_db()
    app.run(debug=True)