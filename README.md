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

Production-style backend runs on:

```text
http://127.0.0.1:3001
```

By default, production-style Arduino calls still target `http://192.168.1.100`.

## Safe local development

Use this flow when you do not want this machine to touch the production Arduino/server.

Terminal 1, run the fake Arduino:

```bash
cd backend
source .venv/bin/activate
python3 mock_arduino.py
```

Terminal 2, run the development backend:

```bash
cd backend
source .venv/bin/activate
python3 dev_server.py
```

The development backend runs on:

```text
http://127.0.0.1:3002
```

The development setup uses:

```text
Database: backend/aquarium-dev.db
Arduino target: http://127.0.0.1:3999
```

For CLI commands against the dev backend:

```bash
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev status
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev status-demo
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev lightstatus
```

Environment overrides:

```text
AMS_DATABASE=/path/to/dev.db
AMS_ARDUINO_BASE_URL=http://127.0.0.1:3999
AMS_SERVER_HOST=127.0.0.1
AMS_SERVER_PORT=3002
```

## Quick checks

```bash
curl http://127.0.0.1:3001/
curl http://127.0.0.1:3001/data
```

Development quick checks:

```bash
curl http://127.0.0.1:3999/light/currentStatus
curl http://127.0.0.1:3002/
curl http://127.0.0.1:3002/data
curl -X POST http://127.0.0.1:3002/environment/light/on
curl -X POST http://127.0.0.1:3002/update/runtopoff \
  -H 'Content-Type: application/json' \
  -d '{"seconds":1,"notes":"dev mock topoff"}'
```

## Tank profile

View the tank profile:

```bash
curl http://127.0.0.1:3002/tank-profile
```

Update the tank profile:

```bash
curl -X PATCH http://127.0.0.1:3002/tank-profile \
  -H 'Content-Type: application/json' \
  -d '{"size_gallons":10,"water_type":"freshwater","target_temperature_min":72,"target_temperature_max":78,"lighting_schedule":"10:00-18:00","setup_date":"2026-05-07","notes":"Development profile"}'
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
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev status-demo
PYTHONPATH=. python3 -m ams_cli.ams_cli.main waterparams
PYTHONPATH=. python3 -m ams_cli.ams_cli.main tankprofile
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
