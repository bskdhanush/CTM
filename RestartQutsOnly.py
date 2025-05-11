import ctypes
import subprocess
import sys
import time

SERVICE_NAME = "QUTS"

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

def is_service_running(service_name):
    result = subprocess.run(
        ["sc", "query", service_name],
        capture_output=True,
        text=True,
        shell=True
    )
    return "RUNNING" in result.stdout

def smart_restart_quts(callback=None):
    if is_service_running(SERVICE_NAME):
        if callback:
            callback("Service is running. Restarting QUTS...")
        try:
            subprocess.run(["sc", "stop", SERVICE_NAME], check=True, shell=True)
            time.sleep(10)
            subprocess.run(["sc", "start", SERVICE_NAME], check=True, shell=True)
            if callback:
                callback("QUTS service restarted successfully.")
        except subprocess.CalledProcessError:
            if callback:
                callback("Failed to restart QUTS service.")
    else:
        try:
            subprocess.run(["sc", "start", SERVICE_NAME], check=True, shell=True)
            if callback:
                callback("QUTS service was not running. Started successfully.")
        except subprocess.CalledProcessError:
            if callback:
                callback("Failed to start QUTS service.")
import ctypes
import subprocess
import sys
import time

SERVICE_NAME = "QUTS"

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

def is_service_running(service_name):
    result = subprocess.run(
        ["sc", "query", service_name],
        capture_output=True,
        text=True,
        shell=True
    )
    return "RUNNING" in result.stdout

def smart_restart_quts(callback=None):
    if is_service_running(SERVICE_NAME):
        if callback:
            callback("Service is running. Restarting QUTS...")
        try:
            subprocess.run(["sc", "stop", SERVICE_NAME], check=True, shell=True)
            time.sleep(10)
            subprocess.run(["sc", "start", SERVICE_NAME], check=True, shell=True)
            if callback:
                callback("QUTS service restarted successfully.")
        except subprocess.CalledProcessError:
            if callback:
                callback("Failed to restart QUTS service.")
    else:
        try:
            subprocess.run(["sc", "start", SERVICE_NAME], check=True, shell=True)
            if callback:
                callback("QUTS service was not running. Started successfully.")
        except subprocess.CalledProcessError:
            if callback:
                callback("Failed to start QUTS service.")
