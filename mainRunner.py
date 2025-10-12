import subprocess
import time
import WifiController 
import MainController

from GUI_modules import DeviceConfigurationPage,CrashForecastPage

if __name__ == "__main__":
    mstr=CrashForecastPage.get_magic_string()
    print(len(mstr))
  