# CrashCountController.py

import os
import time
from Threading import *
from pathlib import Path
from datetime import datetime, date
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from queue import Queue


import CrashHandler as CH
import GUI 
from JsonHandler import load_json, save_json
from Constants import DEFAULT_CRASHDUMP,CRASHDUMP_ROOT_PCAT,RDKBCRASH_ROOT,MIN_CRASH_SIZE,MIN_RDKBCRASH_SIZE



# Lock for thread-safe config I/O
_cfg_lock = thread_lock()

def most_recent_subdir(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    subs = [p for p in root.iterdir() if p.is_dir()]
    return max(subs, key=lambda p: p.stat().st_mtime) if subs else None


def get_size(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())

def rest_counter():
    cfg = load_json()
    print("Resetting Counters" )
    cfg["rdkbcrash_counter"] = 0
    cfg["crash_counter"] = 0
    save_json(cfg)

def process_dir(root: Path,
                prefix: str,
                min_size: float,
                scan_root: bool = False) -> tuple[int, int]:
     print("Processing crash dir")
     with _cfg_lock:
        cfg = load_json()

        # state keys
        prev_k      = f"previous_crash_dir"
        if prefix=='crash' or prefix=='normalcrash':
            count_k     = f"crash_counter"
        else : 
            count_k = f"{prefix}_counter" 
        timestamp_k = f"{prefix}_last_timestamp"

        # initialize defaults
        cfg.setdefault(prev_k, None)
        cfg.setdefault(count_k, 0)
        cfg.setdefault(timestamp_k, None)

        # pick directory to scan
        base = root if scan_root else most_recent_subdir(root)
        if base is None:
            return cfg[count_k]

        # load last-seen timestamp (ISO string → datetime)
        last_ts_str = cfg.get(timestamp_k)
        if last_ts_str:
            try:
                prev_ts = datetime.fromisoformat(last_ts_str)
            except ValueError:
                prev_ts = datetime.fromtimestamp(0)
        else:
            prev_ts = datetime.fromtimestamp(0)

        # gather subfolders newer than prev_ts
        candidates: list[tuple[Path, datetime]] = []
        for p in base.iterdir():
            if not p.is_dir():
                continue
            # name must start with four digits
            if not (len(p.name) >= 4 and p.name[:4].isdigit()):
                continue
            if get_size(p) < min_size:
                continue

            mtime = datetime.fromtimestamp(p.stat().st_mtime)
            if mtime <= prev_ts:
                continue
            candidates.append((p, mtime))

        # sort by time (oldest first)
        candidates.sort(key=lambda x: x[1])

        # only count if created today
        today = date.today()
        for p, mtime in candidates:
            if mtime.date() != today:
                continue

            # increment and record
            cfg[count_k]     = cfg.get(count_k, 0) + 1
            cfg[prev_k]      = str(p)
            cfg[timestamp_k] = mtime.isoformat()

            start_thread(CH.crash_forecast,"Crash forecast Thread", daemon=True, crash_path=str(p), timestamp=cfg[timestamp_k])
            print(cfg[count_k])

            GUI.data_queue.put({
                'type': prefix,
                'count': cfg[count_k]
            })
            

        save_json(cfg)
        return cfg[count_k]

def get_latest_play():
    latest_playlist_path=most_recent_subdir(DEFAULT_CRASHDUMP) 
    final_path= os.path.join(str(latest_playlist_path),"CrashLogs")
    return Path(final_path)


class DefaultCrashHandler(FileSystemEventHandler):
    def on_created(self, e):
        final_path= get_latest_play()
        if e.is_directory and e.src_path.startswith(str(final_path)):
            #print(updated_path)
            time.sleep(10)
            n = process_dir(final_path, 'normalcrash', MIN_CRASH_SIZE)
            
class CrashHandler(FileSystemEventHandler):
    def on_created(self, e):
        if e.is_directory and e.src_path.startswith(str(CRASHDUMP_ROOT_PCAT)):
            time.sleep(10)
            n = process_dir(CRASHDUMP_ROOT_PCAT, 'crash', MIN_CRASH_SIZE)

           # log.info("Crash → Day:%d Night:%d", d, n)

class RdkbHandler(FileSystemEventHandler):
    def on_created(self, e):
        if e.is_directory and e.src_path.startswith(str(RDKBCRASH_ROOT)):
            time.sleep(40)
            n = process_dir(
                RDKBCRASH_ROOT, 'rdkbcrash', MIN_RDKBCRASH_SIZE, scan_root=True
            )
            #log.info("RDKB  → Day:%d Night:%d", d, n)


def run_watchdog():
    # initial run
    final_path= get_latest_play()
    process_dir(final_path,'normalcrash', MIN_CRASH_SIZE)
    process_dir(CRASHDUMP_ROOT_PCAT, 'crash', MIN_CRASH_SIZE)
    process_dir(RDKBCRASH_ROOT, 'rdkbcrash', MIN_RDKBCRASH_SIZE, scan_root=True)

    # start crash observer in its own instance
    obs_dcrash = Observer()
    obs_dcrash.schedule(DefaultCrashHandler(), str(DEFAULT_CRASHDUMP), recursive=True)
    obs_dcrash.start()

    obs_crash = Observer()
    obs_crash.schedule(CrashHandler(), str(CRASHDUMP_ROOT_PCAT), recursive=True)
    obs_crash.start()

    obs_rdkb = Observer()
    obs_rdkb.schedule(RdkbHandler(), str(RDKBCRASH_ROOT), recursive=True)
    obs_rdkb.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        obs_dcrash.stop()
        obs_crash.stop()
        obs_rdkb.stop()
        obs_dcrash.join()
        obs_crash.join()
        obs_rdkb.join()


if __name__ == "__main__":
    run_watchdog()
    