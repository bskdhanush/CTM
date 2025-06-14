from datetime import datetime
from handler import GetLatest_dir as gd
from pathlib import Path

def main():
    root = Path(r"C:\QSTAF\crashDump")
    depth = 1
    tracker_file = Path(r"C:\QSTAF\app_config.json")

    # Step 1: Load tracker
    tracker = gd.ensure_tracker(tracker_file)
    last_seen_dt_str = tracker.get("last_seen_datetime", "1970-01-01 00:00:00")

    # Step 2: Get the first child folder (depth=1)
    first_child_result = gd.get_latest_folder_by_depth(root, depth)
    if not first_child_result:
        print("[WARN] Could not determine first child folder.")
        return

    first_child_path, readable_time = first_child_result
    print(f"[INFO] First child path: {first_child_path} (discovered at {readable_time})")

    # Step 3: Check for unseen folders in that path
    parent_path = first_child_path.parent
    new_folders = gd.get_unseen_folders_since(parent_path, last_seen_dt_str)


    if not new_folders:
        print("[INFO] No new folders found.")
    else:
        print(f"[INFO] Found {len(new_folders)} new folder(s):")
        for folder, ts, formatted_time in new_folders:
            print(f"  - {folder.name} (modified: {datetime.fromtimestamp(ts)})")
            # Your processing logic here

        # Step 4: Update tracker with latest folder info
        latest_folder, latest_time, _ = new_folders[-1]
        gd.update_tracker(tracker_file, latest_time, latest_folder.name, parent_path)
        print(f"[INFO] Tracker updated with timestamp: {latest_time}")

if __name__ == "__main__":
    main()