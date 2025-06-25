# main_controller.py
from __future__ import annotations
import sys
import subprocess
import time
import ctypes
from tkinter import messagebox
import json, threading, time
from pathlib import Path
from typing import Callable, Any
import logging
from pathlib import Path
import builtins

import Kill_process 
import Check_updates
import Start_testCase
import Quts_controller
import Wifi_controller
import GUI as gui
import crash_cout_controller_v2 as cc

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
LOG_DIR  = Path(r"C:\QSTAF\logs") 



#crash_count_controller.run_watch()

# Set up logging for debugging EXE issues
if getattr(sys, 'frozen', False):
    # ensure both crashDump and logs folders exist
    crash_dir = r"C:\QSTAF\crashDump"
    log_dir   = r"C:\QSTAF\logs"
    for d in (crash_dir, log_dir):
        os.makedirs(d, exist_ok=True)

    # now log to files in the logs folder
    logging.basicConfig(
        filename=os.path.join(log_dir, "app_debug.log"),
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # redirect stderr into a separate file
    sys.stderr = open(os.path.join(log_dir, "app_errors.log"), "w")

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
        meta = Wifi_controller.get_meta_build_info()
    except Exception as e:
        print(f'Exception while reading Meta: {e}')
    try:
        mpss = Wifi_controller.get_mpss_build_info()
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

def start_control():
    try:
        Start_testCase.start_tests(CMD_DIR_CONTROL, BAT_FILE_CONTROL,'Control')
    except Exception as e:
        messagebox.showerror("Error", str(e))

def start_traffic():
    try:
        Start_testCase.start_tests(CMD_DIR_TRAFFIC, BAT_FILE_TRAFFIC,'Traffic')
    except Exception as e:
        messagebox.showerror("Error", str(e))

def run_both_with_delay():
    try:
        start_control()
        time.sleep(5)
        start_traffic()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def stop_framework(mode):
    found = Kill_process.stop_all_tests(mode)
    msg = "All processes stopped." if found else "No processes found to stop."
    print(msg)

def run_s3_uploader():
    try:
        Start_testCase.start_tests(CMD_DIR_AWS, BAT_FILE_AWS,None)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def restart_quts_pcat_qxdm():
    def show_status(msg: str):
        print(msg)
    Quts_controller.restart_quts_pcat_qxdm(callback=show_status)
    
def set_wifi_config(dropDown_value):
   # print(dropDown_value)
    Wifi_controller.connectBackhall()
    Wifi_controller.update_cpe_wifi_config(dropDown_value,"")
    Wifi_controller.setpassword_bandwiths()
    

def check_for_updates_integrated():
    """
    Integrated update checker that works in both .py and .exe modes
    Returns True if update was found and applied, False otherwise
    """
    try:
        # Import the update checking functionality directly
        import Check_updates
        
        # Run the update check logic
        data = Check_updates.fetch_latest_release_data()
        raw_tag = data.get("tag_name", "")
        latest_tag = raw_tag.lstrip("v")
        
        print(f"Latest release on GitHub: {latest_tag} (local: {Check_updates.LOCAL_VERSION})")
        
        if Check_updates.parse_version(latest_tag) > Check_updates.parse_version(Check_updates.LOCAL_VERSION):
            print("Newer version detected. Downloading and replacing...")
            asset_api_url, asset_name = Check_updates.find_latest_exe_asset(data)
            
            # Download the new version
            Check_updates.download_and_replace(asset_api_url, asset_name)
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
    exe_path = Check_updates.EXE_PATH
    if os.path.isfile(exe_path):
        print(f"Launching updated EXE: {exe_path} --skip-updates")
        subprocess.Popen([exe_path, "--skip-updates"], shell=False)
        sys.exit(0)
    else:
        print(f"Cannot find EXE at {exe_path}. Continuing with current version.")

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
            updater = os.path.join(get_executable_dir(), "Check_updates.py")
            if os.path.exists(updater):
                subprocess.Popen(
                    ["cmd", "/c", "start", "", sys.executable, updater],
                    shell=False
                )
                sys.exit(0)

    # 3) Fire up the GUI
    gui.launch_gui()
    '''
'''
def update_csv_plots():
    while True:
        time.sleep(20)
        copy_csv.copy_csv_main()
        
'''      
        
        
def start_Pact_only():
    print("pcat called")
    Quts_controller.start_app(Quts_controller.PCAT_PATH,"PCATApp.exe")

def start_QXDM_only():
    print("QXDM called")  
    Quts_controller.start_app(Quts_controller.QXDM_PATH,"QXDM.exe")

def start_all():
    Quts_controller.start_quts()
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
    subprocess.run("taskkill /IM QXDM.exe /F", shell=True)\


def get_internet_status():
    return 1
    
#---------to collect logs to txt------------------------
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


def main() -> None:


    # 1️⃣  Start the watcher in a daemon thread
    t = threading.Thread(
        target=cc.run_watchdog,
        daemon=True        # auto‑stops when the main program exits
    )
    t.start()
    '''
    t2 = threading.Thread(
        target=update_csv_plots,
        daemon=True  # auto‑stops when the main program exits
    )
    t2.start()
    # 2️⃣  Launch GUI (must stay on the main thread on Windows/macOS)
    '''
    run_app()

if __name__ == "__main__":
    main()
