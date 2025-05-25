import datetime
from logging import root
import time
from tkinter import messagebox
import ctypes
import sys
from idna import check_label
import Kill_process, Start_testCase,Track_process,updater


CMD_DIR_Control = r"C:\QSTAF\QSTAFpy\bin\Control_laptop\Windows"
BAT_FILE_Control = "Run_framework_contol.bat"  
CMD_DIR_traffic = r"C:\QSTAF\QSTAFpy\bin\Traffic_laptop\Windows"
BAT_FILE_traffic = "Run_framework_Traffic.bat"
CMD_DIR_AWS= r"C:\QSTAF\QSTAFpy\bin"
BAT_FILE_AWS= "aws_s3_uploder.bat"

updater.main_update_check()
def ensure_admin():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
    except Exception as e:
        print(f"Admin check failed: {e}")
        sys.exit(1)

def start_control():
    try:
        Start_testCase.start_tests(CMD_DIR_Control,BAT_FILE_Control)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def start_traffic():
    try:
        Start_testCase.start_tests(CMD_DIR_traffic,BAT_FILE_traffic)
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
    messagebox.showinfo("Info", msg)

def run_s3_uploader():
    try:
        Start_testCase.start_tests(CMD_DIR_AWS,BAT_FILE_AWS)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def update_clock():
    now = datetime.now().strftime("%H:%M:%S")
    check_label.config(text=now)
    root.after(1000, update_clock)

def restart_quts_pcat_qxdm():
    def show_status(msg):
        print(msg)  # Or use a label update/messagebox as needed
    Track_process.restart_quts_pcat_qxdm(callback=show_status)


