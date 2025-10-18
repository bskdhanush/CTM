import subprocess
import time
import WifiController 
import MainController
import KillProcess
import FzHandler
from GUI_modules import DeviceConfigurationPage,CrashForecastPage
server_upload_path="CPE-Markets/LV/test_smi upload.7z"
loaclfile_path="D:/work/test_smi upload.7z"
if __name__ == "__main__":
   subprocess.call("taskkill /F /IM adb.exe", shell=True)
    
  