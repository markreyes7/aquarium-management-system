# Local Development Checklist

Clean, minimal, and accurate setup instructions for local development.

---

## Project Assumptions

- Backend: Flask + SQLite
- Backend runs on `127.0.0.1:3001`
- SQLite database file: `backend/aquarium.db`
- Commands are run from the project root unless stated otherwise

---

## 1. Backend (Flask API)

### First-time setup (fresh machine)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the backend server

```bash
flask --app server run --debug --host 127.0.0.1 --port 3001
```

Backend should now be available at:

```
http://127.0.0.1:3001
```

---

## 2. Database (SQLite)

The backend uses a local SQLite database.

### Inspect the database (optional)

```bash
cd backend
sqlite3 aquarium.db
```

Useful SQLite commands:

```sql
.tables
.schema tank_status
SELECT * FROM tank_status;
.quit
```

Notes:
- Do **not** recreate tables unless you intend to wipe data
- Use `ALTER TABLE` for schema changes
- Always run Flask from the `backend/` directory so relative DB paths resolve correctly

---

## 3. Backend Sanity Checks (Required)

Run these **after the backend is running**:

```bash
curl http://127.0.0.1:3001/
```

If you have a data route:

```bash
curl http://127.0.0.1:3001/data
```

If these fail, stop and fix the backend before continuing.

---

## 4. Simulator / Scripted Clients (Optional)

Only run simulators **after backend sanity checks pass**.

```bash
source backend/.venv/bin/activate
API_BASE_URL=http://127.0.0.1:3001 python simulator.py
```

Guidelines:
- Simulators must not assume the backend is running
- Simulators must not hardcode ports

---

## 5. Common Failure Modes

### Connection Refused

Likely causes:
- Backend not running
- Wrong port (5000 vs 3001)
- Simulator or frontend started before backend

Quick check:

```bash
ps aux | grep flask
```

---

### Database Errors

Likely causes:
- Flask launched from the wrong directory
- Incorrect relative path to `aquarium.db`

Fix:
- Always start Flask from `backend/`
- Or use absolute paths in database helpers

---

## 6. Development Order (Mental Model)

```
Backend → curl verification → frontend → optional simulators
```

If something breaks, go back one step and re-verify.

---

## Notes

This document intentionally avoids:
- Redundant commands
- Hidden assumptions
- Port ambiguity
- “Magic” copy-paste steps without context

