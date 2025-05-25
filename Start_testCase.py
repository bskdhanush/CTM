import subprocess
import os

def start_tests(CMD_DIR,BAT_FILE):
    if not os.path.exists(os.path.join(CMD_DIR, BAT_FILE)):
        raise FileNotFoundError(f"Batch file not found in: {CMD_DIR}")
    
    subprocess.Popen(
        f'cmd.exe /K "cd /d {CMD_DIR} && {BAT_FILE}"',
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )



