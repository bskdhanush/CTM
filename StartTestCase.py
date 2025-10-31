import os, subprocess
import time
import GUI
import MainController
import CopyCsv
from Threading import *

KEY = "****** Stop Main #"

def start_tests(CMD_DIR,BAT_FILE,WINDOW_TITLE):
    if not os.path.exists(os.path.join(CMD_DIR, BAT_FILE)):
        raise FileNotFoundError(f"Batch file not found in: {CMD_DIR}")
    
    cmd = (
        f'cmd.exe /K '
        f'"title {WINDOW_TITLE} && '
        f'cd /d {CMD_DIR} && '
        f'{BAT_FILE}"'
    )
    subprocess.Popen(
        cmd,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )



def start_bat_and_watch_stdout(cmd_dir, bat_file,callback):
    proc = subprocess.Popen(
        ["cmd.exe", "/C", "call", bat_file],
        cwd=cmd_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,  # no extra console
    )
    def reader():
        assert proc.stdout
        for line in proc.stdout:
            if KEY in line:
                time.sleep(10)
                
                CopyCsv.get_speedtest_csv_list()
                MainController.get_all_speedtest_results()

                if callback:
                    GUI.root.after(0, callback) # type: ignore

                proc.terminate()
             
    start_thread(reader,"Speed test reults thread" ,daemon=True)
