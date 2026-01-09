import json
import os
from typing import Any

# JSON file for bracket
DATA_JSON: str = "data.json"

def load_json() -> dict[str, Any]:
    """Loads data from the JSON file. Returns an empty dict if file doesn't exist."""
    if os.path.exists(DATA_JSON):
        with open(DATA_JSON, "r") as f:
            return json.load(f)
    else:
        return {}

def save_json(data: dict[str, Any]) -> None:
    """Saves the provided dictionary to the JSON file."""
    with open(DATA_JSON, "w") as f:
        json.dump(data, f, indent=4)
        f.flush()
