import json
import os

# JSON file for bracket
DATA_JSON = "data.json"

def loadJson():
    """Loads data from the JSON file. Returns an empty dict if file doesn't exist."""
    if os.path.exists(DATA_JSON):
        with open(DATA_JSON, "r") as f:
            return json.load(f)
    else:
        return {}

def saveJson(data):
    """Saves the provided dictionary to the JSON file."""
    with open(DATA_JSON, "w") as f:
        json.dump(data, f, indent=4)