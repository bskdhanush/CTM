from datetime import datetime
import json
import os
from pathlib import Path
from Threading import thread_lock
from Constants import APP_CONFIG_JSON, PROV_CONFIG_JSON, init_dirs

app_lock = thread_lock()
prov_lock = thread_lock()

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
    if not os.path.exists(APP_CONFIG_JSON):
        save_json(_default_cfg())

    if not os.path.exists(PROV_CONFIG_JSON):
        save_prov_json(_default_prov())
    try:
        with open(APP_CONFIG_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Config read failed – using defaults (%s)", e)
        return _default_cfg()
    
def rest_framework_timestamps(mode):
    cfg = load_json()
    cfg.update({f"{mode}_start_timestamp": "null"})
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
        return json.loads(Path(APP_CONFIG_JSON).read_text("utf-8"))
    except Exception as e:
        print(f"{APP_CONFIG_JSON} is has no data: %s", e)
        return {}

def load_prov_json() -> dict:
    try:
        return json.loads(Path(PROV_CONFIG_JSON).read_text("utf-8"))
    except Exception as e:
        print(f"{PROV_CONFIG_JSON} is has no data: %s", e)
        return {}

def save_json(cfg: dict) -> None:
    init_dirs()
    with app_lock:
        with open(APP_CONFIG_JSON, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

def save_prov_json(cfg):
    init_dirs()
    with prov_lock:
        with open(PROV_CONFIG_JSON, "w", encoding="utf-8")as f:
            json.dump(cfg, f, indent=2)

