# ─── Check_updates.py (with batch-helper launching EXE in a new terminal) ─────────

import glob
import os
import sys
import subprocess
import requests
import logging
import time
import shutil
from datetime import datetime
from packaging.version import parse as parse_version

# ── CONFIGURATION ────────────────────────────────────────────────────────────────

GITHUB_USER   = "bskdhanush"
GITHUB_REPO   = "QC_stuff"

# You should supply a valid PAT in your environment; do NOT hard-code in production.
GITHUB_PAT    = os.getenv("GITHUB_PAT") or "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"

# Bump this on each new build/exe you generate:
LOCAL_VERSION = "1.2.5"

DOWNLOAD_DIR  = r"C:\QSTAF"
EXE_NAME      = "QSTAF_Tool.exe"
EXE_PATH      = os.path.join(DOWNLOAD_DIR, EXE_NAME)
EXE_BACKUP    = os.path.join(DOWNLOAD_DIR, "QSTAF_Tool.exe.backup")

# Log file location (adjust as desired):
LOG_DIR      = os.path.join(DOWNLOAD_DIR, "logs")
LOG_FILENAME = os.path.join(LOG_DIR, "check_updates.log")


# ── SET UP LOGGING ──────────────────────────────────────────────────────────────

# Ensure directories exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR,       exist_ok=True)

logger = logging.getLogger("CheckUpdates")
logger.setLevel(logging.INFO)
logger.handlers.clear()

file_handler = logging.FileHandler(LOG_FILENAME, mode="a", encoding="utf-8")
file_fmt = logging.Formatter(
    "%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_fmt)
logger.addHandler(file_handler)

def log_info(msg: str):
    print(msg)
    logger.info(msg)

def log_warn(msg: str):
    print(msg)
    logger.warning(msg)

def log_error(msg: str):
    print(msg, file=sys.stderr)
    logger.error(msg)


# ── SESSION & API HELPERS ────────────────────────────────────────────────────────

def get_session():
    """
    Return a requests.Session that includes the GitHub PAT header.
    Raises EnvironmentError if the PAT is missing.
    """
    if not GITHUB_PAT:
        raise EnvironmentError("GITHUB_PAT not set. Cannot access private repository.")
    sess = requests.Session()
    sess.headers.update({
        "Authorization": f"Bearer {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    })
    return sess

def fetch_latest_release_data():
    """
    Hits GitHub's /repos/:owner/:repo/releases/latest endpoint.
    Returns the JSON payload or raises HTTPError.
    """
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
    sess = get_session()
    r = sess.get(api_url, timeout=10)
    r.raise_for_status()
    return r.json()

def find_latest_exe_asset(release_data: dict) -> (str, str): # type: ignore
    """
    Scan release_data["assets"] for the newest .exe whose name 
    starts with "QSTAF_Tool" (case‐insensitive). Returns (asset_url, asset_name).
    """
    assets = release_data.get("assets", [])
    exe_assets = [
        a for a in assets
        if a.get("name", "").lower().startswith("qstaf_tool")
           and a.get("name", "").lower().endswith(".exe")
    ]
    if not exe_assets:
        raise RuntimeError("No .exe asset named like 'QSTAF_Tool*.exe' found in latest release.")

    def parse_iso(ts: str) -> datetime:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")

    # Sort by created_at descending
    exe_assets.sort(
        key=lambda a: parse_iso(a.get("created_at", "1970-01-01T00:00:00Z")),
        reverse=True
    )
    chosen = exe_assets[0]
    return chosen["url"], chosen["name"]

def download_asset_to_temp(asset_api_url: str, asset_name: str) -> str:
    sess = get_session()
    sess.headers.update({"Accept": "application/octet-stream"})
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    temp_filename = asset_name + ".tmp"
    temp_path     = os.path.join(DOWNLOAD_DIR, temp_filename)

    log_info(f"Downloading asset to temp file: {temp_path}")
    with sess.get(asset_api_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(temp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
    log_info(f"Finished download of {temp_path}")
    return temp_path


def create_backup(source_path: str, backup_path: str) -> bool:
    """
    Copy source_path → backup_path. Return True on success or if source didn’t exist.
    """
    if not os.path.isfile(source_path):
        return True
    try:
        shutil.copy2(source_path, backup_path)
        log_info(f"Created backup: {backup_path}")
        return True
    except Exception as e:
        log_warn(f"Failed to back up {source_path} → {backup_path}: {e}")
        return False

def restore_from_backup(backup_path: str, target_path: str) -> bool:
    """
    Copy backup_path → target_path. Return True if successful.
    """
    if not os.path.isfile(backup_path):
        log_error(f"Backup file not found: {backup_path}")
        return False
    try:
        shutil.copy2(backup_path, target_path)
        log_info(f"Restored from backup: {target_path}")
        return True
    except Exception as e:
        log_error(f"Failed to restore backup {backup_path} → {target_path}: {e}")
        return False

def create_update_script(temp_path: str, target_path: str, backup_path: str) -> str:
    """
    Generate a self-deleting batch file (update_helper.bat) under DOWNLOAD_DIR that:
     1) Waits for the updater-EXE to close.
     2) Deletes/moves the old EXE into place.
     3) Waits 5 seconds, then opens a new terminal and runs the new EXE with --skip-updates.
     4) Deletes itself (silently, even if %~f0 is missing).

    Returns the absolute path of the created .bat.
    """
    batch_script_path = os.path.join(DOWNLOAD_DIR, "update_helper.bat")
    log_file_path     = os.path.join(LOG_DIR, "update_helper.log")

    # Convert forward slashes to backslashes for Windows paths
    temp_clean    = temp_path.replace("/", "\\")
    target_clean  = target_path.replace("/", "\\")
    backup_clean  = backup_path.replace("/", "\\") if backup_path else ""
    log_clean     = log_file_path.replace("/", "\\")

    # Build the batch-file content
    batch_content = f'''@echo off
rem ─────────────────────────────────────────────────────────────────────────────
rem  Ensure we run from the script’s own folder so that %~f0 is valid:
cd /d "%~dp0"

rem Create or append to a log for debugging:
echo Update Helper Script Started at %date% %time% > "{log_clean}"
echo Waiting for updater to close... >> "{log_clean}"
timeout /t 5 /nobreak >nul

echo Attempting to replace EXE file: {target_clean} >> "{log_clean}"
echo Temp file found: {temp_clean} >> "{log_clean}"

rem Kill any running instance of the old EXE (if still hanging around)
taskkill /f /im QSTAF_Tool.exe 2>nul
timeout /t 2 /nobreak >nul

set MAX_ATTEMPTS=15
set ATTEMPT=1

:RETRY
echo Attempt !ATTEMPT! of !MAX_ATTEMPTS! >> "{log_clean}"
if exist "{target_clean}" (
    del /f /q "{target_clean}" 2>>"{log_clean}"
    if exist "{target_clean}" (
        echo File still in use, trying rename... >> "{log_clean}"
        ren "{target_clean}" "QSTAF_Tool.exe.locked.!ATTEMPT!" 2>>"{log_clean}"
        if not exist "{target_clean}" goto MOVE_NEW
        timeout /t 3 /nobreak >nul
        set /a ATTEMPT+=1
        if !ATTEMPT! leq !MAX_ATTEMPTS! goto RETRY
        echo FAILED to remove/rename after !MAX_ATTEMPTS! attempts >> "{log_clean}"
        goto RESTORE_BACKUP
    )
)

:MOVE_NEW
echo Moving new file into place... >> "{log_clean}"
move "{temp_clean}" "{target_clean}" 2>>"{log_clean}"
if errorlevel 1 (
    echo ERROR: Failed to move new file >> "{log_clean}"
    goto RESTORE_BACKUP
)

if exist "{target_clean}" (
    echo SUCCESS: File replacement completed! >> "{log_clean}"
    goto Update_message
) else (
    echo ERROR: Moved file not found at {target_clean} >> "{log_clean}"
    goto RESTORE_BACKUP
)

:RESTORE_BACKUP
if not "{backup_clean}"=="" (
    if exist "{backup_clean}" (
        echo Restoring from backup... >> "{log_clean}"
        copy "{backup_clean}" "{target_clean}" >nul 2>>"{log_clean}"
        if exist "{target_clean}" (
            echo Backup restored successfully >> "{log_clean}"
        ) else (
            echo ERROR: Failed to restore backup >> "{log_clean}"
        )
    ) else (
        echo ERROR: Backup not found: {backup_clean} >> "{log_clean}"
    )
) else (
    echo No backup available to restore. >> "{log_clean}"
)

:Update_message

rem Show a “Update is complete” pop-up using PowerShell
powershell -noprofile -windowstyle hidden -command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('Update is complete','Update Finished')"

echo Script completed at %date% %time% >> "{log_clean}"

rem Allow 2 seconds before self-delete
timeout /t 2 /nobreak >nul

rem Self-delete (silently)
del "%~f0" >nul 2>&1
'''

    # Write out the batch file
    with open(batch_script_path, "w", encoding="utf-8") as f:
        f.write(batch_content)

    log_info(f"Created update helper script: {batch_script_path}")
    return batch_script_path


def download_and_replace(asset_api_url: str, asset_name: str):
    r"""
    Always use the batch‑file helper to swap the running EXE.

    Steps
    -----
    1. Back up the existing EXE (if present).
    2. Download the new EXE to <DOWNLOAD_DIR>\<asset_name>.tmp.
    3. Generate update_helper.bat that:
          • waits for the updater to exit,
          • moves the new file into place,
          • shows “Update is complete”,
          • launches the fresh EXE in a new console,
          • self‑deletes.
    4. Launch the .bat in a detached console and quit Python so the file
       lock on the old EXE is released.
    """
    backup_created = False
    temp_path      = None

    try:
        # 1) optional backup
        if os.path.isfile(EXE_PATH):
            backup_created = create_backup(EXE_PATH, EXE_BACKUP)

        # 2) download to temp
        temp_path = download_asset_to_temp(asset_api_url, asset_name)

        # 3) batch helper
        batch_script = create_update_script(
            temp_path,
            EXE_PATH,
            EXE_BACKUP if backup_created else ""
        )

        log_info("Launching batch helper in a detached console …")
        subprocess.Popen(
            ["cmd.exe", "/c", "start", "", batch_script],
            shell=False
        )

        # 4) give the .bat a moment to start, then exit updater
        time.sleep(1)
        log_info("Updater exiting so batch script can replace the EXE.")
        sys.exit(0)

    except Exception as exc:
        log_error(f"download_and_replace failed: {exc}")

        # tidy up temp
        if temp_path and os.path.isfile(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

        # try to put the backup back if we nuked the original
        if backup_created and not os.path.isfile(EXE_PATH):
            restore_from_backup(EXE_BACKUP, EXE_PATH)

        raise


def launch_updated_exe():
    """
    Look for the newest “QSTAF_Tool*.exe” inside DOWNLOAD_DIR and run it with
    --skip-updates.  Falls back to the backup if no matching EXE is found.
    """
    # 1) gather candidate EXEs
    pattern     = os.path.join(DOWNLOAD_DIR, "QSTAF_Tool*.exe")
    candidates  = glob.glob(pattern)

    if not candidates:
        log_warn("No QSTAF_Tool*.exe found; attempting to restore from backup.")
        if not restore_from_backup(EXE_BACKUP, EXE_PATH):
            log_error("No executable available to launch. Aborting.")
            sys.exit(1)
        candidates = [EXE_PATH]

    # 2) pick the most‑recently modified one
    exe_to_run = max(candidates, key=os.path.getmtime)

    log_info(f"Launching updated EXE: {exe_to_run} --skip-updates")
    try:
        subprocess.Popen([exe_to_run, "--skip-updates"], shell=False)
        sys.exit(0)
    except Exception as e:
        log_error(f"Failed to launch {exe_to_run}: {e}")
        sys.exit(1)



def check_and_update():
    """
    Check GitHub for a newer tag vs. LOCAL_VERSION. If newer:
    - Download & replace (directly or via batch helper). Returns True if replaced.
    Otherwise returns False.
    """
    try:
        log_info("Checking for updates on GitHub...")
        data = fetch_latest_release_data()
        raw_tag = data.get("tag_name", "")
        latest_tag = raw_tag.lstrip("v")

        log_info(f"Latest GitHub release: {latest_tag} (local: {LOCAL_VERSION})")
        if parse_version(latest_tag) > parse_version(LOCAL_VERSION):
            log_info("Newer version detected. Beginning download & replace...")
            asset_api_url, asset_name = find_latest_exe_asset(data)
            download_and_replace(asset_api_url, asset_name)
            return True
        else:
            log_info("Already up to date.")
            return False
    except Exception as exc:
        log_warn(f"Update check failed: {exc!r}")
        return False


# ── MAIN ROUTINE ─────────────────────────────────────────────────────────────────

def main():
    try:
        log_info("Launching updater...")
        data = fetch_latest_release_data()
        raw_tag = data.get("tag_name", "")
        latest_tag = raw_tag.lstrip("v")

        log_info(f"Latest GitHub release: {latest_tag} (local: {LOCAL_VERSION})")
        if parse_version(latest_tag) > parse_version(LOCAL_VERSION):
            log_info("Newer version detected. Downloading & replacing...")
            asset_api_url, asset_name = find_latest_exe_asset(data)
            download_and_replace(asset_api_url, asset_name)
        else:
            log_info("Already up to date. Launching existing EXE.")
            launch_updated_exe()
    except Exception as exc:
        log_warn(f"Update check failed: {exc!r}")
        launch_updated_exe()


if __name__ == "__main__":
    main()
