# ── dual_watchdog.py ───────────────────────────────────────────────────────────
from __future__ import annotations

import threading, time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler,EVENT_TYPE_CREATED,EVENT_TYPE_MOVED

import crash_count_controller as gd # your get_latest_dir_update_json() lives here


# ── base handler ──────────────────────────────────────────────────────────────
class _BaseHandler(FileSystemEventHandler):
    """
    Common logic for both folder watchers.
    Sub-classes pass all parameters to the constructor, so the attributes
    exist *and* static checkers (Pylance, mypy…) stay happy.
    """
    _DEBOUNCE_SEC = 2  # seconds to wait so the OS finishes writing/moving files

    def __init__(
        self,
        *,
        root: Path,
        depth: int,
        section_key: str,
        tracker_file: Path,
    ) -> None:
        super().__init__()
        self.root = root
        self.depth = depth
        self.section_key = section_key
        self.tracker_file = tracker_file

    # ── watchdog callback -----------------------------------------------------
    def on_any_event(self, event):
        if (
            not event.is_directory
            or event.event_type not in (EVENT_TYPE_CREATED, EVENT_TYPE_MOVED)
        ):
            return

        # off-load the real work so the observer thread never blocks
        threading.Thread(target=self._process_change, daemon=True).start()

    # ── heavy work (runs in its own short-lived thread) -----------------------
    def _process_change(self):
        delay=120 if self.section_key.lower() == "normal" else 60
        print(delay)
        try:
            time.sleep(delay)
            gd.get_latest_dir_update_json(
                self.root,
                self.depth,
                self.tracker_file,
                self.section_key,
            )
        except Exception as exc:  # noqa: BLE001  (keep observer alive)
            print(f"[ERROR] {self.section_key}-handler: {exc}")


# ── concrete handlers ---------------------------------------------------------
class NormalHandler(_BaseHandler):
    def __init__(self, root: Path, depth: int, tracker_file: Path) -> None:
        super().__init__(
            root=root,
            depth=depth,
            section_key="normal",
            tracker_file=tracker_file,
        )


class RdkbHandler(_BaseHandler):
    def __init__(self, root: Path, tracker_file: Path) -> None:
        super().__init__(
            root=root,
            depth=0,
            section_key="rdkb",
            tracker_file=tracker_file,
        )


# ── helper --------------------------------------------------------------------
def _start_observer(path: Path, handler: FileSystemEventHandler) -> Observer: # type: ignore
    obs = Observer()
    obs.schedule(handler, str(path), recursive=True)
    obs.start()          # runs in its own thread
    return obs


# ── main ----------------------------------------------------------------------
def main() -> None:
    normalroot   = Path(r"C:\QSTAF\crashDump")
    rdkcrashroot = Path(r"C:\Temp\automation\QSTAF\QSTAFpy\appcrash_logs")
    depth        = 1
    tracker_file = Path(r"C:\QSTAF\app_config.json")

    # initial catch-up so counters are correct before live watching
    #gd.get_latest_dir_update_json(normalroot,   depth, tracker_file, "normal")
    #gd.get_latest_dir_update_json(rdkcrashroot, 0,    tracker_file, "rdkb")

    # two fully independent observers
    normal_obs = _start_observer(normalroot,   NormalHandler(normalroot, depth, tracker_file))
    rdkb_obs   = _start_observer(rdkcrashroot, RdkbHandler(rdkcrashroot, tracker_file))

    print("[INFO] Watchdogs running …  (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[INFO] Stopping observers …")
        normal_obs.stop(); rdkb_obs.stop()
        normal_obs.join(); rdkb_obs.join()

# gd.reset_all_counters(tracker_file)
if __name__ == "__main__":
    main()

   # gd.reset_all_counters(tracker_file)
