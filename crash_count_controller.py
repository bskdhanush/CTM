# ── crashdump_utils.py ─────────────────────────────────────────────────────────
"""
Single shot use:   python crashdump_utils.py
Watch mode:        python crashdump_utils.py --watch   (needs `watchdog`)
All logic lives in this file so a single PyInstaller build can bundle it.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, time as dtime, timedelta
from pathlib import Path
from typing import Optional, Tuple
import watchdog

import sys
if hasattr(sys.stdout, "reconfigure"):        # Py ≥ 3.7
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except ValueError:
        pass 
# ── optional watchdog imports (lazy loaded) ────────────────────────────────
try:
    from watchdog.observers import Observer  # type: ignore
    from watchdog.events import (
        FileSystemEventHandler,
        EVENT_TYPE_CREATED,
    )  # type: ignore
except ImportError:  # not installed → None
    Observer = FileSystemEventHandler = EVENT_TYPE_CREATED = None  # type: ignore

# ───────────────────────── CONFIGURATION ──────────────────────────────────
CRASHDUMP_ROOT  = Path(r"C:\QSTAF")
COUNTER_FILE    = CRASHDUMP_ROOT / "app_config.json"
CONFIG_FILE  = os.path.join(CRASHDUMP_ROOT, "app_config.json")

DAY_START       = dtime(9, 0)
DAY_END         = dtime(18, 0)                        # exclusive
NIGHT_END       = dtime(8, 45)                        # exclusive
SIZE_THRESHOLD  = int(1.5 * 1024**3)                  # 1.5 GB
# ──────────────────────────────────────────────────────────────────────────


# ── helper: newest directory in a folder ──────────────────────────────────
def newest_child(parent: Path) -> Optional[Tuple[Path, datetime]]:
    try:
        sub = max(
            (p for p in parent.iterdir() if p.is_dir()),
            key=lambda p: p.stat().st_mtime,
            default=None,
        )
        if sub:
            return sub, datetime.fromtimestamp(sub.stat().st_mtime)
    except FileNotFoundError:
        pass
    return None


def newest_top_level(root: Path = CRASHDUMP_ROOT) -> Optional[Tuple[Path, datetime]]:
    return newest_child(root)


# ── name / size gates ─────────────────────────────────────────────────────
def is_valid_child(p: Path) -> bool:
    name = p.name
    return len(name) >= 4 and name[:4].isdigit() and not name.lower().endswith(".zip")


def dir_size(path: Path) -> int:
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except FileNotFoundError:
                pass
    return total

def load_day_count() -> int:
    """Return the current 'day' counter (0 if file or key is missing)."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("day", 0)
    except FileNotFoundError:
        # file hasn't been created yet
        return 0
    except (json.JSONDecodeError, PermissionError) as exc:
        print(f"[WARN] Could not read {CONFIG_FILE} ({exc}); defaulting to 0")
        return 0

def valid_children(parent: Path, after: datetime) -> list[Tuple[Path, datetime]]:
    """All sub folders newer than *after* that pass name + size rules."""
    out: list[Tuple[Path, datetime]] = []
    for p in parent.iterdir():
        if not is_valid_child(p):
            continue
        ts = datetime.fromtimestamp(p.stat().st_mtime)
        if ts <= after:
            continue                           # already processed
        if dir_size(p) >= SIZE_THRESHOLD:
            out.append((p, ts))
    out.sort(key=lambda x: x[1])               # oldest → newest
    return out


# ── ShiftCounters ─────────────────────────────────────────────────────────
class ShiftCounters:
    """Day/night counters with auto reset and persistence."""

    def __init__(self, store: Path = COUNTER_FILE) -> None:
        self.store = store
        self.day = self.night = 0
        self.last_day_reset = datetime.min
        self.last_night_reset = datetime.min
        self.last_parent_path = ""
        self.last_child_path = ""
        self.last_child_ts = datetime.min
        self._load()

    # ---------- persistence -------------------------------------------
    def _load(self) -> None:
        if self.store.exists():
            try:
                d = json.loads(self.store.read_text())
                self.day = d["day"]
                self.night = d["night"]
                self.last_day_reset = datetime.fromisoformat(d["last_day_reset"])
                self.last_night_reset = datetime.fromisoformat(d["last_night_reset"])
                self.last_parent_path = d["last_parent_path"]
                self.last_child_path = d["last_child_path"]
                self.last_child_ts = datetime.fromisoformat(d["last_child_ts"])
                return
            except Exception:
                pass
        now = datetime.now()
        self.last_day_reset = self.last_night_reset = now
        self._save()

    def _save(self) -> None:
        try:
            self.store.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.store.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(
                    {
                        "day": self.day,
                        "night": self.night,
                        "last_day_reset": self.last_day_reset.isoformat(),
                        "last_night_reset": self.last_night_reset.isoformat(),
                        "last_parent_path": self.last_parent_path,
                        "last_child_path": self.last_child_path,
                        "last_child_ts": self.last_child_ts.isoformat(),
                    },
                    indent=2,
                )
            )
            tmp.replace(self.store)
        except Exception as exc:
            print(f"[ERROR] Failed to update {self.store}: {exc}")

    # ---------- shift helpers -----------------------------------------
    @staticmethod
    def _is_day(t: datetime) -> bool:
        return DAY_START <= t.time() < DAY_END

    @staticmethod
    def _is_night(t: datetime) -> bool:
        tt = t.time()
        return tt >= DAY_END or tt < NIGHT_END

    def _maybe_reset_daily(self) -> None:
        now = datetime.now()
        changed = False
        if now.time() >= DAY_START and self.last_day_reset.date() != now.date():
            self.day = 0
            self.last_day_reset = now
            changed = True
        if now.time() >= DAY_END and self.last_night_reset.date() != now.date():
            self.night = 0
            self.last_night_reset = now
            changed = True
        if changed:
            self._save()

    def _switch_parent(self, parent: Path) -> None:
        self.day = self.night = 0
        self.last_parent_path = parent.as_posix()
        self.last_child_path = ""
        self.last_child_ts = datetime.min
        self._save()

    # ---------- public API --------------------------------------------
    def count_if_new(self, parent: Path, child: Path, child_ts: datetime) -> None:
        """Increment counters if child is new and in current shift."""
        self._maybe_reset_daily()

        # parent swap?
        if parent.as_posix() != self.last_parent_path:
            self._switch_parent(parent)

        # already counted?
        if child.as_posix() == self.last_child_path and child_ts == self.last_child_ts:
            return

        now = datetime.now()
        inc = False
        if self._is_day(now):
            if self._is_day(child_ts) and child_ts.date() == now.date():
                self.day += 1
                inc = True
        elif self._is_night(now):
            night_start = (
                now.date() if now.time() >= DAY_END else (now - timedelta(days=1)).date()
            )
            if self._is_night(child_ts) and child_ts.date() == night_start:
                self.night += 1
                inc = True

        if inc:
            self.last_child_path = child.as_posix()
            self.last_child_ts = child_ts
            self._save()

    def snapshot(self) -> Tuple[int, int]:
        self._maybe_reset_daily()
        return self.day, self.night


# ── single shot driver (catch up capable) ────────────────────────────────
def run_once() -> None:
    counters = ShiftCounters()

    top = newest_top_level()
    if top is None:
        print("[WARN] No crash dump folders found.")
        return

    parent_dir, parent_ts = top
    print(
        f"[INFO] Newest dump dir   -> {parent_dir.name} "
        f"({parent_ts:%Y-%m-%d %H:%M:%S})"
    )

    children = valid_children(parent_dir, counters.last_child_ts)

    if not children:
        print("       (no qualifying new sub folders)")
        if parent_dir.as_posix() != counters.last_parent_path:
            counters._switch_parent(parent_dir)
    else:
        for child_dir, child_ts in children:
            sizeGb = dir_size(child_dir) / 1024**3
            print(
                f"       Processing       -> {child_dir.name} "
                f"({child_ts:%Y-%m-%d %H:%M:%S}, {sizeGb:.2f} GB)"
            )
            counters.count_if_new(parent_dir, child_dir, child_ts)

    d, n = counters.snapshot()
    print(f"       Counters          -> day={d}  night={n}")


# ── optional watchdog wrapper (zero polling load) ────────────────────────
class _DumpHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.event_type == EVENT_TYPE_CREATED and event.is_directory:
            try:
                time.sleep(5)   # wait spcified time befor checking the file conditios
                run_once()
                
            except Exception as exc:
                print("[ERROR] handler:", exc)


def run_watch() -> None:
    if Observer is None:
        print("[ERROR] watchdog not installed. Run `pip install watchdog`.")
        return
    obs = Observer()
    obs.schedule(_DumpHandler(), str(CRASHDUMP_ROOT), recursive=True)
    obs.start()
    print("[INFO] Watching", CRASHDUMP_ROOT, "…  (Ctrl C to stop)")
    try:
        while True:
            time.sleep(5) 
    except KeyboardInterrupt:
        obs.stop()
    obs.join()

'''
# ── CLI entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Crash dump day/night counter")
    ap.add_argument("--watch", action="store_true", help="use watchdog instead of polling")
    args = ap.parse_args()

    if args.watch:
        run_watch()
    else:
        run_once()
'''