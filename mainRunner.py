import subprocess
import time
import WifiController 
import MainController
import FzHandler
from GUI_modules import DeviceConfigurationPage,CrashForecastPage
server_upload_path="CPE-Markets/LV/LV-CPE__Aniket_Pinnacles.LE.2.2-00060-EBOOT.CPE.WKK-1-DE70c9-00046_03032025_TMO_1_TDC000022NYQ_Ethernet_DRI.7z"
loaclfile_path="D:/work/LV-CPE__Aniket_Pinnacles.LE.2.2-00060-EBOOT.CPE.WKK-1-DE70c9-00046_03032025_TMO_1_TDC000022NYQ_Ethernet_DRI.7z"

if __name__ == "__main__":
    FzHandler.file_upload(loaclfile_path,server_upload_path)
  
  