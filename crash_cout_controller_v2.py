# crash_counter_controller.py

import json
import time
import threading
import logging
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
# CRASHDUMP_ROOT     = Path(r"C:\QSTAF\crashDump")
CRASHDUMP_ROOT_PCAT  = Path(r"C:\ProgramData\Qualcomm\PCAT\AddOns\CrashCollection\MemoryDumps")
CRASHDUMP_ROOT_QSTAF = Path(r"C:\Temp\automation\QSTAF\QSTAFpy\crashdumps")
RDKBCRASH_ROOT     = Path(r"C:\Temp\automation\QSTAF\QSTAFpy\appcrash_logs")
CONFIG_PATH        = Path(r"C:\QSTAF\app_config.json")

MIN_CRASH_SIZE     = 1.5 * 1024**3   # 1.5 GiB
MIN_RDKBCRASH_SIZE = 2   * 1024**2   # 2 MB

# Lock for thread-safe config I/O
_cfg_lock = threading.Lock()

def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text("utf-8"))
    except Exception as e:
        log.error("App_json is has no data: %s", e)
        return {}


def save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=4, sort_keys=True),
        "utf-8"
    )


def most_recent_subdir(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    subs = [p for p in root.iterdir() if p.is_dir()]
    return max(subs, key=lambda p: p.stat().st_mtime) if subs else None


def get_size(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())

def rest_counter():
    cfg = load_config()
    print("entred the restvoubnt" )
    cfg["rdkbcrash_day_counter"] =0
    cfg["rdkbcrash_night_counter"] =0
    cfg["crash_day_counter"] =0
    cfg["crash_night_counter"] =0
    save_config(cfg)

def process_dir(root: Path,
                prefix: str,
                min_size: float,
                scan_root: bool = False) -> tuple[int, int]:
    with _cfg_lock:
        cfg = load_config()
        now = datetime.now()
        today = date.today()

        # state keys
        prev_k    = f"previous_{prefix}_dir"
        base_k    = f"last_{prefix}_base"
        day_k     = f"{prefix}_day_counter"
        night_k   = f"{prefix}_night_counter"
        last_d_k  = f"last_{prefix}_day_reset"
        last_n_k  = f"last_{prefix}_night_reset"

        # initialize defaults
        for k in (prev_k, base_k):
            cfg.setdefault(k, None)
        for k in (day_k, night_k, last_d_k, last_n_k):
            cfg.setdefault(k, 0 if "counter" in k else None)

        # detect base change → reset
        base = root if scan_root else most_recent_subdir(root)
        base_str = str(base) if base else None
        if cfg[base_k] != base_str:
            cfg[day_k] = 0
            cfg[night_k] = 0
            cfg[prev_k] = None
            cfg[base_k] = base_str
            log.info(f"{prefix.upper()} base changed → counters reset")
        '''
        # daily resets at 09:00 and 17:59
        def reset_at(h, m, c_k, l_k):
            mark = datetime.combine(today, dt_time(h, m))
            last = datetime.fromisoformat(cfg[l_k]) if cfg[l_k] else None
            if now >= mark and (not last or now - last >= timedelta(hours=24)):
                cfg[c_k] = 0
                cfg[l_k] = mark.isoformat()

        reset_at(9,  0,   day_k,   last_d_k)
        reset_at(17, 59,  night_k, last_n_k)
        '''
        # compute day/night windows
        start_day = datetime.combine(today, dt_time(9, 0))
        end_day   = datetime.combine(today, dt_time(18, 0))
        if now < start_day:
            night_start = datetime.combine(today - timedelta(days=1), dt_time(18, 0))
            night_end   = start_day
        else:
            night_start = end_day
            night_end   = datetime.combine(today + timedelta(days=1), dt_time(9, 0))

        # cutoff for new
        prev = cfg.get(prev_k)
        prev_m = (
            datetime.fromtimestamp(Path(prev).stat().st_mtime)
            if prev and Path(prev).exists()
            else datetime.fromtimestamp(0)
        )

        # collect new subfolders
        new = []
        if base:
            for p in base.iterdir():
                if not p.is_dir(): continue
                if not (len(p.name) >= 4 and p.name[:4].isdigit()): continue
                sz = get_size(p)
                if sz < min_size: continue
                mtime = datetime.fromtimestamp(p.stat().st_mtime)
                if mtime <= prev_m: continue
                new.append((p, mtime))
        new.sort(key=lambda x: x[1])

        # tally and advance prev when counted
        for p, mtime in new:
            if start_day <= mtime < end_day:
                cfg[day_k] += 1
            elif night_start <= mtime < night_end:
                cfg[night_k] += 1
            else:
                continue

            cfg[prev_k] = str(p)

        save_config(cfg)


        return cfg[day_k], cfg[night_k]

'''
def schedule_resets():
    schedule.every().day.at("09:00").do(
        lambda: process_dir(CRASHDUMP_ROOT, 'crash',    MIN_CRASH_SIZE)
    )
    schedule.every().day.at("17:59").do(
        lambda: process_dir(CRASHDUMP_ROOT, 'crash',    MIN_CRASH_SIZE)
    )
    schedule.every().day.at("09:00").do(
        lambda: process_dir(RDKBCRASH_ROOT,'rdkbcrash',MIN_RDKBCRASH_SIZE, scan_root=True)
    )
    schedule.every().day.at("17:59").do(
        lambda: process_dir(RDKBCRASH_ROOT,'rdkbcrash',MIN_RDKBCRASH_SIZE, scan_root=True)
    )
    while True:
        schedule.run_pending()
        time.sleep(30)
'''


class CrashHandler(FileSystemEventHandler):
    def on_created(self, e):
        if e.is_directory and e.src_path.startswith(str(CRASHDUMP_ROOT_PCAT)):
            time.sleep(120)
            d, n = process_dir(CRASHDUMP_ROOT_PCAT, 'crash', MIN_CRASH_SIZE)
           # log.info("Crash → Day:%d Night:%d", d, n)


class RdkbHandler(FileSystemEventHandler):
    def on_created(self, e):
        if e.is_directory and e.src_path.startswith(str(RDKBCRASH_ROOT)):
            time.sleep(40)
            d, n = process_dir(
                RDKBCRASH_ROOT, 'rdkbcrash', MIN_RDKBCRASH_SIZE, scan_root=True
            )
            #log.info("RDKB  → Day:%d Night:%d", d, n)


def run_watchdog():
    # initial run
    process_dir(CRASHDUMP_ROOT_PCAT, 'crash', MIN_CRASH_SIZE)
    # process_dir(CRASHDUMP_ROOT_QSTAF, 'crash', MIN_CRASH_SIZE)
    process_dir(RDKBCRASH_ROOT, 'rdkbcrash', MIN_RDKBCRASH_SIZE, scan_root=True)

    # start crash observer in its own instance
    obs_crash = Observer()
    obs_crash.schedule(CrashHandler(), str(CRASHDUMP_ROOT_PCAT), recursive=True)
    obs_crash.start()

    # start crash observer in its own instance
    # obs_crash = Observer()
    # obs_crash.schedule(CrashHandler(), str(CRASHDUMP_ROOT_QSTAF), recursive=True)
    # obs_crash.start()
    # start rdkb observer in separate instance
    obs_rdkb = Observer()
    obs_rdkb.schedule(RdkbHandler(), str(RDKBCRASH_ROOT), recursive=True)
    obs_rdkb.start()

    log.info("Watching crash and RDKB directories in parallel…")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        obs_crash.stop()
        obs_rdkb.stop()
        obs_crash.join()
        obs_rdkb.join()
        log.info("Watchers stopped.")


if __name__ == "__main__":
    run_watchdog()
