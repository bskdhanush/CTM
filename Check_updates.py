# ─── Check_updates.py (with file logging and improved error handling) ─────────

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

# Make sure you have set your PAT in the environment:
#   setx GITHUB_PAT "your_token_here"
# or, if you absolutely must, you can hard‐code it (not recommended):
GITHUB_PAT    = os.getenv("GITHUB_PAT") or "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"

# The "local" version embedded in this build.  Bump this on each new build.
LOCAL_VERSION = "1.2.1"

# Where on disk we keep/download the EXE and write the log:
DOWNLOAD_DIR  = r"C:\QSTAF"
EXE_NAME      = "QSTAF_Tool.exe"
EXE_PATH      = os.path.join(DOWNLOAD_DIR, EXE_NAME)
EXE_BACKUP    = os.path.join(DOWNLOAD_DIR, "QSTAF_Tool.exe.backup")

# Log file (in the same DOWNLOAD_DIR):
LOG_FILENAME  = os.path.join("D:\QC_testing\GUI\Quts_tool\logs", "check_updates.log")


# ── SET UP LOGGING ──────────────────────────────────────────────────────────────

# Ensure the download directory (and thus the log folder) exists:
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILENAME), exist_ok=True)

# Create a logger that writes to both console (via print) and file:
logger = logging.getLogger("CheckUpdates")
logger.setLevel(logging.INFO)

# Clear existing handlers to avoid duplicates
logger.handlers.clear()

# FileHandler: append to LOG_FILENAME, write level+message+timestamp
file_handler = logging.FileHandler(LOG_FILENAME, mode="a", encoding="utf-8")
file_fmt = logging.Formatter(
    "%(asctime)s  [%(levelname)s]  %(message)s", 
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_fmt)
logger.addHandler(file_handler)

# A small helper so that logger.info(...) and print(...) stay in sync:
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
    Create a requests.Session that always sends the GitHub PAT.
    Raises EnvironmentError if GITHUB_PAT is missing.
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
    Calls GitHub's /repos/:owner/:repo/releases/latest endpoint and returns
    the JSON dict for the latest release. Raises HTTPError on any failure.
    """
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
    sess = get_session()
    resp = sess.get(api_url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def find_latest_exe_asset(release_data: dict) -> (str, str):
    """
    Inspect release_data["assets"] for the newest .exe whose name
    starts with "QSTAF_Tool" (case‐insensitive).  Returns a tuple:
       (asset_api_url, asset_filename)

    - asset_api_url is something like:
      "https://api.github.com/repos/bskdhanush/QC_stuff/releases/assets/1234567"
    - If no matching .exe is found, raises RuntimeError.
    """
    assets = release_data.get("assets", [])
    exe_assets = [
        a for a in assets
        if a.get("name", "").lower().startswith("qstaf_tool") and
           a.get("name", "").lower().endswith(".exe")
    ]

    if not exe_assets:
        raise RuntimeError("No .exe asset named like 'QSTAF_Tool*.exe' found on latest release.")

    # If there are multiple matches, pick the one with the latest creation timestamp:
    def parse_iso(ts: str) -> datetime:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")

    exe_assets.sort(
        key=lambda a: parse_iso(a.get("created_at", "1970-01-01T00:00:00Z")),
        reverse=True
    )
    chosen = exe_assets[0]
    asset_api_url = chosen.get("url")    # e.g. "https://api.github.com/repos/.../releases/assets/1234567"
    asset_name    = chosen.get("name")   # e.g. "QSTAF_Tool_v1.2.2.exe"
    return asset_api_url, asset_name


def download_asset_to_temp(asset_api_url: str, asset_name: str) -> str:
    r"""
    Download the .exe asset (via the GitHub asset‐API URL) into a temp file
    under C:\QSTAF\ and return the path to that temporary file.

    We set a streaming GET with header Accept: application/octet-stream so that
    GitHub returns the raw binary.  The temp file is named:
        C:\QSTAF\{asset_name}.tmp

    If anything fails (network, 404, missing PAT, etc.), this will raise HTTPError.
    """
    sess = get_session()
    sess.headers.update({"Accept": "application/octet-stream"})

    # Ensure download folder exists (already done at top, but just in case):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    temp_filename = asset_name + ".tmp"  # e.g. "QSTAF_Tool_v1.2.2.exe.tmp"
    temp_path     = os.path.join(DOWNLOAD_DIR, temp_filename)

    log_info(f"Downloading asset to temp file: {temp_path}")
    with sess.get(asset_api_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(temp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    log_info(f"Finished download: {temp_path}")
    return temp_path


def safe_remove_file(file_path: str, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
    """
    Safely remove a file with retry logic to handle permission errors.
    Returns True if successful, False if failed after all retries.
    """
    if not os.path.isfile(file_path):
        return True
    
    for attempt in range(max_retries):
        try:
            os.remove(file_path)
            log_info(f"Successfully removed: {file_path}")
            return True
        except PermissionError as pe:
            log_warn(f"Permission denied removing {file_path} (attempt {attempt + 1}/{max_retries}): {pe}")
            if attempt < max_retries - 1:
                log_info(f"Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
            else:
                log_error(f"Failed to remove {file_path} after {max_retries} attempts")
                return False
        except OSError as oe:
            log_error(f"OS error removing {file_path}: {oe}")
            return False
    
    return False


def create_backup(source_path: str, backup_path: str) -> bool:
    """
    Create a backup of the current EXE file.
    Returns True if successful, False if failed.
    """
    if not os.path.isfile(source_path):
        return True  # Nothing to backup
    
    try:
        shutil.copy2(source_path, backup_path)
        log_info(f"Created backup: {backup_path}")
        return True
    except Exception as e:
        log_warn(f"Failed to create backup: {e}")
        return False


def restore_from_backup(backup_path: str, target_path: str) -> bool:
    """
    Restore from backup if the original file is missing or corrupted.
    Returns True if successful, False if failed.
    """
    if not os.path.isfile(backup_path):
        log_error(f"Backup file not found: {backup_path}")
        return False
    
    try:
        shutil.copy2(backup_path, target_path)
        log_info(f"Restored from backup: {target_path}")
        return True
    except Exception as e:
        log_error(f"Failed to restore from backup: {e}")
        return False


def create_update_script(temp_path: str, target_path: str, backup_path: str) -> str:
    """
    Create a batch script that will handle the file replacement after this process exits.
    Returns the path to the created batch file.
    """
    batch_script_path = os.path.join(DOWNLOAD_DIR, "update_helper.bat")
    log_file_path = os.path.join(DOWNLOAD_DIR, "update_helper.log")
    
    # Convert paths to use forward slashes to avoid batch script issues
    temp_path_clean = temp_path.replace('/', '\\')
    target_path_clean = target_path.replace('/', '\\')
    backup_path_clean = backup_path.replace('/', '\\') if backup_path else ""
    log_file_clean = log_file_path.replace('/', '\\')
    
    batch_content = f'''@echo off
setlocal enabledelayedexpansion

rem Create log file
echo Update Helper Script Started at %date% %time% > "{log_file_clean}"

echo Waiting for updater to close...
echo Waiting for updater to close... >> "{log_file_clean}"
timeout /t 5 /nobreak >nul

echo Attempting to replace EXE file: {target_path_clean}
echo Attempting to replace EXE file: {target_path_clean} >> "{log_file_clean}"

rem Check if temp file exists
if not exist "{temp_path_clean}" (
    echo ERROR: Temp file not found: {temp_path_clean}
    echo ERROR: Temp file not found: {temp_path_clean} >> "{log_file_clean}"
    goto RESTORE_BACKUP
)

echo Temp file found: {temp_path_clean}
echo Temp file found: {temp_path_clean} >> "{log_file_clean}"

rem Try to kill any processes that might be locking the file
taskkill /f /im QSTAF_Tool.exe 2>nul
timeout /t 2 /nobreak >nul

set MAX_ATTEMPTS=15
set ATTEMPT=1

:RETRY
echo Attempt !ATTEMPT! of !MAX_ATTEMPTS!
echo Attempt !ATTEMPT! of !MAX_ATTEMPTS! >> "{log_file_clean}"

if exist "{target_path_clean}" (
    rem Try to delete the old file
    del /f /q "{target_path_clean}" 2>nul
    if exist "{target_path_clean}" (
        echo Attempt !ATTEMPT!: File still in use, trying alternate methods...
        echo Attempt !ATTEMPT!: File still in use, trying alternate methods... >> "{log_file_clean}"
        
        rem Try to rename old file first
        ren "{target_path_clean}" "QSTAF_Tool.exe.locked.!ATTEMPT!" 2>nul
        if not exist "{target_path_clean}" (
            echo Successfully renamed locked file
            echo Successfully renamed locked file >> "{log_file_clean}"
            goto MOVE_NEW_FILE
        )
        
        rem If rename failed, wait and retry
        timeout /t 3 /nobreak >nul
        set /a ATTEMPT+=1
        if !ATTEMPT! leq !MAX_ATTEMPTS! goto RETRY
        
        echo FAILED: Could not remove or rename old file after !MAX_ATTEMPTS! attempts
        echo FAILED: Could not remove or rename old file after !MAX_ATTEMPTS! attempts >> "{log_file_clean}"
        goto RESTORE_BACKUP
    )
)

:MOVE_NEW_FILE
echo Moving new file into place...
echo Moving new file into place... >> "{log_file_clean}"

move "{temp_path_clean}" "{target_path_clean}" 2>>"{log_file_clean}"
if errorlevel 1 (
    echo ERROR: Failed to move new file
    echo ERROR: Failed to move new file >> "{log_file_clean}"
    goto RESTORE_BACKUP
)

if exist "{target_path_clean}" (
    echo SUCCESS: File replacement completed!
    echo SUCCESS: File replacement completed! >> "{log_file_clean}"
    goto LAUNCH_APP
) else (
    echo ERROR: New file not found after move operation
    echo ERROR: New file not found after move operation >> "{log_file_clean}"
    goto RESTORE_BACKUP
)

:RESTORE_BACKUP
if "{backup_path_clean}" neq "" (
    if exist "{backup_path_clean}" (
        echo Restoring from backup...
        echo Restoring from backup... >> "{log_file_clean}"
        copy "{backup_path_clean}" "{target_path_clean}" >nul 2>>"{log_file_clean}"
        if exist "{target_path_clean}" (
            echo Backup restored successfully
            echo Backup restored successfully >> "{log_file_clean}"
        ) else (
            echo ERROR: Failed to restore backup
            echo ERROR: Failed to restore backup >> "{log_file_clean}"
        )
    ) else (
        echo ERROR: Backup file not found: {backup_path_clean}
        echo ERROR: Backup file not found: {backup_path_clean} >> "{log_file_clean}"
    )
) else (
    echo No backup available
    echo No backup available >> "{log_file_clean}"
)

:LAUNCH_APP
if exist "{target_path_clean}" (
    echo Starting updated application...
    echo Starting updated application... >> "{log_file_clean}"
    start "" "{target_path_clean}" --skip-updates
    echo Application launched
    echo Application launched >> "{log_file_clean}"
) else (
    echo ERROR: Cannot launch - EXE file not found
    echo ERROR: Cannot launch - EXE file not found >> "{log_file_clean}"
    pause
)

echo Script completed at %date% %time%
echo Script completed at %date% %time% >> "{log_file_clean}"

rem Clean up (delete this script)
timeout /t 2 /nobreak >nul
del "%~f0" 2>nul
'''
    
    try:
        with open(batch_script_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        log_info(f"Created update helper script: {batch_script_path}")
        
        # Verify the batch file was created and has content
        if os.path.isfile(batch_script_path):
            file_size = os.path.getsize(batch_script_path)
            log_info(f"Batch file created successfully, size: {file_size} bytes")
        else:
            raise RuntimeError("Batch file was not created")
            
        return batch_script_path
    except Exception as e:
        log_error(f"Failed to create update helper script: {e}")
        raise


def download_and_replace(asset_api_url: str, asset_name: str):
    r"""
    New strategy to handle locked files:
    1) Create a backup of the current EXE
    2) Download the new EXE to a temp file
    3) Create a batch script to handle the replacement after this process exits
    4) Launch the batch script and exit immediately
    
    This avoids the permission issue by letting the batch script handle the replacement
    after the current process (which might be locking the file) has exited.
    """
    backup_created = False
    temp_path = None
    
    try:
        # (A) Create backup of current EXE
        if os.path.isfile(EXE_PATH):
            backup_created = create_backup(EXE_PATH, EXE_BACKUP)
        
        # (B) Download into a ".tmp" file
        temp_path = download_asset_to_temp(asset_api_url, asset_name)

        # (C) Try direct replacement first (in case file isn't locked)
        if os.path.isfile(EXE_PATH):
            log_info(f"Attempting direct replacement of {EXE_PATH}")
            if safe_remove_file(EXE_PATH, max_retries=2, retry_delay=1.0):
                # Direct replacement worked
                log_info(f"Renaming {temp_path} to {EXE_PATH}")
                os.replace(temp_path, EXE_PATH)
                log_info("Direct replacement successful.")
                
                # Clean up backup
                if backup_created and os.path.isfile(EXE_BACKUP):
                    safe_remove_file(EXE_BACKUP)
                return
        
        # (D) If direct replacement failed, use batch script approach
        log_info("Direct replacement failed, using batch script approach...")
        batch_script = create_update_script(temp_path, EXE_PATH, EXE_BACKUP if backup_created else "")
        
        log_info("Launching update helper script and exiting...")
        log_info(f"Batch script path: {batch_script}")
        log_info(f"Temp file path: {temp_path}")
        log_info(f"Target file path: {EXE_PATH}")
        
        # Verify files exist before launching batch script
        if not os.path.isfile(batch_script):
            raise RuntimeError(f"Batch script not found: {batch_script}")
        if not os.path.isfile(temp_path):
            raise RuntimeError(f"Temp file not found: {temp_path}")
            
        # Launch the batch script with elevated privileges if possible
        try:
            # Try to run with elevated privileges first
            subprocess.Popen(['powershell', '-Command', f'Start-Process -FilePath "{batch_script}" -Verb RunAs'], 
                           shell=False, creationflags=subprocess.CREATE_NEW_CONSOLE)
            log_info("Launched batch script with elevated privileges")
        except:
            # Fallback to normal execution
            subprocess.Popen([batch_script], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
            log_info("Launched batch script with normal privileges")
        
        # Give the batch script a moment to start
        time.sleep(1)
        log_info("Exiting Python process to allow file replacement...")
        sys.exit(0)
            
    except Exception as e:
        log_error(f"Error during download and replace: {e}")
        
        # Clean up temp file if it exists
        if temp_path and os.path.isfile(temp_path):
            try:
                os.remove(temp_path)
                log_info(f"Cleaned up temp file: {temp_path}")
            except:
                pass
        
        # Try to restore from backup if we have one and the main EXE is missing
        if backup_created and not os.path.isfile(EXE_PATH):
            log_info("Attempting to restore from backup...")
            restore_from_backup(EXE_BACKUP, EXE_PATH)
        
        raise  # Re-raise the exception


def launch_updated_exe():
    """
    Launch whatever is at EXE_PATH ("C:\QSTAF\QSTAF_Tool.exe") with
    the --skip-updates flag, then exit this script.  If EXE_PATH is missing,
    try to restore from backup, and if that fails, print an error and exit(1).
    """
    if not os.path.isfile(EXE_PATH):
        log_warn(f"EXE not found at {EXE_PATH}, attempting to restore from backup...")
        if not restore_from_backup(EXE_BACKUP, EXE_PATH):
            log_error(f"Cannot find or restore EXE at {EXE_PATH}. Aborting.")
            sys.exit(1)

    log_info(f"Launching updated EXE: {EXE_PATH} --skip-updates")
    try:
        # Using shell=False lets arguments be passed safely.
        subprocess.Popen([EXE_PATH, "--skip-updates"], shell=False)
        sys.exit(0)
    except Exception as e:
        log_error(f"Failed to launch EXE: {e}")
        sys.exit(1)


def check_and_update():
    """
    Standalone function to check for updates and download if needed.
    Returns True if update was downloaded, False if no update needed.
    """
    try:
        log_info("Checking for updates...")
        data = fetch_latest_release_data()
        raw_tag = data.get("tag_name", "")
        latest_tag = raw_tag.lstrip("v")

        log_info(f"Latest release on GitHub: {latest_tag} (local: {LOCAL_VERSION})")

        if parse_version(latest_tag) > parse_version(LOCAL_VERSION):
            log_info("Newer version detected. Downloading and replacing...")
            asset_api_url, asset_name = find_latest_exe_asset(data)
            download_and_replace(asset_api_url, asset_name)
            log_info(f"Replaced old EXE with version {latest_tag}.")
            # Note: download_and_replace handles launching the updated EXE via batch script
            # No need to call launch_updated_exe() here as the process will exit
            return True
        else:
            log_info("Already up to date.")
            return False

    except Exception as exc:
        log_warn(f"Update check failed: {exc!r}")
        return False


# ── MAIN ROUTINE ─────────────────────────────────────────────────────────────────

def main():
    """
    1) Fetch "latest release" JSON from GitHub.
    2) Compare its tag (without leading 'v') to LOCAL_VERSION.
    3) If GitHub's tag is newer, download & replace, then launch the new EXE.
       Otherwise, launch the existing EXE immediately.
    4) On ANY exception (network, 404, missing PAT, etc.), log a warning and
       fall back to launching whatever EXE is already on disk.
    """
    try:
        log_info("Checking for updates...")
        data = fetch_latest_release_data()
        raw_tag = data.get("tag_name", "")
        latest_tag = raw_tag.lstrip("v")  # strip a leading "v" if present

        log_info(f"Latest release on GitHub: {latest_tag} (local: {LOCAL_VERSION})")

        if parse_version(latest_tag) > parse_version(LOCAL_VERSION):
            log_info("Newer version detected. Downloading and replacing...")
            asset_api_url, asset_name = find_latest_exe_asset(data)

            download_and_replace(asset_api_url, asset_name)
            log_info(f"Replaced old EXE with version {latest_tag}.")
            # Note: The download_and_replace function will handle launching the updated EXE
            # Either directly (if direct replacement worked) or via batch script
            # The process will exit after this point, so no further code will run
        else:
            log_info("Already up to date. Launching existing EXE.")
            launch_updated_exe()

    except Exception as exc:
        # Any failure -> log and fall back to launching whatever is on disk
        log_warn(f"Update check failed: {exc!r}")
        launch_updated_exe()


if __name__ == "__main__":
    main()