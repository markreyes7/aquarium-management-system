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

CREATE TABLE IF NOT EXISTS tank_profile (
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

CREATE TABLE IF NOT EXISTS livestock (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  common_name TEXT NOT NULL,
  species_name TEXT,
  livestock_type TEXT CHECK (
    livestock_type IS NULL OR livestock_type IN (
      'fish',
      'shrimp',
      'snail',
      'crab',
      'coral',
      'other'
    )
  ),
  quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
  in_tank BOOLEAN NOT NULL DEFAULT 1 CHECK (in_tank IN (0, 1)),
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

CREATE TABLE IF NOT EXISTS topoff_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL CHECK (source IN ('manual', 'pump')),
  requested_seconds REAL,
  status TEXT NOT NULL CHECK (status IN ('requested', 'completed', 'failed')),
  notes TEXT,
  arduino_response TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT (datetime('now', 'localtime')),
  completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS water_parameter_log (
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
);
