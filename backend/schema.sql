-- Tank status (single row)

--tank_status needs to have the temperature AND the light status
--for now it will latest temp and n/a


CREATE TABLE IF NOT EXISTS tank_status (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_fertilized TEXT,
    last_water_change TEXT,
    last_water_topoff TEXT,
    last_trimmed TEXT,
    temperature REAL,
    light_state BOOLEAN,  --- check this to make sure it wont lead to any issues going forward. light can be either on or off that's it
    light_timer_enabled BOOLEAN DEFAULT 0,
    notes TEXT
);

-- Temperature logs
CREATE TABLE IF NOT EXISTS temperature_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature REAL NOT NULL,
    recorded_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- Light state history
CREATE TABLE IF NOT EXISTS light_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state BOOLEAN NOT NULL CHECK (state IN (0, 1)),
    recorded_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS plants (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plant_type TEXT NOT NULL,
  in_tank BOOLEAN NOT NULL DEFAULT 1,
  added_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
  removed_at TIMESTAMP,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS maintenance_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  action TEXT NOT NULL,
  occurred_at TIMESTAMP NOT NULL DEFAULT (datetime('now', 'localtime')),
  notes TEXT
);
