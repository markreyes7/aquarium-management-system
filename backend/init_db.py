import sqlite3

with open("schema.sql") as f:
    schema = f.read()

conn = sqlite3.connect("aquarium.db")
conn.executescript(schema)

# Insert singleton row
conn.execute(
    "INSERT OR IGNORE INTO tank_status (id) VALUES (1)"
)

conn.commit()
conn.close()

print("Database initialized.")
