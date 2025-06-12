# crash_counter_controller.py

import json, time, schedule, threading, logging
from pathlib import Path
from datetime import datetime, date, time as dt_time, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# — Minimal logging —
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("Counter")

# — Config —
CRASHDUMP_ROOT     = Path(r"C:\QSTAF\crashDump")
RDKBCRASH_ROOT     = Path(r"C:\Temp\automation\QSTAF\QSTAFpy\appcrash_logs")
CONFIG_PATH        = Path(r"C:\QSTAF\app_config.json")

MIN_CRASH_SIZE     = 1.5 * 1024**3    # 1.5 GB
MIN_RDKBCRASH_SIZE = 2   * 1024**2    # 2 MB

def load_config() -> dict:
    try:    return json.loads(CONFIG_PATH.read_text("utf-8"))
    except: return {}

def save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=4, sort_keys=True), "utf-8")

def most_recent_subdir(root: Path) -> Path | None:
    if not root.is_dir(): return None
    subs = [p for p in root.iterdir() if p.is_dir()]
    return max(subs, key=lambda p: p.stat().st_mtime) if subs else None

def get_size(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())

def process_dir(root: Path,
                prefix: str,
                min_size: int,
                scan_root: bool = False) -> tuple[int,int]:
    cfg = load_config()
    now = datetime.now(); today = date.today()

    # state keys
    prev_k    = f"previous_{prefix}_dir"
    base_k    = f"last_{prefix}_base"
    day_k     = f"{prefix}_day_counter"
    night_k   = f"{prefix}_night_counter"
    last_d_k  = f"last_{prefix}_day_reset"
    last_n_k  = f"last_{prefix}_night_reset"

    # defaults
    for k in (prev_k, base_k):
        cfg.setdefault(k, None)
    for k in (day_k, night_k, last_d_k, last_n_k):
        cfg.setdefault(k, 0 if "counter" in k else None)

    # if the first‐level folder changed, reset everything
    base = root if scan_root else most_recent_subdir(root)
    base_str = str(base) if base else None
    if cfg[base_k] != base_str:
        cfg[day_k]   = 0
        cfg[night_k] = 0
        cfg[prev_k]  = None
        cfg[base_k]  = base_str
        log.info(f"{prefix.upper()} base changed → counters reset")

    # daily resets at 09:00 and 17:59
    def reset_at(h,m,c_k,l_k):
        mark = datetime.combine(today, dt_time(h,m))
        last = datetime.fromisoformat(cfg[l_k]) if cfg[l_k] else None
        if now >= mark and (not last or now - last >= timedelta(hours=24)):
            cfg[c_k] = 0
            cfg[l_k] = mark.isoformat()
    reset_at(9,0,   day_k,  last_d_k)
    reset_at(17,59, night_k,last_n_k)

    # cutoff for new
    prev = cfg[prev_k]
    prev_m = (datetime.fromtimestamp(Path(prev).stat().st_mtime)
              if prev and Path(prev).exists()
              else datetime.fromtimestamp(0))

    # collect new subfolders
    new = []
    if base:
        for p in base.iterdir():
            if not p.is_dir(): continue
            if not (len(p.name)>=4 and p.name[:4].isdigit()): continue
            sz = get_size(p)
            if sz < min_size: continue
            mtime = datetime.fromtimestamp(p.stat().st_mtime)
            if mtime <= prev_m: continue
            new.append((p, mtime))
    new.sort(key=lambda x: x[1])

    # tally and advance prev pointer
    for p, mtime in new:
        t = mtime.time()
        if mtime.date()==today and dt_time(9,0)<=t<=dt_time(18,0):
            cfg[day_k] += 1
        else:
            cfg[night_k] += 1
        cfg[prev_k] = str(p)

    save_config(cfg)
    return cfg[day_k], cfg[night_k]

from pathlib import Path

def _is_level(event_path: str, root: Path, depth: int) -> bool:
    '''
    Return True if *event_path* is exactly *depth* levels below *root*.
    depth = 1  →  C:\root\child
    depth = 2  →  C:\root\child\grandchild
    '''
    try:
        rel_parts = Path(event_path).resolve().relative_to(root).parts
        return len(rel_parts) == depth
    except ValueError:               # not under *root*
        return False


class CrashHandler(FileSystemEventHandler):
    def on_created(self, e):
        if not e.is_directory:
            return
        if not _is_level(e.src_path, CRASHDUMP_ROOT, depth=2):
            return                      # ignore dev3 itself & any deeper dirs

        # Give the dumper a moment to finish writing
        threading.Timer(
            10,
            lambda: self._tally()
        ).start()

    def _tally(self):
        d, n = process_dir(CRASHDUMP_ROOT, 'crash', MIN_CRASH_SIZE)
        log.info("Crash  → Day:%d Night:%d", d, n)


class RdkbHandler(FileSystemEventHandler):
    def on_created(self, e):
        if not e.is_directory:
            return
        if not _is_level(e.src_path, RDKBCRASH_ROOT, depth=1):
            return                      # ignore sub-folders of a log

        threading.Timer(
            10,
            lambda: self._tally()
        ).start()

    def _tally(self):
        d, n = process_dir(RDKBCRASH_ROOT, 'rdkbcrash',
                           MIN_RDKBCRASH_SIZE, scan_root=True)
        log.info("RDKB   → Day:%d Night:%d", d, n)


def schedule_resets():
    schedule.every().day.at("09:00")  .do(lambda: process_dir(CRASHDUMP_ROOT, 'crash',    MIN_CRASH_SIZE))
    schedule.every().day.at("17:59") .do(lambda: process_dir(CRASHDUMP_ROOT, 'crash',    MIN_CRASH_SIZE))
    schedule.every().day.at("09:00")  .do(lambda: process_dir(RDKBCRASH_ROOT,'rdkbcrash',MIN_RDKBCRASH_SIZE, scan_root=True))
    schedule.every().day.at("17:59") .do(lambda: process_dir(RDKBCRASH_ROOT,'rdkbcrash',MIN_RDKBCRASH_SIZE, scan_root=True))
    while True:
        schedule.run_pending()
        time.sleep(30)

def run_watchdog():
    process_dir(CRASHDUMP_ROOT, 'crash',    MIN_CRASH_SIZE)
    process_dir(RDKBCRASH_ROOT,'rdkbcrash',MIN_RDKBCRASH_SIZE, scan_root=True)

    threading.Thread(target=schedule_resets, daemon=True).start()
    obs = Observer()
    obs.schedule(CrashHandler(), str(CRASHDUMP_ROOT), recursive=True)
    obs.schedule(RdkbHandler(), str(RDKBCRASH_ROOT), recursive=True)
    obs.start()
    log.info("Watching for new folders…")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        obs.stop(); obs.join()
        log.info("Watcher stopped.")

if __name__ == "__main__":
    run_watchdog()
