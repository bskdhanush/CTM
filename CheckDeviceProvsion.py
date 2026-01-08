import os
from WifiController import get_adb_id
from Constants import PROV_LOG_DIR
from datetime import datetime



def check_Install_status(option):
    
    if "2" in option:
        print("Checking for meta install")
        
    if "3" in option:
        print("Checking for mpss install")
        check_the_text_file()
    if "4" in option:
        print("checking for IMEI Write")
        
def check_the_text_file():
    #adb_Id=get_adb_id()
    latest_file=""
    list_of_files = [p for p in PROV_LOG_DIR.iterdir() if p.is_file()]

    if not list_of_files:
        print("No files found in the directory.")
    else:
        latest_file = max(list_of_files, key=os.path.getmtime)
       # print(f"The most recent file is: {latest_file}")
    
    try:
        with open(latest_file, 'r') as f:
            content=f.read()
            print(content)
            if not "MPSS loading completed" in content:
                print ("MPSS not loaded ")
                
    except:
        print("NO such file")
            
        
    
    