# Local Dev Checklist

This checklist keeps local development separate from the production-style backend and real Arduino target.

## 1. Start From The Project Root

```bash
cd /Users/markreyes/aquariummanagementsystem/aquarium-management-system
```

If commands ever load an older CLI, confirm Python is importing this project:

```bash
PYTHONPATH=. python3 -c "import ams_cli.ams_cli.main as m; print(m.__file__)"
```

Expected path:

```text
/Users/markreyes/aquariummanagementsystem/aquarium-management-system/ams_cli/ams_cli/main.py
```

## 2. Create Or Activate The Environment

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

## 3. Initialize The Database

Production-style database:

```bash
cd backend
source .venv/bin/activate
python3 init_db.py
```

Default database:

```text
backend/aquarium.db
```

Development database is initialized automatically by `dev_server.py`, but you can also initialize it explicitly:

```bash
cd backend
source .venv/bin/activate
AMS_DATABASE="$PWD/aquarium-dev.db" python3 init_db.py
```

Development database:

```text
backend/aquarium-dev.db
```

## 4. Local Development Mode

Use this mode for normal feature work. It talks to the mock Arduino and development database.

Terminal 1, mock Arduino:

```bash
cd backend
source .venv/bin/activate
python3 mock_arduino.py
```

Mock Arduino URL:

```text
http://127.0.0.1:3999
```

Terminal 2, development backend:

```bash
cd backend
source .venv/bin/activate
python3 dev_server.py
```

Development backend URL:

```text
http://127.0.0.1:3002
```

Development defaults:

```text
AMS_DATABASE=backend/aquarium-dev.db
AMS_ARDUINO_BASE_URL=http://127.0.0.1:3999
AMS_SERVER_HOST=127.0.0.1
AMS_SERVER_PORT=3002
```

## 5. Production-Style Mode

Use this only when you intend to run against the normal backend settings.

```bash
cd backend
source .venv/bin/activate
python3 server.py
```

Production-style backend URL:

```text
http://127.0.0.1:3001
```

Production-style defaults:

```text
AMS_DATABASE=backend/aquarium.db
AMS_ARDUINO_BASE_URL=http://192.168.1.100
AMS_SERVER_HOST=0.0.0.0
AMS_SERVER_PORT=3001
```

## 6. Quick Health Checks

Development:

```bash
curl http://127.0.0.1:3999/light/currentStatus
curl http://127.0.0.1:3002/
curl http://127.0.0.1:3002/data
curl http://127.0.0.1:3002/livestock
```

Production-style:

```bash
curl http://127.0.0.1:3001/
curl http://127.0.0.1:3001/data
```

## 7. CLI Commands For Local Development

Run these from the project root:

```bash
source backend/.venv/bin/activate
```

Dashboard and raw status:

```bash
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev status
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev status-json
```

Tank profile:

```bash
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev tankprofile
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev updatetankprofile
```

Water parameters:

```bash
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev waterparams
```

Livestock:

```bash
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev livestock
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev addlivestock
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev removelivestock
```

Maintenance and logs:

```bash
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev fertilize
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev trimmed
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev topoff
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev runtopoff
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev logs --limit 10
```

Light controls:

```bash
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev lightstatus
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev lighton
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev lightoff
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev lightauto
```

Temperature graph:

```bash
PYTHONPATH=. python3 -m ams_cli.ams_cli.main --dev temp24
```

## 8. CLI Commands For Production-Style Backend

Run the same commands without `--dev`:

```bash
PYTHONPATH=. python3 -m ams_cli.ams_cli.main status
PYTHONPATH=. python3 -m ams_cli.ams_cli.main status-json
PYTHONPATH=. python3 -m ams_cli.ams_cli.main tankprofile
PYTHONPATH=. python3 -m ams_cli.ams_cli.main updatetankprofile
PYTHONPATH=. python3 -m ams_cli.ams_cli.main livestock
PYTHONPATH=. python3 -m ams_cli.ams_cli.main addlivestock
PYTHONPATH=. python3 -m ams_cli.ams_cli.main removelivestock
```

You can also target a backend explicitly:

```bash
AMS_BASE_URL=http://127.0.0.1:3002 PYTHONPATH=. python3 -m ams_cli.ams_cli.main status
```

## 9. Direct API Examples

Update tank profile:

```bash
curl -X PUT http://127.0.0.1:3002/update/tankprofile \
  -H 'Content-Type: application/json' \
  -d '{"size_gallons":10,"water_type":"freshwater","target_temperature_min":72,"target_temperature_max":78,"lighting_schedule":"10:00-18:00","setup_date":"2026-05-07","notes":"Development profile"}'
```

Add livestock:

```bash
curl -X POST http://127.0.0.1:3002/livestock \
  -H 'Content-Type: application/json' \
  -d '{"common_name":"Cherry shrimp","livestock_type":"shrimp","quantity":10}'
```

Remove livestock:

```bash
curl -X POST http://127.0.0.1:3002/livestock/remove \
  -H 'Content-Type: application/json' \
  -d '{"common_name":"Cherry shrimp","quantity":3}'
```

Run topoff through the mock Arduino:

```bash
curl -X POST http://127.0.0.1:3002/update/runtopoff \
  -H 'Content-Type: application/json' \
  -d '{"seconds":1,"notes":"dev mock topoff"}'
```

## 10. Optional Temperature Poller

```bash
cd backend
source .venv/bin/activate
python3 services/temperature_poller.py
```
