PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS sensors(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  unit TEXT,
  scale REAL DEFAULT 1.0,
  offset REAL DEFAULT 0.0,
  meta TEXT
);
CREATE TABLE IF NOT EXISTS samples(
  sensor_id INTEGER NOT NULL,
  ts_utc INTEGER NOT NULL,     -- epoch seconds
  value REAL NOT NULL,
  PRIMARY KEY(sensor_id, ts_utc),
  FOREIGN KEY(sensor_id) REFERENCES sensors(id)
);
CREATE INDEX IF NOT EXISTS idx_samples_sid_ts ON samples(sensor_id, ts_utc DESC);