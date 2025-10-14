from datetime import datetime
import json
import os
from pathlib import Path
from Threading import thread_lock

LOG_DIR  = Path(r"C:\QSTAF\CTM_logs")
CONFIG_FILE  = os.path.join(LOG_DIR, "app_config.json")
PROV_CONFIG_FILE = os.path.join(LOG_DIR, "prov_config.json")
app_lock = thread_lock()
prov_lock = thread_lock()

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
        "traffic_start_timestamp": "null",
        "Local_downloadPath": "",
        "Auto_download": "false",
        "SpeedTestData":[],
    }

def _default_prov():
    return {
        "provisioning_path": "No path Selected",
        "magic_string": "No Magic String Found",
        "market": "Pls enter market",
        "name": "Enter name (eg. Kiran or Aniket)",
        "fst_id": "Enter FST ID",
        "operator": "Enter operator (TMO / ATT / VZW)",
        "tdc_serial": "Enter TDC Serial"
    }

def load_cfg():
    _ensure_dir()

    if not os.path.exists(CONFIG_FILE):
        save_json(_default_cfg())

    if not os.path.exists(PROV_CONFIG_FILE):
        print(" prov check called ")
        save_prov_json(_default_prov())
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Config read failed – using defaults (%s)", e)
        return _default_cfg()
    
def rest_framework_timestamps(mode):
    cfg=load_json()
    cfg[f"{mode}_start_timestamp"] = "null"
    save_json(cfg)

def set_time(mode):
    TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S"
    now = datetime.now()
    now_str = now.strftime(TIMESTAMP_FMT)
    cfg=load_json()
    cfg[f"{mode}_start_timestamp"] = now_str
    save_json(cfg)


def load_json() -> dict:
    try:
        return json.loads(Path(CONFIG_FILE).read_text("utf-8"))
    except Exception as e:
        print("app_config.json is has no data: %s", e)
        return {}

def load_prov_json() -> dict:
    try:
        return json.loads(Path(PROV_CONFIG_FILE).read_text("utf-8"))
    except Exception as e:
        print("prov_config.json is has no data: %s", e)
        return {}

def save_json(cfg: dict) -> None:
    _ensure_dir()
    with app_lock:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

def save_prov_json(cfg):
    with prov_lock:
        with open(PROV_CONFIG_FILE, "w", encoding="utf-8")as f:
            json.dump(cfg, f, indent=2)

def get_json_path():
    return CONFIG_FILE