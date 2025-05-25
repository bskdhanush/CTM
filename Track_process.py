import subprocess
import time
import os

SERVICE_NAME = "QUTS"
PCAT_PATH = r"C:\Program Files (x86)\Qualcomm\PCAT\bin\PCATApp.exe"
QXDM_PATH = r"C:\Program Files\Qualcomm\QXDM5\QXDM.exe"


def is_service_running(service_name):
    result = subprocess.run(["sc", "query", service_name], capture_output=True, text=True, shell=True)
    return "RUNNING" in result.stdout

def start_quts():
    subprocess.run(["sc", "start", SERVICE_NAME], check=True, shell=True)

def stop_quts():
    subprocess.run(["sc", "stop", SERVICE_NAME], check=True, shell=True)

def start_app(path):
    if os.path.exists(path):
        subprocess.Popen(path)
        return True
    return False

def is_process_running(name):
    result = subprocess.run(f'tasklist /FI "IMAGENAME eq {name}"', capture_output=True, text=True, shell=True)
    return name.lower() in result.stdout.lower()

def restart_quts():
    stop_quts()
    time.sleep(5)
    start_quts()

def restart_quts_pcat_qxdm(callback=None):
    quts_running = is_service_running(SERVICE_NAME)
    pcat_running = is_process_running("PCATApp.exe")
    qxdm_running = is_process_running("QXDM.exe")

    if quts_running and pcat_running and qxdm_running:
        # Stop all in reverse order
        if callback: callback("Stopping all apps...")
        subprocess.run("taskkill /IM PCATApp.exe /F", shell=True)
        subprocess.run("taskkill /IM QXDM.exe /F", shell=True)
        stop_quts()
        time.sleep(5)
        # Restart all
        if callback: callback("Restarting apps...")
        start_quts()
        time.sleep(10)
        start_app(PCAT_PATH)
        time.sleep(3)
        start_app(QXDM_PATH)
        if callback: callback("All apps restarted.")
    else:
        # Start/restart only those that were running, then start remaining
        if quts_running:
            stop_quts()
            time.sleep(5)
            start_quts()
        elif not quts_running:
            start_quts()
        time.sleep(10)

        if pcat_running:
            subprocess.run("taskkill /IM PCATApp.exe /F", shell=True)
            time.sleep(2)
            start_app(PCAT_PATH)
        elif not pcat_running:
            start_app(PCAT_PATH)
        time.sleep(3)

        if qxdm_running:
            subprocess.run("taskkill /IM QXDM.exe /F", shell=True)
            time.sleep(2)
            start_app(QXDM_PATH)
        elif not qxdm_running:
            start_app(QXDM_PATH)

        if callback:
            callback("Apps checked and started/restarted as needed.")
