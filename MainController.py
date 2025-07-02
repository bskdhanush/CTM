# MainController.py
from __future__ import annotations
import sys
import subprocess
import time
from datetime import datetime
import ctypes
from tkinter import messagebox
import json, threading, time
import logging

import KillProcess
import CheckUpdates
import StartTestCase
import QutsController
import WifiController
import GUI as gui
import CrashCountController as cc
import JsonHandler as JH

# ── NEW IMPORT ────────────────────────────────────────────────────────────────
# We need to know when to skip updates:
import os

# Constants for batch file directories and names
CMD_DIR_CONTROL  = r"C:\QSTAF\QSTAFpy\bin\Control_laptop\Windows"
BAT_FILE_CONTROL = "Run_framework.bat"
CMD_DIR_TRAFFIC  = r"C:\QSTAF\QSTAFpy\bin\Traffic_laptop\Windows"
BAT_FILE_TRAFFIC = "Run_framework.bat"
CMD_DIR_AWS      = r"C:\QSTAF\QSTAFpy\bin"
BAT_FILE_AWS     = "aws_s3_uploder.bat"
QSTAF_file_path  =r"C:\QSTAF\QSTAFpy\version.txt"
TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S"
MODES = ("control", "traffic")
DEFAULT_TIMER_HOURS = 6


# CrashCountController.run_watch()

# Set up logging for debugging EXE issues
if getattr(sys, 'frozen', False):
    # ensure both crashDump and logs folders exist
    os.makedirs(JH.LOG_DIR, exist_ok=True)

    # redirect stderr into a separate file
    sys.stderr = open(os.path.join(JH.LOG_DIR, "app_errors.log"), "w")

def log_exception(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
sys.excepthook = log_exception

def get_qstaf_version():
    """Read and return the version string from the given text file."""
    try:
        with open(QSTAF_file_path, 'r', encoding='utf-8') as f:
            # strip off any whitespace/newlines
            return f.read()
    except Exception as e:
        # fallback if file’s missing or unreadable
        return "Unknown"

def get_meta_mpss():
    meta = "UNKNOWN"
    mpss = "UNKNOWN"
    try:
        meta = WifiController.get_meta_build_info()
    except Exception as e:
        print(f'Exception while reading Meta: {e}')
    try:
        mpss = WifiController.get_mpss_build_info()
    except Exception as e:
        print(f'Exception while reading MPSS: {e}')

    return meta, mpss

def get_executable_dir():
    """Get the directory where the executable is located, works for both .py and .exe"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as Python script
        return os.path.dirname(os.path.abspath(__file__))

def is_running_as_exe():
    """Check if we're running as a compiled executable"""
    return getattr(sys, 'frozen', False)

def ensure_admin():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            if is_running_as_exe():
                # If running as EXE, restart the EXE with admin privileges
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
            else:
                # If running as Python script
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
            sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Admin check failed: {e}")
        sys.exit(1)

def start_framework(mode):
    if mode.lower() == 'control':
        try:
            StartTestCase.start_tests(CMD_DIR_CONTROL, BAT_FILE_CONTROL,'Control')
            JH.set_time(mode)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    elif mode.lower() == 'traffic':
        try:
            StartTestCase.start_tests(CMD_DIR_TRAFFIC, BAT_FILE_TRAFFIC,'Traffic')
            JH.set_time(mode)
        except Exception as e:
            messagebox.showerror("Error", str(e))
'''
def run_both_with_delay():
    try:
        start_control()
        time.sleep(5)
        start_traffic()
    except Exception as e:
        messagebox.showerror("Error", str(e))
'''
def stop_framework(mode):
    found = KillProcess.stop_all_tests(mode)
    JH.rest_framework_timestamps(mode)
    msg = "All processes stopped." if found else "No processes found to stop."
    print(msg)

def run_s3_uploader():
    try:
        StartTestCase.start_tests(CMD_DIR_AWS, BAT_FILE_AWS,None)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def restart_quts_pcat_qxdm():
    def show_status(msg: str):
        print(msg)
    QutsController.restart_quts_pcat_qxdm(callback=show_status)
    
def set_wifi_config(dropDown_value):
   # print(dropDown_value)
    # WifiController.connectBackhaul()
    WifiController.update_cpe_wifi_config(dropDown_value,"")
    # WifiController.setpassword_bandwiths()


def check_restart_timer():
    """
    Every 5 minutes, for each mode:
      - load config
      - if timestamp is null → ignore that mode entirely
      - else if elapsed >= timer → restart and update timestamp
    """
    while True:
        cfg = JH.load_json()
        # compute relaunch period in seconds
        relaunch_timer = cfg.get("relaunch_timer", DEFAULT_TIMER_HOURS)
        try:
            hrs = int(relaunch_timer)
        except (TypeError, ValueError):
            hrs = DEFAULT_TIMER_HOURS
        relaunch_timer = hrs *3600 

        now = datetime.now()
        now_str = now.strftime(TIMESTAMP_FMT)

        for mode in MODES:
            ts_str = cfg.get(f"{mode}_start_timestamp")

            # **IGNORE** if no timestamp or explicitly "null"
            if not ts_str or ts_str.lower() == "null":
                print(f"invalid time stamp found for {mode}")
                continue

            # parse & check elapsed
            start_time = datetime.strptime(ts_str, TIMESTAMP_FMT)
            elapsed = (now - start_time).total_seconds()
            if elapsed >= relaunch_timer:
                stop_framework(mode)
                cfg[f"{mode}_start_timestamp"] = now_str
                JH.save_json(cfg)
                time.sleep(10)
                start_framework(mode)
                
        time.sleep(300)

'''
def check_for_updates_integrated():
    """
    Integrated update checker that works in both .py and .exe modes
    Returns True if update was found and applied, False otherwise
    """
    try:
        # Import the update checking functionality directly
        import CheckUpdates
        
        # Run the update check logic
        data = CheckUpdates.fetch_latest_release_data()
        relaunch_timer_tag = data.get("tag_name", "")
        latest_tag = relaunch_timer_tag.lstrip("v")
        
        print(f"Latest release on GitHub: {latest_tag} (local: {CheckUpdates.LOCAL_VERSION})")
        
        if CheckUpdates.parse_version(latest_tag) > CheckUpdates.parse_version(CheckUpdates.LOCAL_VERSION):
            print("Newer version detected. Downloading and replacing...")
            asset_api_url, asset_name = CheckUpdates.find_latest_exe_asset(data)
            
            # Download the new version
            CheckUpdates.download_and_replace(asset_api_url, asset_name)
            print(f"Replaced old EXE with version {latest_tag}.")
            
            # Launch the updated EXE and exit
            launch_updated_exe()
            return True
        else:
            print("Already up to date.")
            return False
            
    except Exception as exc:
        print(f"Update check failed: {exc}")
        return False


def launch_updated_exe():
    """Launch the updated executable"""
    exe_path = CheckUpdates.EXE_PATH
    if os.path.isfile(exe_path):
        print(f"Launching updated EXE: {exe_path} --skip-updates")
        subprocess.Popen([exe_path, "--skip-updates"], shell=False)
        sys.exit(0)
    else:
        print(f"Cannot find EXE at {exe_path}. Continuing with current version.")
'''

def run_app() -> None:
    """Entry‑point called by QSTAF_Tool.exe"""
    # 1) Require admin
    ensure_admin()

    #commont the below line and uncomment step 2 to check for updates
    gui.launch_gui()

    '''
    # 2) One‑time update check unless the flag is present
    if "--skip-updates" not in sys.argv:
        if is_running_as_exe():
            if check_for_updates_integrated():
                # New version will relaunch, so stop here
                return
        else:
            # Running from .py – spawn updater in separate console
            updater = os.path.join(get_executable_dir(), "CheckUpdates.py")
            if os.path.exists(updater):
                subprocess.Popen(
                    ["cmd", "/c", "start", "", sys.executable, updater],
                    shell=False
                )
                sys.exit(0)

    # 3) Fire up the GUI
    gui.launch_gui()
    '''

        
def start_Pact_only():
    print("pcat called")
    QutsController.start_app(QutsController.PCAT_PATH,"PCATApp.exe")

def start_QXDM_only():
    print("QXDM called")
    QutsController.start_app(QutsController.QXDM_PATH,"QXDM.exe")

def start_all():
    QutsController.start_quts()
    start_Pact_only()
    start_QXDM_only()

def stop_pcat_only():
    print("Stopped pcat")
    subprocess.run("taskkill /IM PCATApp.exe /F", shell=True)

def stop_qxdm_only():
    print("Stopped qxdm")
    subprocess.run("taskkill /IM QXDM.exe /F", shell=True)

def stop_all_tools_Framework():
    stop_framework(mode="control")
    stop_framework(mode="")
    subprocess.run("taskkill /IM PCATApp.exe /F", shell=True)
    subprocess.run("taskkill /IM QXDM.exe /F", shell=True)

   
#---------to collect logs to txt------------------------
'''
LOG_DIR.mkdir(parents=True, exist_ok=True) 
LOG_PATH = LOG_DIR / "qstaf_tool.log" 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler()          # still prints to console if visible
    ],
)
log = logging.getLogger(__name__)
builtins.print = lambda *a, **kw: log.info(" ".join(map(str, a)))
'''

def main() -> None:

    # Start the watcher in a daemon thread
    t = threading.Thread(
        target=cc.run_watchdog,
        daemon=True        # auto‑stops when the main program exits
    )
    t.start()
    
    t2 = threading.Thread(
        target=check_restart_timer,
        daemon=True  # auto‑stops when the main program exits
    )
    t2.start()

    # Launch GUI (must stay on the main thread on Windows/macOS)
    run_app()

if __name__ == "__main__":
    main()
