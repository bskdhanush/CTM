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

def ensure_tracker(tracker_file: Path, crashType: str) -> dict:
    """
    Ensure tracker file exists and return the crashType's sub-dictionary.
    """
    if not tracker_file.exists():
        with tracker_file.open("w") as f:
            json.dump({crashType: {"last_seen_datetime": "1970-01-01 00:00:00.000000"}}, f, indent=2)

    try:
        with tracker_file.open("r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        with tracker_file.open("w") as f:
            json.dump({crashType: {"last_seen_datetime": "1970-01-01 00:00:00.000000"}}, f, indent=2)
        return {crashType: {"last_seen_datetime": "1970-01-01 00:00:00.000000"}}

    # Ensure crashType key exists
    if crashType not in data:
        data[crashType] = {"last_seen_datetime": "1970-01-01 00:00:00.000000"}
        with tracker_file.open("w") as f:
            json.dump(data, f, indent=2)

    return data.get(crashType, {})



def update_tracker(tracker_file: Path, latest_time: float, latest_folder: str, parent_path: Path, crashType: str):
    """
    Update tracker JSON using nested structure per crashType.
    """
    if tracker_file.exists():
        try:
            with tracker_file.open("r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("[WARN] Tracker file corrupt. Resetting...")
            data = {}
    else:
        data = {}

    # Update nested block
    data[crashType] = {
        "last_seen_datetime": datetime.fromtimestamp(latest_time).strftime("%Y-%m-%d %H:%M:%S.%f"),
        "last_seen_folder": latest_folder,
        "first_child_path": str(parent_path),
        "DIR_Counter":0,
        "OVN_Counter":0

    }

    with tracker_file.open("w") as f:
        json.dump(data, f, indent=2)
        print(f"[INFO] Tracker updated for {crashType}")




def get_latest_dir_update_json(root,depth,tracker_file,crashType):
    # Step 1: Load tracker
    tracker = ensure_tracker(tracker_file,crashType)
    last_seen_dt_str = tracker.get("last_seen_datetime", "1970-01-01 00:00:00.000000")
    print(last_seen_dt_str)

    # Step 2: Get the first child folder (depth=1)
    first_child_result = get_latest_folder_by_depth(root, depth)
    if not first_child_result:
        print("[WARN] Could not determine first child folder.")
        return

    first_child_path, readable_time = first_child_result
    print(f"[INFO] First child path: {first_child_path} (discovered at {readable_time})")

    # Step 3: Check for unseen folders in that path
    parent_path = first_child_path.parent
    new_folders = get_unseen_folders_since(parent_path, last_seen_dt_str)


    if not new_folders:
        print("[INFO] No new folders found.")
    else:
        print(f"[INFO] Found {len(new_folders)} new folder(s):")
        for folder, ts, formatted_time in new_folders:
            print(f"  - {folder.name} (modified: {datetime.fromtimestamp(ts)})")
            # Your processing logic here

        # Step 4: Update tracker with latest folder info
        latest_folder, latest_time, _ = new_folders[-1]
        update_tracker(tracker_file, latest_time, latest_folder.name, parent_path,crashType)
        print(f"[INFO] Tracker updated with timestamp: {latest_time}")