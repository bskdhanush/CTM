"""
QSTAF launcher – ONLY two decisions
───────────────────────────────────
1. remote_tag > __version__  -> download & launch new
2. otherwise                 -> launch local exe that matches __version__
"""
from __future__ import annotations
import os, subprocess, sys, typing

import Check_updates as updater           # local helper module
from packaging.version import parse as vparse

# ── config derived from Check_updates ──────────────────────────────────────
DOWNLOAD_DIR  = updater.DOWNLOAD_DIR           # r"C:\QSTAF"
LOCAL_VERSION = updater.__version__.lstrip("v")
LOCAL_EXE     = os.path.join(DOWNLOAD_DIR, f"QSTAF_Tool_v{LOCAL_VERSION}.exe")

# console UTF‑8 guard
if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass


# ── helpers ────────────────────────────────────────────────────────────────
def _launch(exe_path: str) -> "typing.Never":
    subprocess.Popen(f'cmd /c start "" "{exe_path}"', shell=True)
    sys.exit(0)


def _remove_old(keep_name: str) -> None:
    for fn in os.listdir(DOWNLOAD_DIR):
        if fn.lower().startswith("qstaf_tool_v") and fn.lower() != keep_name.lower():
            try: os.remove(os.path.join(DOWNLOAD_DIR, fn))
            except PermissionError: print(f"[WARN] could not delete {fn}")


def _download_asset(rel: dict) -> str | None:
    """Download the .exe asset from *rel*; return its path or None on error."""
    try:
        url, asset = updater.find_latest_exe_download_url(rel)
        dest       = os.path.join(DOWNLOAD_DIR, asset)

        if not updater.asset_already_present(DOWNLOAD_DIR, asset):
            print(f"[INFO] downloading -> {dest}")
            dest = updater.download_file(url, DOWNLOAD_DIR, asset)
        else:
            print(f"[INFO] build already on disk -> {dest}")

        print(_remove_old(asset))

        return dest
    except Exception as exc:
        print(f"[ERROR] download failed ({exc})")
        return None 


# ── main ───────────────────────────────────────────────────────────────────
def main() -> None:
    try:
        rel = updater.fetch_latest_release_data()
    except Exception as exc:
        print(f"[WARN] could not reach GitHub ({exc}); using local build.")
        if os.path.isfile(LOCAL_EXE):
            _launch(LOCAL_EXE)
        print("[ERROR] no network and local exe missing.")
        sys.exit(1)

    remote_ver = (rel.get("tag_name") or rel.get("name") or "").lstrip("v")

    # ── 1) remote newer? → update ─────────────────────────────────────────
    if vparse(remote_ver) > vparse(LOCAL_VERSION):
        print(f"[INFO] update available: {remote_ver}  (local {LOCAL_VERSION})")
        exe_path = _download_asset(rel)
        if exe_path: _launch(exe_path)
        print("[ERROR] update failed.")
        sys.exit(1)

    # ── 2) up‑to‑date → ensure local exe present, else fetch same version ─
    if os.path.isfile(LOCAL_EXE):
        print(f"[INFO] up‑to‑date ({LOCAL_VERSION}). launching local build…")
        _launch(LOCAL_EXE)

    print(f"[INFO] {os.path.basename(LOCAL_EXE)} missing – re‑downloading.")
    exe_path = _download_asset(rel)          # same version asset
    if exe_path: _launch(exe_path)

    print("[ERROR] could not obtain executable.")
    sys.exit(1)


if __name__ == "__main__":
    main()
