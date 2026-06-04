import sqlite3

from config import BASE_DIR, get_database_path


def init_database() -> None:
    database = get_database_path()
    with open(BASE_DIR / "schema.sql") as f:
        schema = f.read()

    conn = sqlite3.connect(database)
    conn.executescript(schema)

    # Insert singleton row
    conn.execute(
        "INSERT OR IGNORE INTO tank_status (id) VALUES (1)"
    )
    conn.execute(
        "INSERT OR IGNORE INTO tank_profile (id) VALUES (1)"
    )

    # Backfill columns for existing databases created before schema changes.
    tank_status_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(tank_status)").fetchall()
    }
    if "last_trimmed" not in tank_status_cols:
        conn.execute("ALTER TABLE tank_status ADD COLUMN last_trimmed TIMESTAMP")
    # earlier patch added temperature and light_state columns; the schema now
    # uses REAL for temperature to match the log table.  Add them if missing.
    if "temperature" not in tank_status_cols:
        conn.execute("ALTER TABLE tank_status ADD COLUMN temperature REAL")
    if "light_state" not in tank_status_cols:
        conn.execute("ALTER TABLE tank_status ADD COLUMN light_state BOOLEAN")
    if "light_timer_enabled" not in tank_status_cols:
        conn.execute(
            "ALTER TABLE tank_status ADD COLUMN light_timer_enabled BOOLEAN DEFAULT 0"
        )
    if "notes" not in tank_status_cols:
        conn.execute("ALTER TABLE tank_status ADD COLUMN notes TEXT")

    existing_tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    if "tank_profile" not in existing_tables:
        conn.execute(
            """
            CREATE TABLE tank_profile (
              id INTEGER PRIMARY KEY CHECK (id = 1),
              size_gallons REAL CHECK (size_gallons IS NULL OR size_gallons > 0),
              water_type TEXT CHECK (
                water_type IS NULL OR water_type IN (
                  'freshwater',
                  'saltwater',
                  'brackish'
                )
              ),
              target_temperature_min REAL,
              target_temperature_max REAL,
              lighting_schedule TEXT,
              setup_date TEXT,
              notes TEXT,
              updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
              CHECK (
                target_temperature_min IS NULL
                OR target_temperature_max IS NULL
                OR target_temperature_min <= target_temperature_max
              )
            )
            """
        )
    if "water_parameter_log" not in existing_tables:
        conn.execute(
            """
            CREATE TABLE water_parameter_log (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ph REAL CHECK (ph IS NULL OR (ph >= 0 AND ph <= 14)),
              ammonia REAL CHECK (ammonia IS NULL OR ammonia >= 0),
              nitrite REAL CHECK (nitrite IS NULL OR nitrite >= 0),
              nitrate REAL CHECK (nitrate IS NULL OR nitrate >= 0),
              gh REAL CHECK (gh IS NULL OR gh >= 0),
              kh REAL CHECK (kh IS NULL OR kh >= 0),
              tds REAL CHECK (tds IS NULL OR tds >= 0),
              tested_at TIMESTAMP NOT NULL DEFAULT (datetime('now', 'localtime')),
              notes TEXT,
              CHECK (
                ph IS NOT NULL
                OR ammonia IS NOT NULL
                OR nitrite IS NOT NULL
                OR nitrate IS NOT NULL
                OR gh IS NOT NULL
                OR kh IS NOT NULL
                OR tds IS NOT NULL
              )
            )
            """
        )
    if "topoff_log" not in existing_tables:
        conn.execute(
            """
            CREATE TABLE topoff_log (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              source TEXT NOT NULL CHECK (source IN ('manual', 'pump')),
              requested_seconds REAL,
              status TEXT NOT NULL CHECK (status IN ('requested', 'completed', 'failed')),
              notes TEXT,
              arduino_response TEXT,
              created_at TIMESTAMP NOT NULL DEFAULT (datetime('now', 'localtime')),
              completed_at TIMESTAMP
            )
            """
        )

    maintenance_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(maintenance_log)").fetchall()
    }
    if "notes" not in maintenance_cols and "note" in maintenance_cols:
        conn.execute("ALTER TABLE maintenance_log ADD COLUMN notes TEXT")
        conn.execute("UPDATE maintenance_log SET notes = note WHERE notes IS NULL")

    conn.execute(
        "INSERT OR IGNORE INTO tank_profile (id) VALUES (1)"
    )

    conn.commit()
    conn.close()

    print(f"Database initialized: {database}")


if __name__ == "__main__":
    init_database()
