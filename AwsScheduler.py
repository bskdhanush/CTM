"""
AwsScheduler.py
Pure logic for remembering a checkbox state and—if enabled—running
aws_s3_uploder.bat every day at 4 PM.

Usage from any UI:
    import AwsScheduler as aws

    aws.is_enabled()              -> bool
    aws.set_enabled(True | False) -> persist + (un)schedule
    aws.run_now()                 -> launch the BAT immediately
"""
from __future__ import annotations
import os, time, subprocess, schedule, logging

import JsonHandler as JH
from Threading import *

# -------------------------------------------------------------------- #
# Configurable paths & constants
# -------------------------------------------------------------------- 
BAT_PATH     = r"C:\QSTAF\QSTAFpy\bin\aws_s3_uploder.bat"
RUN_TIME     = "16:00"                                # 4 PM every day


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
        start_thread(target_func=_loop, daemon=True)
        _loop_started = True

def is_enabled() -> bool:
    return bool(JH.load_cfg().get("aws_scheduler_enabled", False))

def set_enabled(enable: bool) -> None:
    cfg = JH.load_cfg()
    cfg["aws_scheduler_enabled"] = bool(enable)
    JH.save_json(cfg)
    _reschedule(enable)

# Initialise on import
_reschedule(is_enabled())
_start_loop_once()
