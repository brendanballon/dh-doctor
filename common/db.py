# common/db.py
import sqlite3, pathlib

def init_db(db_path: str, schema_path: str) -> None:
    """Create parent folder, create DB file if missing, apply schema, enable WAL."""
    p = pathlib.Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            con.executescript(f.read())
        # ensure WAL; safe to call repeatedly
        con.execute("PRAGMA journal_mode=WAL;")
    finally:
        con.close()

def open_read(db_path: str) -> sqlite3.Connection:
    """Open SQLite in read-only mode."""
    uri = f"file:{pathlib.Path(db_path).as_posix()}?mode=ro&cache=shared"
    return sqlite3.connect(uri, uri=True, check_same_thread=False)

def open_write(db_path: str) -> sqlite3.Connection:
    """Open SQLite for writing."""
    return sqlite3.connect(db_path, check_same_thread=False)

def insert_samples(db_path: str, samples: list[tuple[int,int,float]]) -> None:
    """samples: list of (sensor_id, ts_utc, value)."""
    con = open_write(db_path)
    try:
        con.executemany(
            "INSERT OR REPLACE INTO samples(sensor_id, ts_utc, value) VALUES (?,?,?)",
            samples,
        )
        con.commit()
    finally:
        con.close()

def get_latest(db_path: str, sensor_id: int, n: int) -> list[tuple[int,float]]:
    con = open_read(db_path)
    try:
        rows = con.execute(
            "SELECT ts_utc, value FROM samples WHERE sensor_id=? "
            "ORDER BY ts_utc DESC LIMIT ?",
            (sensor_id, n),
        ).fetchall()
        return rows
    finally:
        con.close()