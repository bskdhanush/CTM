import os
import psutil
import threading
import time
import requests
import json
import datetime
import subprocess
import platform

# Paths
CONTROL_PATH = r"C:\QSTAF\QSTAFpy\bin\Control_laptop\Windows"
CONTROL_BAT = os.path.join(CONTROL_PATH, "Run_framework.bat")
TRAFFIC_PATH = r"C:\QSTAF\QSTAFpy\bin\Traffic_laptop\Windows"
TRAFFIC_BAT = os.path.join(TRAFFIC_PATH, "Run_framework.bat")
AWS_S3_PATH = r"C:\QSTAF\QSTAFpy\bin"
AWS_S3_BAT = os.path.join(AWS_S3_PATH, "aws_s3_uploder")
CONFIG_PATH = r"C:\QSTAF"
CONFIG_FILE = os.path.join(CONFIG_PATH, "app_config.json")

# Ensure config directory exists
os.makedirs(CONFIG_PATH, exist_ok=True)

def save_settings():
    config = {"aws_scheduler_enabled": True}
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_settings():
    default_config = {"aws_scheduler_enabled": False}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return default_config
    return default_config

def run_bat_as_admin(bat_path, working_dir):
    try:
        vbs_content = f'''
Set objShell = CreateObject("WScript.Shell")
Set UAC = CreateObject("Shell.Application")
objShell.CurrentDirectory = "{working_dir}"
UAC.ShellExecute "cmd.exe", "/k cd /d {working_dir} & {os.path.basename(bat_path)}", "", "runas", 1
'''
        temp_vbs = os.path.join(os.environ['TEMP'], 'run_as_admin.vbs')
        with open(temp_vbs, 'w') as f:
            f.write(vbs_content)
        os.system(f'wscript.exe "{temp_vbs}"')
        os.remove(temp_vbs)
    except Exception as e:
        print(f"Failed to run the script: {e}")

def run_control_framework():
    run_bat_as_admin(CONTROL_BAT, CONTROL_PATH)

def run_traffic_framework():
    run_bat_as_admin(TRAFFIC_BAT, TRAFFIC_PATH)

def run_aws_s3_uploader(new_terminal=True, as_admin=False):
    if new_terminal:
        if platform.system() == "Windows":
            cmd = f'start cmd.exe /k "{AWS_S3_BAT}"'
            subprocess.run(cmd, cwd=AWS_S3_PATH, shell=True)
        # Add macOS and Linux support here if needed
    else:
        if as_admin:
            run_bat_as_admin(AWS_S3_BAT, AWS_S3_PATH)
        else:
            subprocess.run([AWS_S3_BAT], cwd=AWS_S3_PATH, shell=True)

def run_both_frameworks():
    def execute():
        run_bat_as_admin(CONTROL_BAT, CONTROL_PATH)
        time.sleep(2.5)
        run_bat_as_admin(TRAFFIC_BAT, TRAFFIC_PATH)
    threading.Thread(target=execute, daemon=True).start()

def kill_framework_processes(framework_type="all"):
    from Track_process import close_all_chrome_tabs

    if framework_type in ["traffic", "all"]:
        close_all_chrome_tabs(close_chrome=True)

    target_processes = ['python.exe', 'cmd.exe', 'java.exe', 'conhost.exe']
    search_terms = []
    if framework_type in ["control", "all"]:
        search_terms.append("control_laptop")
    if framework_type in ["traffic", "all"]:
        search_terms.append("traffic_laptop")
    search_terms.append("qstaf")

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in target_processes:
                cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                if any(term in cmdline for term in search_terms):
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def kill_control_processes():
    kill_framework_processes("control")

def kill_traffic_processes():
    kill_framework_processes("traffic")

def kill_all_processes():
    kill_framework_processes("all")
