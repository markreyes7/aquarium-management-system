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

    maintenance_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(maintenance_log)").fetchall()
    }
    if "notes" not in maintenance_cols and "note" in maintenance_cols:
        conn.execute("ALTER TABLE maintenance_log ADD COLUMN notes TEXT")
        conn.execute("UPDATE maintenance_log SET notes = note WHERE notes IS NULL")

    conn.commit()
    conn.close()

    print(f"Database initialized: {database}")


if __name__ == "__main__":
    init_database()
