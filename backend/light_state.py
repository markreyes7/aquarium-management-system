def normalize_light_state(value):
    if isinstance(value, bool):
        return int(value)
    elif isinstance(value, int) and value in (0, 1):
        return value
    elif isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("0", "off", "false"):
            return 0
        if normalized in ("1", "on", "true"):
            return 1
    return None
