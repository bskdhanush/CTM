import json
import os
from pathlib import Path

LOG_DIR  = Path(r"C:\QSTAF\CTM_logs")
CONFIG_FILE  = os.path.join(LOG_DIR, "app_config.json")

def _ensure_dir() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)

def _default_cfg() -> dict:
    return {
        "aws_scheduler_enabled": "true",
        "control_start_timestamp": "null",
        "crash_counter": 0,
        "crash_last_timestamp": "null",
        "normalcrash_last_timestamp": "null",
        "previous_crash_dir": "null",
        "previous_normalcrash_dir": "null",
        "previous_rdkbcrash_dir": "null",
        "rdkbcrash_counter": 0,
        "rdkbcrash_last_timestamp": "null",
        "relaunch_control": "false",
        "relaunch_timer": 6,
        "relaunch_traffic": "false",
        "traffic_start_timestamp": "null"
    }

def _load_cfg() -> dict:
    _ensure_dir()
    if not os.path.exists(CONFIG_FILE):
        save_json(_default_cfg())
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Config read failed – using defaults (%s)", e)
        return _default_cfg()



def load_json() -> dict:
    try:
        return json.loads(Path(CONFIG_FILE).read_text("utf-8"))
    except Exception as e:
        print("App_json is has no data: %s", e)
        return {}

def save_json(cfg: dict) -> None:
    _ensure_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)