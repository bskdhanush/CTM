To build the exe with out cmd : pyinstaller --onefile MainController.py --name CTM --noconfirm --windowed --icon=logs/logo.ico --add-data "config;config" --add-data "GUI_modules;GUI_modules"
To build the exe with cmd : pyinstaller --onefile MainController.py --name CTM --noconfirm --console --icon=logs/logo.ico --add-data "config;config" --add-data "GUI_modules;GUI_modules"


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
