# main_controller.py
import sys
import subprocess
import time
import ctypes
from tkinter import messagebox

import Kill_process
import Start_testCase
import Quts_conroller
import Check_updates
import GUI as gui

# Constants for batch file directories and names
CMD_DIR_CONTROL = r"C:\QSTAF\QSTAFpy\bin\Control_laptop\Windows"
BAT_FILE_CONTROL = "Run_framework.bat"
CMD_DIR_TRAFFIC = r"C:\QSTAF\QSTAFpy\bin\Traffic_laptop\Windows"
BAT_FILE_TRAFFIC = "Run_framework.bat"
CMD_DIR_AWS = r"C:\QSTAF\QSTAFpy\bin"
BAT_FILE_AWS = "aws_s3_uploder.bat"

def ensure_admin():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
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
    #messagebox.showinfo("Info", msg)
    print(msg)

def run_s3_uploader():
    try:
        Start_testCase.start_tests(CMD_DIR_AWS, BAT_FILE_AWS)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def restart_quts_pcat_qxdm():
    def show_status(msg: str):
        print(msg)
    Quts_conroller.restart_quts_pcat_qxdm(callback=show_status)

def check_for_updates() -> bool:
    """
    Perform an update check. Returns True if an update was downloaded and should trigger a restart.
    """
    try:
        updated = Check_updates.main_update_check()
        if updated:
            print("[INFO] Update applied, restarting...")
        return bool(updated)
    except Exception as e:
        print(f"[WARNING] Update check failed: {e}")
        return False

def run_app():
    # Ensure running with administrative privileges
    ensure_admin()
    # Check for updates and restart if needed
    if check_for_updates():
        exe_path = sys.executable
        subprocess.Popen([exe_path] + sys.argv[1:])
        sys.exit(0)
    # Launch the GUI
    gui.launch_gui()

def start_Pact_QXDM():
    Quts_conroller.start_app(Quts_conroller.PCAT_PATH)
    Quts_conroller.start_app(Quts_conroller.QXDM_PATH)

def stop_all_tools_Framework():
    stop_all()
    subprocess.run("taskkill /IM PCATApp.exe /F", shell=True)
    subprocess.run("taskkill /IM QXDM.exe /F", shell=True)
    
if __name__ == "__main__":
    run_app()
