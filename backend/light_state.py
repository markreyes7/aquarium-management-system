from db import get_db
from datetime import datetime

global time_set


def normalize_light_state(value):
    if isinstance(value, bool):
        return int(value)
    elif isinstance(value, int) and value in (0, 1):
        return value
    elif isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("0", "off", "false"):
            return 0
        elif normalized in ("1", "on", "true"):
            return 1
    return None


def record_light_state(state):
    normalized_state = normalize_light_state(state)
    if normalized_state is None:
        return None

    db = get_db()
    db.execute(
        "INSERT INTO light_log (state, recorded_at) VALUES (?, CURRENT_TIMESTAMP)",
        (normalized_state,)
    )
    db.execute(
        "UPDATE tank_status SET light_state = ? WHERE id = 1",
        (normalized_state,)
    )
    db.commit()
    return normalized_state
