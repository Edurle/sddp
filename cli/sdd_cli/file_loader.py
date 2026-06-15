import json


def load_value_from_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw
