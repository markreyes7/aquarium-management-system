# Local Dev Checklist

## 1. Create a venv

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install flask requests rich
```

Optional for the CLI temperature graph:

```bash
pip install plotext
```

## 2. Initialize the database

```bash
cd backend
source .venv/bin/activate
python3 init_db.py
```

## 3. Run the backend

```bash
cd backend
source .venv/bin/activate
python3 server.py
```

Backend URL:

```text
http://127.0.0.1:3001
```

## 4. Quick checks

```bash
curl http://127.0.0.1:3001/
curl http://127.0.0.1:3001/data
```

## 5. Run the CLI

From the project root:

```bash
source backend/.venv/bin/activate
PYTHONPATH=. python3 -m ams_cli.ams_cli.main status
```

Useful commands:

```bash
PYTHONPATH=. python3 -m ams_cli.ams_cli.main status-demo
PYTHONPATH=. python3 -m ams_cli.ams_cli.main logs --limit 10
PYTHONPATH=. python3 -m ams_cli.ams_cli.main lightstatus
PYTHONPATH=. python3 -m ams_cli.ams_cli.main lighton
PYTHONPATH=. python3 -m ams_cli.ams_cli.main lightoff
PYTHONPATH=. python3 -m ams_cli.ams_cli.main lightauto
PYTHONPATH=. python3 -m ams_cli.ams_cli.main fertilize
PYTHONPATH=. python3 -m ams_cli.ams_cli.main trimmed
PYTHONPATH=. python3 -m ams_cli.ams_cli.main topoff
PYTHONPATH=. python3 -m ams_cli.ams_cli.main runtopoff
PYTHONPATH=. python3 -m ams_cli.ams_cli.main temp24
```

## 6. Optional temperature poller

```bash
cd backend
source .venv/bin/activate
python3 services/temperature_poller.py
```
