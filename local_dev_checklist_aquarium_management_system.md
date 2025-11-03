# 🧰 Local Development Checklist

A reproducible guide to run the Aquarium Management System on macOS or Linux. Assumes:
- **Backend**: Flask (Python)
- **Frontend**: React (Create React App)
- **Simulator**: `simulator.py`
- **Default backend port**: **3001** (proxy points here)

---

## One‑Time Setup (both machines)
- Install **Python 3.10+** and **Node 18/20** (via `nvm`).
- Commit dependency locks:
  - `requirements.txt` (generate on a working machine: `pip freeze > requirements.txt`)
  - `package-lock.json`
- Recommended repo structure:
  - `backend/` (Flask app with `server.py`)
  - `frontend/` (React app with `package.json`)
  - `simulator.py` (or `tools/`)

---

## Backend (Flask) – Setup & Run
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
pip install -r requirements.txt

# Start Flask on 3001 to match the frontend proxy
flask --app server run --debug --host 127.0.0.1 --port 3001
```
**Verify**
```bash
curl -v http://127.0.0.1:3001/
# Replace with real route (e.g., /items, /temp)
curl -v http://127.0.0.1:3001/items
```

> Tip: If you prefer port 5000, change the frontend proxy accordingly (see Frontend section).

---

## Frontend (React) – Setup & Run
```bash
cd frontend
nvm install 20
nvm use 20
node -v

# Install exactly from lockfile when available
npm ci   # (fallback: npm install)
```
`package.json` must have the proxy pointing to the backend:
```json
{
  "proxy": "http://127.0.0.1:3001"
}
```
Start React:
```bash
npm start
```

Use **relative URLs** in your React code (e.g., `axios.get('/items')`) so the proxy works. If you call an absolute URL (e.g., `http://127.0.0.1:5000/items`), the proxy is bypassed.

---

## Simulator – Setup & Run
In `simulator.py`, use one source of truth for the API base URL:
```python
import os
BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:3001")
```
Optionally add a quick wait‑retry before sending requests:
```python
import time, requests

def wait_for_api(base, tries=20, delay=0.25):
    for _ in range(tries):
        try:
            requests.get(f"{base}/", timeout=2).raise_for_status()
            return True
        except Exception:
            time.sleep(delay)
    return False
```
Run the simulator **after** the backend is up:
```bash
source backend/.venv/bin/activate
python simulator.py
```

---

## Quick Health Checks (when anything breaks)
- **Is backend listening on the expected port?**
  ```bash
  ss -ltnp | grep -E '3001|5000'
  curl -v http://127.0.0.1:3001/
  ```
- **Does the route exist?** Frontend fetches `/temp` → Flask must have `@app.route('/temp')`.
- **Correct protocol/host/port?** Use `http://127.0.0.1:3001` unless you changed it.
- **Right virtualenv?**
  ```bash
  which python; which flask
  python -c "import flask, sys; print(flask.__version__, sys.version)"
  ```
- **Proxy actually targeting the backend?**
  - `frontend/package.json` → `"proxy": "http://127.0.0.1:3001"`
  - Restart React after proxy changes: `Ctrl+C` then `npm start`.
  - Use **relative** API paths in the frontend.
- **Skip proxy (alternative):** enable CORS in Flask and call full backend URL from React.

---

## VS Code Tips
- Select interpreter: **backend/.venv/bin/python**.
- Optional `launch.json` to run Flask consistently:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Flask: run",
      "type": "python",
      "request": "launch",
      "module": "flask",
      "args": ["--app", "server", "run", "--debug", "--host", "127.0.0.1", "--port", "3001"],
      "console": "integratedTerminal"
    }
  ]
}
```

---

## Consistency Rules (prevent drift)
- Always commit `requirements.txt` and `package-lock.json`.
- On a new machine:
  ```bash
  # Backend
  pip install -r backend/requirements.txt
  # Frontend
  cd frontend && npm ci
  nvm use 20
  ```
- Optional `.env` at repo root (used by simulator):
  ```
  API_BASE_URL=http://127.0.0.1:3001
  ```

---

## Common Errors → Fast Fix
- **ECONNREFUSED (proxy/simulator)** → Backend not running on that port. Start Flask on 3001 or update proxy to match.
- **“Could not locate a Flask application”** → Use `flask --app server run` (or `server:create_app`), run from backend folder, ensure `app = Flask(__name__)` exists.
- **Import/path issues** → Start from repo/backend root; use `Path(__file__).parent`‑based paths in Python for robustness.
- **CORS errors** → Use CRA proxy or enable `flask-cors` in the backend.

---

## Copy‑Paste Quickstart (fresh machine)
```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
flask --app server run --debug --host 127.0.0.1 --port 3001

# (new terminal) Frontend
cd frontend
nvm install 20 && nvm use 20
npm ci
npm start

# (new terminal) Sanity checks
curl -v http://127.0.0.1:3001/
# If your route is /items
curl -v http://127.0.0.1:3001/items

# (optional) Simulator after backend is up
source backend/.venv/bin/activate
API_BASE_URL=http://127.0.0.1:3001 python simulator.py
```

Happy hacking 🐠

