"""
aws_scheduler.py
Pure logic for remembering a checkbox state and—if enabled—running
aws_s3_uploder.bat every day at 4 PM.

Usage from any UI:
    import aws_scheduler as aws

    aws.is_enabled()              -> bool
    aws.set_enabled(True | False) -> persist + (un)schedule
    aws.run_now()                 -> launch the BAT immediately
"""
from __future__ import annotations
import os, json, threading, time, subprocess, schedule, logging, datetime

# -------------------------------------------------------------------- #
# Configurable paths & constants
# -------------------------------------------------------------------- #
CONFIG_DIR   = r"C:\QSTAF\CTM_logs"
CONFIG_FILE  = os.path.join(CONFIG_DIR, "app_config.json")
BAT_PATH     = r"C:\QSTAF\QSTAFpy\bin\aws_s3_uploder.bat"
RUN_TIME     = "16:00"                                # 4 PM every day

# -------------------------------------------------------------------- #
# Logging (optional)
# -------------------------------------------------------------------- #
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)

# -------------------------------------------------------------------- #
# Private helpers – JSON persistence
# -------------------------------------------------------------------- #
def _ensure_dir() -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)

def _default_cfg() -> dict:
    return {"aws_scheduler_enabled": True}

def _load_cfg() -> dict:
    _ensure_dir()
    if not os.path.exists(CONFIG_FILE):
        _save_cfg(_default_cfg())
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.warning("Config read failed – using defaults (%s)", e)
        return _default_cfg()

def _save_cfg(cfg: dict) -> None:
    _ensure_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

# -------------------------------------------------------------------- #
#  Batch launcher – opens in a visible console
# -------------------------------------------------------------------- #
def _run_bat() -> None:
    logging.info("Launching AWS BAT …")
    if not os.path.exists(BAT_PATH):
        logging.error("Batch file not found: %s", BAT_PATH)
        return
    try:
        subprocess.Popen(
            ["cmd", "/c", BAT_PATH],                  # "/k" if you prefer it to stay open
            cwd=os.path.dirname(BAT_PATH),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    except Exception as e:
        logging.exception("Failed to start BAT: %s", e)

# Public “run now” helper (handy for a manual button)
run_now = _run_bat

# -------------------------------------------------------------------- #
#  Scheduler plumbing
# -------------------------------------------------------------------- #
_job: schedule.Job | None = None
_loop_started = False

def _reschedule(enable: bool) -> None:
    """(Re)create or cancel the daily job."""
    global _job
    if _job:
        schedule.cancel_job(_job)
        _job = None
    if enable:
        logging.info("Scheduling daily run at %s", RUN_TIME)
        _job = schedule.every().day.at(RUN_TIME).do(_run_bat)

def _loop() -> None:
    """Background thread that drives `schedule`."""
    logging.info("Scheduler loop STARTED")
    while True:
        schedule.run_pending()
        time.sleep(1)

def _start_loop_once() -> None:
    global _loop_started
    if not _loop_started:
        threading.Thread(target=_loop, daemon=True).start()
        _loop_started = True

# -------------------------------------------------------------------- #
#  Public API
# -------------------------------------------------------------------- #
def is_enabled() -> bool:
    return bool(_load_cfg().get("aws_scheduler_enabled", False))

def set_enabled(enable: bool) -> None:
    cfg = _load_cfg()
    cfg["aws_scheduler_enabled"] = bool(enable)
    _save_cfg(cfg)
    _reschedule(enable)

# Initialise on import
_reschedule(is_enabled())
_start_loop_once()
