# QSTAFInstaller.py — exit-based flow (no success-line check)
from __future__ import annotations

import zipfile
import tempfile
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional, Tuple, List
import re
import os
import WifiController
from Threading import *

# --------------------------- Destinations (Windows) ---------------------------
QSTAF_BASE = Path(r"C:/QSTAF/QSTAFpy")

StatusCB   = Optional[Callable[[str], None]]
ProgressCB = Optional[Callable[[int], None]]

CREATE_NO_WINDOW = 0x08000000  # Windows hidden console flag

# ------------------------------ Small utilities ------------------------------

def _status(cb: StatusCB, msg: str) -> None:
    if cb:
        try:
            cb(msg)
        except Exception:
            pass

def _progress(cb: ProgressCB, pct: int) -> None:
    if cb:
        try:
            cb(int(max(0, min(100, pct))))
        except Exception:
            pass

# --------------------------- Extraction helpers ------------------------------

def _extract_zip(src: Path, dest: Path) -> None:
    with zipfile.ZipFile(src, "r") as zf:
        zf.extractall(dest)

def _find_7z_exe() -> Optional[Path]:
    p = shutil.which("7z.exe") or shutil.which("7za.exe")
    if p:
        return Path(p)
    for cand in (
        Path(r"C:\Program Files\7-Zip\7z.exe"),
        Path(r"C:\Program Files (x86)\7-Zip\7z.exe"),
    ):
        if cand.exists():
            return cand
    return None

def _extract_7z_with_py7zr(src: Path, dest: Path) -> bool:
    try:
        import py7zr  # type: ignore
    except Exception:
        return False
    with py7zr.SevenZipFile(src, mode="r") as z:
        z.extractall(path=dest)
    return True

def _extract_7z_with_cli(src: Path, dest: Path) -> None:
    exe = _find_7z_exe()
    if not exe:
        raise RuntimeError("7-Zip not found. Install 7-Zip or `pip install py7zr`. ")
    dest.mkdir(parents=True, exist_ok=True)
    cmd = [str(exe), "x", str(src), f"-o{dest}", "-y"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False )#creationflags=CREATE_NO_WINDOW
    if proc.returncode != 0:
        raise RuntimeError(f"7-Zip failed (code {proc.returncode}): {proc.stderr.strip()}")

def _extract_archive(src: Path, dest: Path, on_status: StatusCB,type: str) -> None:
    ext = src.suffix.lower()
    if ext == ".zip":
        if type=="QSTAF":
            _status(on_status, "Extracting ZIP…")
        _extract_zip(src, dest)
        return
    if ext == ".7z":
        if type=="QSTAF":
            _status(on_status, "Extracting 7z…")
        if _extract_7z_with_py7zr(src, dest):
            return
        _extract_7z_with_cli(src, dest)
        return
    raise ValueError("Unsupported archive type. Provide a .zip or .7z file.")

# ------------------------------ BAT runner -----------------------------------
key ="QSTAF and its dependencies have been installed successfully!"
def _run_batch_wait_exit(
    bat_path: Path,
    on_status: StatusCB,
    timeout_sec: int = 300,
) -> Tuple[int, str]:
    """
    Run the batch file hidden and stream output to `on_status`.
    Proceed immediately when the success KEY is printed.
    Returns (returncode, message).
    """
    import queue

    cmd = ["cmd", "/d", "/c", "call", bat_path.name]
    _status(on_status, f"Launching installer… ({bat_path})")

    q: "queue.Queue[Optional[str]]" = queue.Queue()
    success_event = thread_event()

    try:
        p = subprocess.Popen(
            cmd,
            cwd=str(bat_path.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )
    except Exception as e:
        return -1, f"Failed to run installer: {e}"

    def reader():
        try:
            for line in p.stdout:  # type: ignore
                q.put(line)
                if key in line:
                    _status(on_status, "[installer] Success key detected.")
                    success_event.set()
                    break
        except Exception:
            pass

    start_thread(reader,"", daemon=True)

    start = time.time()
    while True:
        if success_event.is_set():
            try:
                p.terminate()
            except Exception:
                pass
            return 0, "Installer key detected – proceeding to next step."

        if time.time() - start > timeout_sec:
            try:
                p.kill()
            except Exception:
                pass
            return -1, "Installer timed out."

        try:
            item = q.get(timeout=0.2)
        except queue.Empty:
            if p.poll() is not None:
                break
            continue

        if item:
            s = item.rstrip("\r\n")
            if s:
                _status(on_status, f"[installer] {s}")

    try:
        rc = p.wait(timeout=5)
    except Exception:
        rc = 0

    return rc, "Installer exited."

# -------------------------- Copy helper with report --------------------------

def _copy_verified(src: Path, dst: Path, on_status: StatusCB) -> Optional[str]:
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        size_src = src.stat().st_size
        try:
            size_dst = dst.stat().st_size
        except Exception:
            size_dst = -1
        if size_dst != size_src:
            err = f"Verification failed for {dst} (expected {size_src} bytes, got {size_dst})."
            _status(on_status, err)
            return err
        _status(on_status, f"Copied {src.name} ({size_src} bytes) → {dst}")
        if 'config.yaml' in src.name:
            update_config_yaml_with_adbid(dst)
        return None
    except Exception as e:
        err = f"Copy failed {src} → {dst}: {e}"
        _status(on_status, err)
        return err

def replacer(match):
    adb_id = WifiController.get_adb_id()
    if adb_id:
        return f'{match.group(1)}{adb_id}'
    else:
        return f'{match.group(1)}{match.group(2)}'

def update_config_yaml_with_adbid(config_file):
    config_content = ''
    with open(config_file, 'r') as f:
        config_content = f.read()
    updated_config = re.sub(r'(adb_serial_id\s*:\s*)(\w+)', replacer, config_content)
    with open(config_file, 'w') as f:
        f.write(updated_config)
# ------------------------------- Main routine --------------------------------

def install_qstaf_from_zip(
    archive_path: str,
    on_status: StatusCB = None,
    on_progress: ProgressCB = None,
    keep_temp: bool = False,
    timeout_sec: int = 600,
) -> Tuple[bool, str]:
    """Exit-based flow: proceed to replace files after the BAT process exits."""
    apath = Path(archive_path)
    if not apath.exists() or apath.suffix.lower() not in (".zip", ".7z"):
        return False, f"Invalid archive (expected .zip or .7z): {archive_path}"

    temp_dir = Path(tempfile.mkdtemp(prefix="qstaf_"))
    _status(on_status, f"Temp dir: {temp_dir}")

    try:
        # 1) Extract
        _status(on_status, "Preparing to extract…")
        _progress(on_progress, 5)
        _extract_archive(apath, temp_dir, on_status,"QSTAF")
        _progress(on_progress, 25)

        # 2) Run installer
        _status(on_status, "Locating qstaf_install.bat…")
        bat_path = next((p for p in temp_dir.rglob("qstaf_install.bat")), None)
        if not bat_path:
            return False, "qstaf_install.bat not found in the archive."

        _status(on_status, f"Running installer: {bat_path}")
        _status(on_status, "Running installer…")
        _progress(on_progress, 45)

        rc, msg = _run_batch_wait_exit(bat_path, on_status, timeout_sec=timeout_sec)
        _status(on_status, f"Installer result: rc={rc} – {msg}")
      

        # Proceed regardless of rc, per request. We still report rc in final message.

        # 3) Copy files from Replace
        _progress(on_progress, 60)
        _status(on_status, "Locating 'Replace' folder…")
        replace_dir = next(
            (p for p in temp_dir.rglob("*") if p.is_dir() and p.name.lower() == "replace"),
            None,
        )
        if not replace_dir:
            return False, "Replace folder not found."

        _status(on_status, f"Replace dir: {replace_dir}")

        def find_in_dir(name: str, directory: Path) -> Optional[Path]:
            return next((p for p in directory.rglob(name)), None)

        _status(on_status, "Copying updated files…")
        step = 60
        step_inc = 40 // max(1, len(os.listdir(replace_dir)))

        errors: List[str] = []
        for src_name in os.listdir(replace_dir):
            dst_path = find_in_dir(src_name, QSTAF_BASE)
            if not dst_path or not dst_path.exists():
                msg_missing = f"File {src_name} not found in : {QSTAF_BASE.name}"
                _status(on_status, msg_missing)
                errors.append(msg_missing)
            else:
                err = _copy_verified(Path(os.path.join(replace_dir, src_name)), dst_path, on_status)
                if err:
                    errors.append(err)
            step += step_inc
            _progress(on_progress, step)

        _progress(on_progress, 100)
        if errors:
            _status(on_status, f"Completed with errors (installer rc={rc})")
            return False, f"Completed with errors (installer rc={rc}): " + "; ".join(errors)

        _status(on_status, "Completed.")
        return True, f"QSTAF installed; installer rc={rc}. Files replaced successfully."

    except Exception as e:
        return False, str(e)

    finally:
        if not keep_temp:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

# ---------------------- Legacy wrapper kept for GUI compat --------------------

def isntallQSTAF(filePAth: str):
    """Legacy misspelled API still used by existing GUI code."""
    return install_qstaf_from_zip(filePAth)
