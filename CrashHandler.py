import json
import os
from pathlib import Path
import subprocess

crash_forecast_path = r"C:\QSTAF\crash_forecast.4.4"
LOG_DIR  = Path(r"C:\QSTAF\CTM_logs")
CONFIG_FILE  = os.path.join(LOG_DIR, "app_config.json")
exe_name = "crash_forecast.exe"
magic_number = "eJx1j8FuwyAQRP+F8x4wEOLkVywLYWfrIhnsAq4SRfn37jpR2ks5MW9HM7t3UW8rFnG+iy2kqpU4dxJMD7u0hmQDLcnx02cSChoSw7LM6BNpTfoBotzisMx7zLhkvGxx5f/gC4qzMsZqLY/GgLj46nmCmdM6MYeEaYsCVGtA9tCJUn2uroaIBE+W+zrxEWZMnpFuFCg47NaIpfiJoWWoDpbp6rOnQKskSGgUI79dXSwTQf3HWMfBPUPV0RrizY5DcXgdca1hSTxqJeiejg6Ru3jpr9Htwn1jLuRypeaQJjafOL9R7R709PgcfKq/nhMt9vYsGP/J0tK0Lx+Vv6ZU//7SdbJ/0PsBBs+KUg=="
tester_name = "XYZ"
operator = "TMO"


def crash_forecast(crash_path: str):
    if crash_path!= "null":
        args = f'-p {crash_path} -m {magic_number} -t {tester_name} -o {operator} --publish true'
        cmd = (
        f'cmd.exe /K '
        f'cd /d {crash_forecast_path} && '
        f'{exe_name} {args}"'
    )
        subprocess.Popen(
        cmd,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    else:
        print("[INFO] No valid crash path provided.")

def load_json() -> dict:
    try:
        return json.loads(Path(CONFIG_FILE).read_text("utf-8"))
    except Exception as e:
        print("App_json is has no data: %s", e)
        return {}

def get_crash_path():
    cfg =load_json()
    normal_crash_path =cfg.get("previous_normalcrash_dir", "null")
    rdkb_crash_path = cfg.get("previous_rdkbcrash_dir", "null")

    # Choose which to run, or run both if needed
    crash_forecast(normal_crash_path)
    crash_forecast(rdkb_crash_path)  # Uncomment if needed


if __name__ == "__main__":
    get_crash_path()
