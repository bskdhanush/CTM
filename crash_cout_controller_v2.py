# crash_cout_controller_v2.py

import json
from pathlib import Path
from datetime import datetime, date, time

# — Configurable paths & thresholds —
CRASHDUMP_ROOT = Path(r"C:\QSTAF\crashDump")
CONFIG_PATH    = Path(r"C:\QSTAF\app_config.json")
MIN_SIZE_BYTES = 1.5 * 1024**3  # 1.5 GB

# — JSON I/O helpers —
def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=4, sort_keys=True), encoding="utf-8")

# — Filesystem helpers —
def most_recent_subdir(root: Path) -> Path | None:
    if not root.is_dir(): 
        return None
    subs = [p for p in root.iterdir() if p.is_dir()]
    return max(subs, key=lambda p: p.stat().st_mtime) if subs else None

def get_folder_size_bytes(folder: Path) -> int:
    return sum(f.stat().st_size for f in folder.rglob("*") if f.is_file())

# — Main processing function —
def process_new_dumps() -> dict:
    cfg = load_config()

    # Initialize defaults
    cfg.setdefault("previous_first_child_dir", None)
    cfg.setdefault("selected_dump_dir",       None)
    cfg.setdefault("day_counter",             0)
    cfg.setdefault("night_counter",           0)

    # 1) Detect & handle first‐child change
    first_child = most_recent_subdir(CRASHDUMP_ROOT)
    fc_path     = str(first_child) if first_child else None

    if fc_path != cfg["previous_first_child_dir"]:
        # Reset counters & last‐seen dump when parent folder rotates
        cfg["day_counter"]             = 0
        cfg["night_counter"]           = 0
        cfg["selected_dump_dir"]       = None
        cfg["previous_first_child_dir"] = fc_path

    # 2) Determine cutoff time from last seen dump
    prev_path = cfg["selected_dump_dir"]
    if prev_path and Path(prev_path).exists():
        prev_mtime = datetime.fromtimestamp(Path(prev_path).stat().st_mtime)
    else:
        prev_mtime = datetime.fromtimestamp(0)  # epoch → everything is new

    # 3) Gather & filter new dump folders
    new_folders = []
    if first_child:
        # all subfolders whose name[:4].isdigit() and size ≥ threshold
        candidates = [
            p for p in first_child.iterdir()
            if p.is_dir()
               and len(p.name) >= 4
               and p.name[:4].isdigit()
               and get_folder_size_bytes(p) >= MIN_SIZE_BYTES
        ]
        # only those strictly newer than prev_mtime
        new_folders = [
            p for p in candidates
            if datetime.fromtimestamp(p.stat().st_mtime) > prev_mtime
        ]
        # chronological order
        new_folders.sort(key=lambda p: p.stat().st_mtime)

    # 4) Classify & count each new dump
    today = date.today()
    for p in new_folders:
        ts = datetime.fromtimestamp(p.stat().st_mtime)
        t  = ts.time()
        d  = ts.date()

        # Day window only if on the same date
        if d == today and time(9,0) <= t <= time(18,0):
            cfg["day_counter"]   += 1
        else:
            cfg["night_counter"] += 1

    # 5) Update JSON with the latest-seen dump
    if new_folders:
        cfg["selected_dump_dir"] = str(new_folders[-1])

    save_config(cfg)

    return {
        "first_child_dir": fc_path,
        "new_folders":     [str(p) for p in new_folders],
        "day_counter":     cfg["day_counter"],
        "night_counter":   cfg["night_counter"],
    }

# — CLI entrypoint for testing —
if __name__ == "__main__":
    result = process_new_dumps()

    print(f"First child   : {result['first_child_dir']}")
    if result["new_folders"]:
        print("New dump folders:")
        for p in result["new_folders"]:
            print("  ", p)
    else:
        print("No new dump folders since last run.")

    print(f"\nDay counter   : {result['day_counter']}")
    print(f"Night counter : {result['night_counter']}")
