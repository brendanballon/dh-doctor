# # collector/main.py
# import time
# from common.db import init_db, insert_samples

# DB_PATH = "data/db.sqlite"
# SCHEMA_PATH = "config/schema.sql"

# def read_all_mock() -> list[tuple[int,int,float]]:
#     """Return two fake readings: (sensor_id, ts_utc, value)."""
#     now = int(time.time())
#     v1 = (now % 100) / 2.0
#     v2 = (now % 50) + 10.0
#     return [(1, now, v1), (2, now, v2)]

# def run_once() -> None:
#     init_db(DB_PATH, SCHEMA_PATH)
#     samples = read_all_mock()
#     insert_samples(DB_PATH, samples)

# def run_forever(interval_s: float = 1.0) -> None:
#     init_db(DB_PATH, SCHEMA_PATH)
#     while True:
#         try:
#             insert_samples(DB_PATH, read_all_mock())
#         except Exception as e:
#             # simple resilience; log and continue
#             print(f"[collector] error: {e}")
#         time.sleep(interval_s)

# if __name__ == "__main__":
#     # pick one during development:
#     # run_once()
#     run_forever(1.0)
# # collector/main.py
import time
from typing import List, Tuple
from pymodbus.client import ModbusSerialClient
from common.db import init_db, insert_samples

DB_PATH = "data/db.sqlite"
SCHEMA_PATH = "config/schema.sql"

# --- Modbus RS-485 sensor config (first working version) ---
# Use the same settings you validated in your one-shot test.
MODBUS_PORT = "/dev/ttyUSB0"   # or "/dev/serial0" if using the HAT
MODBUS_BAUD = 9600
MODBUS_PARITY = "N"             # "E" for even, "N" for none
MODBUS_STOPBITS = 1
MODBUS_TIMEOUT_S = 1
SENSOR_UNIT_ID = 1               # Modbus node id that responded

# Map logical metrics to sensor_id in the DB
SENSOR_ID_TEMP = 1
SENSOR_ID_HUM  = 2


def read_sht20_once() -> List[Tuple[int, int, float]]:
    """Poll the SHT20 RS-485 sensor once and return DB-ready samples.
    Returns: [(sensor_id, ts_utc, value), ...]
    """
    ts = int(time.time())

    client = ModbusSerialClient(
        port=MODBUS_PORT,
        baudrate=MODBUS_BAUD,
        parity=MODBUS_PARITY,
        stopbits=MODBUS_STOPBITS,
        timeout=MODBUS_TIMEOUT_S,
    )

    if not client.connect():
        raise RuntimeError(f"Modbus open failed on {MODBUS_PORT}")

    try:
        client.unit_id = SENSOR_UNIT_ID
        # Sensor spec: FC 0x04 (input registers), start=1, count=2 -> 30002..30003
        rr = client.read_input_registers(address=1, count=2)
        if not rr or rr.isError():
            raise RuntimeError(f"Modbus read failed: {rr}")
        temp_raw, hum_raw = rr.registers
        temp_c = temp_raw / 10.0
        rh_pct = hum_raw / 10.0
        return [
            (SENSOR_ID_TEMP, ts, float(temp_c)),
            (SENSOR_ID_HUM,  ts, float(rh_pct)),
        ]
    finally:
        client.close()


def run_once() -> None:
    init_db(DB_PATH, SCHEMA_PATH)
    samples = read_sht20_once()
    insert_samples(DB_PATH, samples)


def run_forever(interval_s: float = 1.0) -> None:
    init_db(DB_PATH, SCHEMA_PATH)
    while True:
        try:
            samples = read_sht20_once()
            insert_samples(DB_PATH, samples)
        except Exception as e:
            # log and continue; no insert on failure
            print(f"[collector] modbus error: {e}")
        time.sleep(interval_s)


if __name__ == "__main__":
    # pick one during development:
    # run_once()
    run_forever(1.0)