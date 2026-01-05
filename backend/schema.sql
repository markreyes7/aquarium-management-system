-- Tank status (single row)
CREATE TABLE IF NOT EXISTS tank_status (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_fertilized TIMESTAMP,
    last_water_change TIMESTAMP,
    last_water_topoff TIMESTAMP,
    notes TEXT
);

-- Temperature logs
CREATE TABLE IF NOT EXISTS temperature_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature REAL NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Light state history
CREATE TABLE IF NOT EXISTS light_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

