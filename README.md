# Aquarium Management System

Simple local setup and run commands.

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install flask requests rich
python3 init_db.py
python3 server.py
```

Backend runs on:

```text
http://127.0.0.1:3001
```

## Quick checks

```bash
curl http://127.0.0.1:3001/
curl http://127.0.0.1:3001/data
```

## CLI

From the project root:

```bash
source backend/.venv/bin/activate
PYTHONPATH=. python3 -m ams_cli.ams_cli.main status
```

More commands:

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
```

Optional graph command:

```bash
pip install plotext
PYTHONPATH=. python3 -m ams_cli.ams_cli.main temp24
```

## Temperature poller

```bash
cd backend
source .venv/bin/activate
python3 services/temperature_poller.py
```
