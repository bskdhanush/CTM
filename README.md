To build the exe: pyinstaller main_controller.py  --name QSTAF_Tool   --noconfirm --onefile --console

app_json format:    
{
    "aws_scheduler_enabled": true,
    "crash_day_counter": 0,
    "crash_night_counter": 0,
    "last_crash_base": "C:\\QSTAF\\crashDump\\test5",
    "last_crash_day_reset": null,
    "last_crash_night_reset": null,
    "last_rdkbcrash_base": "C:\\Temp\\automation\\QSTAF\\QSTAFpy\\appcrash_logs",
    "last_rdkbcrash_day_reset": null,
    "last_rdkbcrash_night_reset": null,
    "previous_crash_dir": null,
    "previous_rdkbcrash_dir": "C:\\Temp\\automation\\QSTAF\\QSTAFpy\\appcrash_logs\\123234 - Copy - Copy - Copy - Copy - Copy",
    "rdkbcrash_day_counter": 0,
    "rdkbcrash_night_counter": 0
}
