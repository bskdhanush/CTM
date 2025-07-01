import subprocess
import os

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




