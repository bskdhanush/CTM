"""
Self‑updater for QSTAF_Tool_v*.exe

  • Looks at the latest GitHub release for bskdhanush/QC_stuff
  • If a newer build exists, downloads it to C:\QSTAF
  • Can run stand‑alone:   python -m Check_updates --update-only
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Tuple, Any

import requests
from packaging.version import parse as parse_version

# ── Configuration ─────────────────────────────────────────────────────
GITHUB_USERNAME   = os.getenv("GITHUB_USERNAME", "bskdhanush")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "QC_stuff")
GITHUB_PAT        = os.getenv("GITHUB_PAT") or "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"      # ← do *not* hard‑code
DOWNLOAD_DIR      = Path(r"C:\QSTAF")

EXE_PREFIX = "QSTAF_Tool_v"
EXT        = ".exe"

# ── Helpers ───────────────────────────────────────────────────────────
def _github_session() -> requests.Session:
    if not GITHUB_PAT:
        raise RuntimeError("GITHUB_PAT environment variable is missing.")
    s = requests.Session()
    s.headers.update(
        {
            "Authorization": f"token {GITHUB_PAT}",
            "Accept":        "application/vnd.github.v3+json",
            "User-Agent":    "qstaf-updater",
        }
    )
    return s


def _current_version() -> str:
    """Extract 1.2.2 from the running exe name, else fall back to env var."""
    m = re.search(rf"{EXE_PREFIX}(\d+\.\d+\.\d+){EXT}", Path(sys.executable).name)
    if m:
        return m.group(1)
    return os.getenv("APP_VERSION", "0.0.0")


__version__ = _current_version()


def _fetch_latest_release() -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/releases/latest"
    r = _github_session().get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def _pick_windows_asset(release_json: Dict[str, Any]) -> Dict[str, Any]:
    for asset in release_json.get("assets", []):
        n = asset.get("name", "")
        if n.startswith(EXE_PREFIX) and n.endswith(EXT):
            return asset
    raise ValueError("No Windows .exe asset found in the latest release.")


def _is_update_needed(latest_tag: str) -> bool:
    return parse_version(latest_tag.lstrip("v")) > parse_version(__version__)


# ── Public API (used by launcher.py) ───────────────────────────────────
def check_for_update() -> Tuple[bool, Dict[str, Any] | None]:
    """
    Returns (needs_update, asset_dict | None).
    """
    release = _fetch_latest_release()
    latest_tag = release.get("tag_name", "").lstrip("v")

    if not _is_update_needed(latest_tag):
        return False, None

    return True, _pick_windows_asset(release)


def _download_asset(asset: Dict[str, Any]) -> Path:
    """
    Streams the asset to C:\QSTAF, skipping if identical file already exists.
    Returns the full path.
    """
    dst = DOWNLOAD_DIR / asset["name"]
    if dst.exists() and dst.stat().st_size == asset["size"]:
        print(f"[INFO] {dst} already present – skipping download.")
        return dst

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Downloading {asset['name']} → {dst}")

    with _github_session().get(asset["browser_download_url"], stream=True, timeout=60) as r, dst.open("wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

    return dst


def launch_new_exe(exe_path: Path) -> None:
    """
    Start the new build in its own console and terminate this process.
    """
    print(f"[INFO] Launching new build: {exe_path}")
    subprocess.Popen(["cmd", "/c", "start", '""', str(exe_path)], shell=True, close_fds=True)
    sys.exit(0)


# ── CLI usage ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    only = "--update-only" in sys.argv
    try:
        need, asset = check_for_update()
    except Exception as exc:
        print(f"[ERROR] Update check failed: {exc}")
        sys.exit(1 if only else 0)

    if need:
        path = _download_asset(asset)          # type: ignore[arg-type]
        launch_new_exe(path)

    if only:
        print("[INFO] Already on the latest version.")
