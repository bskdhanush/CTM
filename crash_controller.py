# ── GetLatest_dir.py ───────────────────────────────────────────────────────────
from pathlib import Path
from datetime import datetime, time, timedelta
from typing import Iterable, Literal, Optional, Tuple
import json

# ──────────────────────────────────────────────────────────────────────────────
#  Helpers for latest-folder discovery
# ──────────────────────────────────────────────────────────────────────────────
def get_latest_folder_by_depth(root: Path, depth: int) -> Optional[tuple[Path, str]]:
    """
    Return the latest folder at *depth* below *root*.
    depth = 0 → latest sub-folder inside *root* (not root itself)
    """
    if not root.exists() or depth < 0:
        return None

    subdirs = [d for d in root.iterdir() if d.is_dir()]
    if not subdirs:
        return None

    latest_sub = max(subdirs, key=lambda d: d.stat().st_mtime)
    if depth == 0:
        ts = datetime.fromtimestamp(latest_sub.stat().st_mtime)
        return latest_sub, ts.strftime("%Y-%m-%d %H:%M:%S")

    return get_latest_folder_by_depth(latest_sub, depth - 1)


# ──────────────────────────────────────────────────────────────────────────────
#  Rules for counting
# ──────────────────────────────────────────────────────────────────────────────
DAY_START  = time(9, 0)
DAY_END    = time(18, 0)          # inclusive
NIGHT_END  = time(8, 59)          # inclusive
NIGHT_START = time(18, 1)         # first minute after the day window


def classify_window(ts: datetime, today: datetime.date) -> Literal["day", "night", None]: # type: ignore
    """
    Return "day", "night", or None for the folder timestamp *ts* according to:
      • day   -> ts.date() == today   and 09:00 ≤ ts.time() ≤ 18:00
      • night -> (ts.date() == today     and ts.time() ≥ 18:01)  OR
                 (ts.date() == today+1   and ts.time() ≤ 08:59)
    """
    if ts.date() == today:
        if DAY_START <= ts.time() <= DAY_END:
            return "day"
        elif ts.time() >= NIGHT_START:
            return "night"
    elif ts.date() == today + timedelta(days=1) and ts.time() <= NIGHT_END:
        return "night"
    return None


# ──────────────────────────────────────────────────────────────────────────────
#  Folder-filtering helpers
# ──────────────────────────────────────────────────────────────────────────────
def get_unseen_folders_since(
    root: Path,
    last_seen_datetime_str: str,
    crash_type: str,
) -> list[tuple[Path, float, str]]:
    """
    Return folders newer than *last_seen_datetime_str* that:
      • start with 4 digits
      • meet the size threshold (2 MB for normal, 5 MB for rdkb)
    """
    if not root.exists() or not root.is_dir():
        return []

    try:
        last_seen_dt = datetime.strptime(
            last_seen_datetime_str, "%Y-%m-%d %H:%M:%S.%f"
        )
    except ValueError:
        last_seen_dt = datetime.fromtimestamp(0)

    min_sz = 2 * 1024**2 if crash_type.lower() == "normal" else 5 * 1024**2
    unseen: list[tuple[Path, float, str]] = []

    for p in root.iterdir():
        if p.is_dir() and p.name[:4].isdigit() and not p.name.endswith(".zip"):
            mtime = p.stat().st_mtime
            m_dt  = datetime.fromtimestamp(mtime)
            if m_dt <= last_seen_dt:
                continue
            folder_sz = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
            if folder_sz < min_sz:
                continue
            unseen.append((p, mtime, m_dt.strftime("%Y-%m-%d %H:%M:%S.%f")))

    return sorted(unseen, key=lambda x: x[1])


# ──────────────────────────────────────────────────────────────────────────────
#  Counter-reset utilities
# ──────────────────────────────────────────────────────────────────────────────
def should_reset_24(last_reset_str: str, now: datetime, reset_hour: int) -> bool:
    """
    Return True once per 24 h window starting at *reset_hour*.
    """
    try:
        last_reset = datetime.strptime(last_reset_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        last_reset = datetime.fromtimestamp(0)

    today_reset = now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
    return now >= today_reset and last_reset < today_reset


def _maybe_reset_counters(
    dir_cnt: int,
    ovn_cnt: int,
    last_day_reset: str,
    last_night_reset: str,
    now: datetime,
) -> Tuple[int, int, str, str]:
    """
    Apply 09:00 / 18:00 resets if needed and return updated counters + timestamps.
    """
    if should_reset_24(last_day_reset, now, 9):
        dir_cnt = 0
        last_day_reset = now.strftime("%Y-%m-%d %H:%M:%S.%f")

    if should_reset_24(last_night_reset, now, 18):
        ovn_cnt = 0
        last_night_reset = now.strftime("%Y-%m-%d %H:%M:%S.%f")

    return dir_cnt, ovn_cnt, last_day_reset, last_night_reset

# ──────────────────────────────────────────────────────────────────────────────
#  Rest all counters
# ──────────────────────────────────────────────────────────────────────────────
def reset_all_counters(
    tracker_file: Path,
    crash_types: Optional[Iterable[str]] = None,
    stamp_now: bool = True,
) -> None:
    """
    Set both counters to 0 for every crash-type in *tracker_file*.

    Parameters
    ----------
    tracker_file : Path
        Path to the JSON tracker.
    crash_types : Iterable[str] | None
        • None  → reset ALL crash-types present.  
        • list → reset only those keys (e.g. ["normal", "rdkb"]).
    stamp_now : bool
        If True, overwrite `last_reset_day` & `last_reset_night` with
        the current timestamp; otherwise leave them unchanged.
    """
    if not tracker_file.exists():
        print(f"[WARN] {tracker_file} not found — nothing to reset.")
        return

    try:
        data = json.loads(tracker_file.read_text())
    except json.JSONDecodeError:
        print(f"[ERROR] Tracker JSON malformed — aborting reset.")
        return

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    targets = crash_types if crash_types is not None else data.keys()

    for ctype in targets:
        node = data.get(ctype)
        if node is None:
            print(f"[INFO] crash-type '{ctype}' not present — skipped.")
            continue
        node["DIR_Counter"] = 0
        node["OVN_Counter"] = 0
        if stamp_now:
            node["last_reset_day"]   = now_str
            node["last_reset_night"] = now_str

    tracker_file.write_text(json.dumps(data, indent=2))
    print(f"[INFO] Counters reset for: {', '.join(targets)}")


# ──────────────────────────────────────────────────────────────────────────────
#  JSON tracker helpers
# ──────────────────────────────────────────────────────────────────────────────
def _load_tracker_node(tracker_file: Path, crash_type: str) -> dict:
    """
    Ensure *tracker_file* exists and return its crash-type node.
    """
    if not tracker_file.exists():
        tracker_file.parent.mkdir(parents=True, exist_ok=True)
        tracker_file.write_text("{}")

    try:
        data = json.loads(tracker_file.read_text())
    except json.JSONDecodeError:
        data = {}
    if crash_type not in data:
        data[crash_type] = {
            "last_seen_datetime": "1970-01-01 00:00:00.000000",
            "DIR_Counter": 0,
            "OVN_Counter": 0,
            "last_reset_day": "1970-01-01 00:00:00.000000",
            "last_reset_night": "1970-01-01 00:00:00.000000",
        }
    return data[crash_type]


def _persist_tracker(
    tracker_file: Path,
    crash_type: str,
    node: dict,
) -> None:
    try:
        data = json.loads(tracker_file.read_text())
    except json.JSONDecodeError:
        data = {}
    data[crash_type] = node
    tracker_file.write_text(json.dumps(data, indent=2))


# ──────────────────────────────────────────────────────────────────────────────
#  Main entry -- update counters & JSON
# ──────────────────────────────────────────────────────────────────────────────
def get_latest_dir_update_json(
    root: Path,
    depth: int,
    tracker_file: Path,
    crash_type: str,
) -> None:
    """
    Update *tracker_file* for *crash_type* based on unseen folders under *root*.
    """
    now          = datetime.now()
    today        = now.date()
    node         = _load_tracker_node(tracker_file, crash_type)

    # ── 0. 24-hour resets ────────────────────────────────────────────────
    dir_cnt, ovn_cnt, last_day_reset, last_night_reset = _maybe_reset_counters(
        node["DIR_Counter"],
        node["OVN_Counter"],
        node["last_reset_day"],
        node["last_reset_night"],
        now,
    )

    # ── 1. Folder discovery ──────────────────────────────────────────────
    first_child = get_latest_folder_by_depth(root, depth)
    if not first_child:
        print("[WARN] No first-child folder found.")
        return

    first_child_path, _ = first_child
    parent_path = first_child_path.parent

    unseen = get_unseen_folders_since(
        parent_path,
        node["last_seen_datetime"],
        crash_type,
    )

    # ── 2. Classify & count ───────────────────────────────────────────────
    for folder, ts, _ in unseen:
        ts_dt = datetime.fromtimestamp(ts)
        bucket = classify_window(ts_dt, today)
        if bucket == "day":
            dir_cnt += 1
        elif bucket == "night":
            ovn_cnt += 1
        # else: outside the defined windows – recorded but not counted

    # ── 3. Persist tracker ────────────────────────────────────────────────
    if unseen:
        latest_folder, latest_ts, _ = unseen[-1]
        node["last_seen_datetime"] = datetime.fromtimestamp(
            latest_ts
        ).strftime("%Y-%m-%d %H:%M:%S.%f")
        node["last_seen_folder"]   = latest_folder.name
    # even if *unseen* is empty we still record path & counter resets
    node["first_child_path"] = str(parent_path)
    node["DIR_Counter"]      = dir_cnt
    node["OVN_Counter"]      = ovn_cnt
    node["last_reset_day"]   = last_day_reset
    node["last_reset_night"] = last_night_reset

    _persist_tracker(tracker_file, crash_type, node)
    print(f"[INFO] Tracker updated for '{crash_type}'. "
          f"Dir={dir_cnt}, Night={ovn_cnt}")
