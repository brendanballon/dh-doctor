# webui/app.py
from flask import Flask, render_template, jsonify, request, Response
from common.db import get_latest, get_bucketed_avg
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

# no-cache so dropdown refreshes immediately
@APP.after_request
def no_cache(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

# Map ranges to bucket size
RANGE_MAP = {
    "1h":  (60*60,   60),      # last 1 hour, avg per minute
    "1d":  (24*3600, 30*60),   # last 1 day, avg per 30 min
    "7d":  (7*24*3600, 3600),  # last 7 days, avg per hour
    "30d": (30*24*3600, 3600), # last 30 days, avg per hour
}

@APP.get("/api/series")
def api_series():
    sensor_id = int(request.args.get("sensor_id", 1))
    rng = request.args.get("range", "1h")
    dur_sec, bucket_sec = RANGE_MAP.get(rng, RANGE_MAP["1h"])

    # optional override for flexibility: ?bucket_sec=300 for 5-minute bins
    if "bucket_sec" in request.args:
        try:
            bucket_sec = max(60, int(request.args["bucket_sec"]))
        except ValueError:
            pass

    now = int(time.time())
    start_ts = now - dur_sec
    rows = get_bucketed_avg(DB_PATH, sensor_id, start_ts, bucket_sec)

    # Fill all expected buckets, use None where no data exists
    row_map = {int(ts): float(avg) for ts, avg in rows}
    start_aligned = (start_ts // bucket_sec) * bucket_sec
    end_aligned   = ((now + bucket_sec - 1) // bucket_sec) * bucket_sec
    points = []
    ts = start_aligned
    while ts <= end_aligned:
        points.append({"ts": ts, "avg": row_map.get(ts, None)})
        ts += bucket_sec

    return jsonify({
        "bucket_sec": bucket_sec,
        "points": points  # list of {ts, avg}
    })

if __name__ == "__main__":
    # run as: python -m webui.app  (from project root)
    APP.run(host="0.0.0.0", port=5000, debug=True)
