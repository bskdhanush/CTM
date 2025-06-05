# ── crashdump_utils.py ─────────────────────────────────────────────────────────
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, time, timedelta
from typing import Optional, Tuple

# ───────────────────────── CONFIGURATION ──────────────────────────────────
CRASHDUMP_ROOT = Path(r"C:\QSTAF\crashDump")
COUNTER_FILE   = CRASHDUMP_ROOT / "crash_counters.json"

DAY_START  = time(9, 0)       # 09:00
DAY_END    = time(18, 0)      # 18:00  (exclusive)
NIGHT_END  = time(8, 45)      # 08:45  (exclusive) – night shift ends
# ──────────────────────────────────────────────────────────────────────────


# ── helpers to locate newest folders ──────────────────────────────────────
def newest_child(dir_path: Path) -> Optional[Tuple[Path, datetime]]:
    """Return newest *direct* child directory of *dir_path* (path, mtime)."""
    try:
        child = max((p for p in dir_path.iterdir() if p.is_dir()),
                    key=lambda p: p.stat().st_mtime, default=None)
        return (child,
                datetime.fromtimestamp(child.stat().st_mtime)) if child else None
    except FileNotFoundError:
        return None


def newest_top_level(root: Path = CRASHDUMP_ROOT) -> Optional[Tuple[Path, datetime]]:
    """Newest folder directly under CRASHDUMP_ROOT (path, mtime) or None."""
    return newest_child(root)


# ── ShiftCounters ─────────────────────────────────────────────────────────
class ShiftCounters:
    """Tracks day/night counts; resets at 09 :00 / 18 :00 and on new dump root."""
    def __init__(self, store: Path = COUNTER_FILE) -> None:
        self.store = store
        self.day   = 0
        self.night = 0
        self.last_day_reset   = datetime.min
        self.last_night_reset = datetime.min
        self.last_parent_path = ""
        self.last_child_path  = ""
        self.last_child_ts    = datetime.min
        self._load()

    # ── persistence helpers ───────────────────────────────────────────
    def _load(self) -> None:
        if self.store.exists():
            try:
                d = json.loads(self.store.read_text())
                self.day               = d["day"]
                self.night             = d["night"]
                self.last_day_reset    = datetime.fromisoformat(d["last_day_reset"])
                self.last_night_reset  = datetime.fromisoformat(d["last_night_reset"])
                self.last_parent_path  = d["last_parent_path"]
                self.last_child_path   = d["last_child_path"]
                self.last_child_ts     = datetime.fromisoformat(d["last_child_ts"])
                return
            except Exception:
                pass   # Corrupted JSON -> start fresh
        now = datetime.now()
        self.last_day_reset = self.last_night_reset = now
        self._save()

    def _save(self) -> None:
        """Safely write counters to disk; create folder if necessary."""
        try:
            self.store.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.store.with_suffix(".tmp")
            tmp.write_text(json.dumps({
                "day":  self.day,
                "night": self.night,
                "last_day_reset":   self.last_day_reset.isoformat(),
                "last_night_reset": self.last_night_reset.isoformat(),
                "last_parent_path": self.last_parent_path,
                "last_child_path":  self.last_child_path,
                "last_child_ts":    self.last_child_ts.isoformat(),
            }, indent=2))
            tmp.replace(self.store)
        except Exception as exc:
            print(f"[ERROR] Failed to update {self.store}: {exc}")

    # ── shift utilities ───────────────────────────────────────────────
    @staticmethod
    def _is_day(ts: datetime) -> bool:
        return DAY_START <= ts.time() < DAY_END

    @staticmethod
    def _is_night(ts: datetime) -> bool:
        t = ts.time()
        return (t >= DAY_END) or (t < NIGHT_END)

    def _maybe_reset_daily(self) -> None:
        """Reset counters at 09 :00 and 18 :00 each day."""
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

    # ── helper: switch parent ───────────────────────────────────────────
    def _switch_parent(self, parent: Path) -> None:
        """Reset counters & remember the new top‑level dump folder."""
        self.day = self.night = 0
        self.last_parent_path = parent.as_posix()
        self.last_child_path  = ""
        self.last_child_ts    = datetime.min
        self._save()

    # ── public API ─────────────────────────────────────────────────────
    def count_if_new(self, parent: Path, child: Path, child_ts: datetime) -> None:
        """
        Increment counters only if *child* is new and belongs to current shift.
        Also handles parent‑folder switches and writes JSON on change.
        """
        self._maybe_reset_daily()

        # New parent folder?
        if parent.as_posix() != self.last_parent_path:
            self._switch_parent(parent)

        # Same child as last run?
        if child.as_posix() == self.last_child_path and child_ts == self.last_child_ts:
            return

        now = datetime.now()
        incremented = False

        if self._is_day(now):
            if self._is_day(child_ts) and child_ts.date() == now.date():
                self.day += 1
                incremented = True
        elif self._is_night(now):
            night_start = now.date() if now.time() >= DAY_END else (now - timedelta(days=1)).date()
            if self._is_night(child_ts) and child_ts.date() == night_start:
                self.night += 1
                incremented = True

        if incremented:
            self.last_child_path = child.as_posix()
            self.last_child_ts   = child_ts
            self._save()

    def snapshot(self) -> Tuple[int, int]:
        self._maybe_reset_daily()
        return self.day, self.night


# ── MAIN ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    counters = ShiftCounters()

    top = newest_top_level()
    if top is None:
        print("[WARN] No crash‑dump folders found.")
        exit()

    parent_dir, parent_ts = top
    print(f"[INFO] Newest dump dir   -> {parent_dir.name} "
          f"({parent_ts:%Y-%m-%d %H:%M:%S})")

    child = newest_child(parent_dir)
    if child is None:
        print("       (no sub folders yet)")
        counters._switch_parent(parent_dir)       # ensure JSON reflects new root
    else:
        child_dir, child_ts = child
        print(f"       Newest sub folder -> {child_dir.name} "
              f"({child_ts:%Y-%m-%d %H:%M:%S})")
        counters.count_if_new(parent_dir, child_dir, child_ts)

    day_cnt, night_cnt = counters.snapshot()
    print(f"       Counters          -> day={day_cnt}  night={night_cnt}")
