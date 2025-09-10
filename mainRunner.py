import subprocess
import time
import WifiController 
import MainController

command = ['timeout /t 1']
if __name__ == "__main__":
       # subprocess.Popen(command, shell=True)
        WifiController.run_command(command)
        
