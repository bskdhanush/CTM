To build the exe with out cmd : pyinstaller --onefile MainController.py --name CTM --noconfirm --windowed --icon=logs/logo.ico --add-data "config;config" --add-data "GUI_modules;GUI_modules"

To build the exe with cmd : pyinstaller --onefile MainController.py --name CTM --noconfirm --console --icon=logs/logo.ico --add-data "config;config" --add-data "GUI_modules;GUI_modules" --add-data ".env;.env" --add-data "SSH_Modules;SSH_Modules" --hidden-import=ssh2


***** USE the follwoing to create EXE ******
pyinstaller --onefile MainController.py --name CTM --noconfirm --console --icon=logs/logo.ico --add-data "config;config" --add-data "GUI_modules;GUI_modules" --hidden-import=ssh2 --hidden-import=ssh2.agent --hidden-import=ssh2.channel --hidden-import=ssh2.error_codes --hidden-import=ssh2.exceptions --hidden-import=ssh2.fileinfo --hidden-import=ssh2.knownhost --hidden-import=ssh2.listener --hidden-import=ssh2.pkey --hidden-import=ssh2.publickey --hidden-import=ssh2.session --hidden-import=ssh2.sftp --hidden-import=ssh2.sftp_handle --hidden-import=ssh2.statinfo --hidden-import=ssh2.utils 




D:/work/GUI/Quts_tool/myenv_312/Scripts/Activate.ps1    



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
