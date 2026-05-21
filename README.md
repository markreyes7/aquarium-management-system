# Aquarium Management System

Aquarium Management System is a local command center for tracking an aquarium's health, maintenance, livestock, and environment. It combines a Flask backend, a SQLite database, Arduino/mock hardware controls, and a terminal dashboard built for quick daily checks.

The project is designed around one simple loop: log what changed, watch the trend, and make better tank decisions.

## What AMS Tracks

- Tank profile: size, water type, temperature target, lighting schedule, setup date, notes
- Water parameters: pH, ammonia, nitrite, nitrate, GH, KH, TDS
- Livestock: current in-tank animals by common name and quantity
- Maintenance: fertilizer, trimming, topoff, pump topoff, notes
- Environment: temperature history and light state
- Dashboard: a Rich-powered `ams status` view for the current tank snapshot

## Project Layout

```text
backend/                  Flask API, database schema, Arduino integration
backend/routes/           Route modules for tank profile, livestock, water, environment, maintenance
backend/schema.sql        SQLite schema
ams_cli/ams_cli/          Command-line app
ams_cli/ams_cli/main.py   CLI command routing and prompts
ams_cli/ams_cli/status_dashboard.py
                           Status dashboard rendering
```

## Backend Setup

From the project root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install flask requests rich
python3 init_db.py
python3 server.py
```

Production-style backend:

```text
http://127.0.0.1:3001
```

By default, production-style Arduino calls target:

```text
http://192.168.1.100
```

## Safe Local Development

Use the development flow when you do not want this machine to touch the real Arduino.

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

Development backend:

```text
http://127.0.0.1:3002
```

Development defaults:

```text
Database: backend/aquarium-dev.db
Arduino target: http://127.0.0.1:3999
```

## CLI

Run commands from the project root:

```bash
source backend/.venv/bin/activate
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev status
```

Use `--dev` for the local development backend on port `3002`. Omit `--dev` for the production-style backend on port `3001`.

Core commands:

```bash
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev status
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev status-json
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev tankprofile
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev updatetankprofile
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev waterparams
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev livestock
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev addlivestock
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev removelivestock
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev logs --limit 10
```

Hardware and maintenance commands:

```bash
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev lightstatus
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev lighton
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev lightoff
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev lightauto
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev fertilize
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev trimmed
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev topoff
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev runtopoff
```

Optional graph command:

```bash
pip install plotext
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev temp24
```

## API Quick Checks

Production-style:

```bash
curl http://127.0.0.1:3001/
curl http://127.0.0.1:3001/data
```

Development:

```bash
curl http://127.0.0.1:3999/light/currentStatus
curl http://127.0.0.1:3002/
curl http://127.0.0.1:3002/data
curl http://127.0.0.1:3002/livestock
```

## Tank Profile API

View the tank profile:

```bash
curl http://127.0.0.1:3002/tankprofile
```

Update the tank profile:

```bash
curl -X PUT http://127.0.0.1:3002/update/tankprofile \
  -H 'Content-Type: application/json' \
  -d '{"size_gallons":10,"water_type":"freshwater","target_temperature_min":72,"target_temperature_max":78,"lighting_schedule":"10:00-18:00","setup_date":"2026-05-07","notes":"Development profile"}'
```

## Livestock API

Add livestock:

```bash
curl -X POST http://127.0.0.1:3002/livestock \
  -H 'Content-Type: application/json' \
  -d '{"common_name":"Cherry shrimp","livestock_type":"shrimp","quantity":10}'
```

Remove livestock from the tank:

```bash
curl -X POST http://127.0.0.1:3002/livestock/remove \
  -H 'Content-Type: application/json' \
  -d '{"common_name":"Cherry shrimp","quantity":3}'
```

## Environment Overrides

```text
AMS_DATABASE=/path/to/dev.db
AMS_ARDUINO_BASE_URL=http://127.0.0.1:3999
AMS_SERVER_HOST=127.0.0.1
AMS_SERVER_PORT=3002
AMS_BASE_URL=http://127.0.0.1:3002
```

## Temperature Poller

```bash
cd backend
source .venv/bin/activate
python3 services/temperature_poller.py
```
