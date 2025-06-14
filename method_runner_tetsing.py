from datetime import datetime
from handler import GetLatest_dir as gd
from pathlib import Path

def main():
    normalroot = Path(r"C:\QSTAF\crashDump")
    rdkcrashroot=Path(r"C:\Temp\automation\QSTAF\QSTAFpy\appcrash_logs")
    depth = 1
    tracker_file = Path(r"C:\QSTAF\app_config.json")
    gd.get_latest_dir_update_json(normalroot,depth,tracker_file,"normal")
    gd.get_latest_dir_update_json(rdkcrashroot,0,tracker_file,"rdkb")


if __name__ == "__main__":
    main()