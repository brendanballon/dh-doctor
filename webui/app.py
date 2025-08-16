# webui/app.py
from flask import Flask, render_template, jsonify, request, Response
from common.db import get_latest
import time
import json

APP = Flask(__name__)

DB_PATH = "data/db.sqlite"  # same path the collector writes to

@APP.get("/")
def index():
    # demo: show last 10 rows for sensor 1 and 2
    rows1 = get_latest(DB_PATH, sensor_id=1, n=10)
    rows2 = get_latest(DB_PATH, sensor_id=2, n=10)
    return render_template("index.html", rows1=rows1, rows2=rows2)

@APP.get("/api/last")
def api_last():
    sid = int(request.args.get("sensor_id", "1"))
    n = int(request.args.get("n", "1"))
    data = get_latest(DB_PATH, sid, n)
    return jsonify([{"ts_utc": ts, "value": val} for (ts, val) in data])

@APP.get("/api/stream")
def api_stream():
    def generate():
        while True:
            # Get latest data for both sensors
            data1 = get_latest(DB_PATH, sensor_id=1, n=1)
            data2 = get_latest(DB_PATH, sensor_id=2, n=1)
            
            # Format as SSE
            event_data = {
                "sensor1": {"ts_utc": data1[0][0], "value": data1[0][1]} if data1 else None,
                "sensor2": {"ts_utc": data2[0][0], "value": data2[0][1]} if data2 else None,
                "timestamp": int(time.time())
            }
            
            yield f"data: {json.dumps(event_data)}\n\n"
            time.sleep(1)  # Update every second
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == "__main__":
    # run as: python -m webui.app  (from project root)
    APP.run(host="127.0.0.1", port=5000, debug=True)