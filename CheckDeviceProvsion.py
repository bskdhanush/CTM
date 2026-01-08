from WifiController import get_adb_id
from Constants import PROV_LOG_DIR



def check_Install_status(option):
    adb_Id=get_adb_id()
    if "2" in option:
        print("Checking for meta install")
    if "3" in option:
        print("Checking for mpss install")
    if "4" in option:
        print("checking for IMEI Write")
        
def check_the_text_file():
    PROV_LOG_DIR
    
        
    
    