from datetime import datetime
import json
import os
from pathlib import Path
import MainController as mc

LOG_DIR  = Path(r"C:\QSTAF\CTM_logs")
CONFIG_FILE  = os.path.join(LOG_DIR, "app_config.json")
POV_config_FIle=os.path.join(LOG_DIR, "POV_config.json")


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

def _default_POV():
    return {
        "POV_Path": "No path Selected",
        "Magic_string": "No Magic String Found",
        "Market": "Pls enter market",
        "Name": "Kiran",
        "FSTID": "set fst id"
    }

def load_cfg():
    _ensure_dir()

    if not os.path.exists(CONFIG_FILE):
        save_json(_default_cfg())

    if not os.path.exists(POV_config_FIle):
        print(" pov check called ")
        
        save_POV_json(_default_POV())

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
    now = datetime.now()
    now_str = now.strftime(mc.TIMESTAMP_FMT)
    cfg=load_json()
    cfg[f"{mode}_start_timestamp"] = now_str
    save_json(cfg)



def load_json() -> dict:
    try:
        return json.loads(Path(CONFIG_FILE).read_text("utf-8"))
    except Exception as e:
        print("App_json is has no data: %s", e)
        return {}
def load_POV_json() -> dict:
    try:
        return json.loads(Path(POV_config_FIle).read_text("utf-8"))
    except Exception as e:
        print("App_json is has no data: %s", e)
        return {}

def save_json(cfg: dict) -> None:
    _ensure_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def save_POV_json(cfg):
    with open(POV_config_FIle,"w", encoding="utf-8")as f:
        json.dump(cfg, f, indent=2)

def get_json_path():
    return CONFIG_FILE