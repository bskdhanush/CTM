from pathlib import Path
from datetime import datetime
from typing import Optional


def get_latest_folder_by_depth(root: Path, depth: int) -> Optional[tuple[Path, str]]:
    """
    Return the latest folder at the specified depth level from root.

    When depth = 0, it returns the latest folder *inside* root (not root itself).
    When depth = 1, it returns latest subfolder inside the latest first child.
    """
    if not root.exists() or depth < 0:
        return None

    # Get all subdirectories in current level
    subdirs = [d for d in root.iterdir() if d.is_dir()]
    if not subdirs:
        return None

    # Select latest subdirectory based on last modified time
    latest_sub = max(subdirs, key=lambda d: d.stat().st_mtime)

    # If depth is 0, return this subfolder
    if depth == 0:
        mtime = latest_sub.stat().st_mtime
        return latest_sub, datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

    # Go one level deeper
    return get_latest_folder_by_depth(latest_sub, depth - 1)


def get_unseen_folders_since(root: Path, last_seen_datetime_str: str) -> list[tuple[Path, float, str]]:
    """
    Return a list of folders under *root* modified after *last_seen_datetime*.
    Each result is (Path, mtime, formatted_datetime).
    """
    if not root.exists() or not root.is_dir():
        return []

    try:
        last_seen_dt = datetime.strptime(last_seen_datetime_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        print("[WARN] Invalid datetime format in tracker. Defaulting to epoch.")
        last_seen_dt = datetime.fromtimestamp(0)

    unseen = []
    for p in root.iterdir():
        if p.is_dir():
            mtime = p.stat().st_mtime
            mtime_dt = datetime.fromtimestamp(mtime)
            if mtime_dt > last_seen_dt:
                formatted_time = mtime_dt.strftime("%Y-%m-%d %H:%M:%S")
                unseen.append((p, mtime, formatted_time))

    return sorted(unseen, key=lambda x: x[1])


import json

def ensure_tracker(tracker_file: Path) -> dict:
    """
    Ensure the tracker file exists and return its content as a dict.
    If missing or corrupted, initialize with default values.
    """
    if not tracker_file.exists():
        with tracker_file.open("w") as f:
            json.dump({"last_seen_time": 0.0}, f, indent=2)

    try:
        with tracker_file.open("r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        with tracker_file.open("w") as f:
            json.dump({"last_seen_time": 0.0}, f, indent=2)
        return {"last_seen_time": 0.0}


def update_tracker(tracker_file: Path, latest_time: float, latest_folder: str, parent_path: Path):
    """
    Update the tracker file with latest folder's time and name.
    """
    data = {
        "last_seen_datetime": datetime.fromtimestamp(latest_time).strftime("%Y-%m-%d %H:%M:%S.%f"),
        "last_seen_folder": latest_folder,
        "first_child_path": str(parent_path)
    }
    with tracker_file.open("w") as f:
        print("method called")
        json.dump(data, f, indent=2)
