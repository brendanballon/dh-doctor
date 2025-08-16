# collector/main.py
import time
from common.db import init_db, insert_samples

DB_PATH = "data/db.sqlite"
SCHEMA_PATH = "config/schema.sql"

def read_all_mock() -> list[tuple[int,int,float]]:
    """Return two fake readings: (sensor_id, ts_utc, value)."""
    now = int(time.time())
    v1 = (now % 100) / 2.0
    v2 = (now % 50) + 10.0
    return [(1, now, v1), (2, now, v2)]

def run_once() -> None:
    init_db(DB_PATH, SCHEMA_PATH)
    samples = read_all_mock()
    insert_samples(DB_PATH, samples)

def run_forever(interval_s: float = 1.0) -> None:
    init_db(DB_PATH, SCHEMA_PATH)
    while True:
        try:
            insert_samples(DB_PATH, read_all_mock())
        except Exception as e:
            # simple resilience; log and continue
            print(f"[collector] error: {e}")
        time.sleep(interval_s)

if __name__ == "__main__":
    # pick one during development:
    # run_once()
    run_forever(1.0)