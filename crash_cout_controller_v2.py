# crash_cout_controller_v2.py

import json
import time
from pathlib import Path
from datetime import datetime, date, time as dt_time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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

# — Core processing —
def process_new_dumps() -> dict:
    cfg = load_config()
    now = datetime.now()

    # Initialize defaults
    cfg.setdefault("previous_first_child_dir", None)
    cfg.setdefault("selected_dump_dir",       None)
    cfg.setdefault("day_counter",             0)
    cfg.setdefault("night_counter",           0)
    cfg.setdefault("last_day_reset",          None)
    cfg.setdefault("last_night_reset",        None)

    # 1) Handle first-child change
    first_child = most_recent_subdir(CRASHDUMP_ROOT)
    fc_path     = str(first_child) if first_child else None
    if fc_path != cfg["previous_first_child_dir"]:
        cfg["day_counter"]               = 0
        cfg["night_counter"]             = 0
        cfg["selected_dump_dir"]         = None
        cfg["previous_first_child_dir"]  = fc_path
        cfg["last_day_reset"]            = None
        cfg["last_night_reset"]          = None

    # 2) Daily time-based resets
    today = date.today()
    # Day reset at 08:59 AM
    day_reset_time = datetime.combine(today, dt_time(8, 59))
    if now >= day_reset_time and cfg.get("last_day_reset") != today.isoformat():
        cfg["day_counter"]     = 0
        cfg["last_day_reset"]  = today.isoformat()
    # Night reset at 05:59 PM
    night_reset_time = datetime.combine(today, dt_time(17, 59))
    if now >= night_reset_time and cfg.get("last_night_reset") != today.isoformat():
        cfg["night_counter"]     = 0
        cfg["last_night_reset"]  = today.isoformat()

    # 3) Determine cutoff from last seen dump
    prev_path = cfg["selected_dump_dir"]
    if prev_path and Path(prev_path).exists():
        prev_mtime = datetime.fromtimestamp(Path(prev_path).stat().st_mtime)
    else:
        prev_mtime = datetime.fromtimestamp(0)

    # 4) Collect & filter new dumps
    new_folders = []
    if first_child:
        candidates = [
            p for p in first_child.iterdir()
            if p.is_dir()
               and len(p.name) >= 4
               and p.name[:4].isdigit()
               and get_folder_size_bytes(p) >= MIN_SIZE_BYTES
        ]
        new_folders = [
            p for p in candidates
            if datetime.fromtimestamp(p.stat().st_mtime) > prev_mtime
        ]
        new_folders.sort(key=lambda p: p.stat().st_mtime)

    # 5) Classify & count
    today = date.today()
    for p in new_folders:
        ts = datetime.fromtimestamp(p.stat().st_mtime)
        t  = ts.time()
        d  = ts.date()
        if d == today and dt_time(9, 0) <= t <= dt_time(18, 0):
            cfg["day_counter"]  += 1
        else:
            cfg["night_counter"]+= 1

    # 6) Update last-seen
    if new_folders:
        cfg["selected_dump_dir"] = str(new_folders[-1])
    save_config(cfg)

    return {
        "first_child_dir": fc_path,
        "new_folders":     [str(p) for p in new_folders],
        "day_counter":     cfg["day_counter"],
        "night_counter":   cfg["night_counter"],
    }

# — Watchdog handler & runner —
class CrashDumpHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_day = None
        self.last_night = None

    def on_created(self, event):
        if not event.is_directory:
            return
        # Only trigger on new directory creation
        time.sleep(10)
        result = process_new_dumps()
        # Print only when counters change
        day, night = result['day_counter'], result['night_counter']
        if (day != self.last_day) or (night != self.last_night):
            print(f"[watchdog] First: {result['first_child_dir']}, "
                  f"Day: {day}, Night: {night}")
            self.last_day, self.last_night = day, night


def run_watchdog(poll_interval: float = 1.0) -> None:
    observer = Observer()
    handler  = CrashDumpHandler()
    observer.schedule(handler, str(CRASHDUMP_ROOT), recursive=True)
    observer.start()
    print(f"[INFO] Watching {CRASHDUMP_ROOT}…")
    try:
        while True:
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# — CLI entrypoint —
if __name__ == "__main__":
    run_watchdog()
