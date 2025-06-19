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
import crash_handler

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
LOG_DIR  = Path(r"C:\QSTAF\logs") 



#crash_count_controller.run_watch()

# Set up logging for debugging EXE issues
if getattr(sys, 'frozen', False):
    # Running as EXE - log to file
    log_dir = r"C:\QSTAF\crashDump"
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(log_dir, "app_debug.log"),
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Redirect stderr to log file for debugging
    sys.stderr = open(os.path.join(log_dir, "app_errors.log"), "w")

def log_exception(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
sys.excepthook = log_exception

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
        Start_testCase.start_tests(CMD_DIR_CONTROL, BAT_FILE_CONTROL)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def start_traffic():
    try:
        Start_testCase.start_tests(CMD_DIR_TRAFFIC, BAT_FILE_TRAFFIC)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def run_both_with_delay():
    try:
        start_control()
        time.sleep(5)
        start_traffic()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def stop_all():
    found = Kill_process.stop_all_tests()
    msg = "All processes stopped." if found else "No processes found to stop."
    print(msg)

def run_s3_uploader():
    try:
        Start_testCase.start_tests(CMD_DIR_AWS, BAT_FILE_AWS)
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


# ─crash_counter_monitor.py ──────────────────────────────────────────────

Json = dict[str, Any]

class AppConfigMonitor:
    """
    Poll C:\\QSTAF\\app_config.json every *interval* seconds and call each
    listener with a dictionary like

        {
            "normal_DIR":  3,
            "normal_OVN":  1,
            "rdkb_DIR":    0,
            "rdkb_OVN":    5
        }

    If the file is missing or malformed the values become None.
    """

    def __init__(self, path: str | Path, interval: float = 1.0) -> None:
        self.path      = Path(path)
        self.interval  = interval
        self._stop_evt = threading.Event()
        self._thread   = threading.Thread(target=self._loop, daemon=True)
        self._last_mtime: float | None = None
        self._listeners: list[Callable[[dict[str, int | None]], None]] = []

    # –– public API –– --------------------------------------------------
    def add_listener(self, fn: Callable[[dict[str, int | None]], None]) -> None:
        self._listeners.append(fn)

    def start(self) -> None:
        self._thread.start()

    def stop(self, timeout: float = 3) -> None:
        self._stop_evt.set()
        self._thread.join(timeout)

    # –– internal –– ----------------------------------------------------
    def _loop(self) -> None:
        while not self._stop_evt.is_set():
            self._check()
            time.sleep(self.interval)

    def _check(self) -> None:
        try:
            mtime = self.path.stat().st_mtime
        except FileNotFoundError:
            self._notify(self._empty(None))
            return

        if self._last_mtime is None or mtime != self._last_mtime:
            self._last_mtime = mtime
            self._notify(self._read())

    def _read(self) -> dict[str, int | None]:
        try:
            with self.path.open(encoding="utf-8") as f:
                cfg: Json = json.load(f)
            return {
                "normal_DIR": int(cfg["normal"]["DIR_Counter"]),
                "normal_OVN": int(cfg["normal"]["OVN_Counter"]),
                "rdkb_DIR":   int(cfg["rdkb"]["DIR_Counter"]),
                "rdkb_OVN":   int(cfg["rdkb"]["OVN_Counter"]),
            }
        except Exception:            # any KeyError / JSON error
            return self._empty(None)

    @staticmethod
    def _empty(val: int | None) -> dict[str, int | None]:
        return {k: val for k in
                ("normal_DIR", "normal_OVN", "rdkb_DIR", "rdkb_OVN")}

    def _notify(self, payload: dict[str, int | None]) -> None:
        for fn in self._listeners:
            fn(payload)



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
        
        
def start_Pact_QXDM():
    Quts_controller.start_app(Quts_controller.PCAT_PATH)
    Quts_controller.start_app(Quts_controller.QXDM_PATH)

def stop_all_tools_Framework():
    stop_all()
    subprocess.run("taskkill /IM PCATApp.exe /F", shell=True)
    subprocess.run("taskkill /IM QXDM.exe /F", shell=True)
    
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
        target=crash_handler.main,
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
