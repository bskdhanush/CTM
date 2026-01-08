import os
from WifiController import get_adb_id
from Constants import PROV_LOG_DIR
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

list_messages=["META loading completed on Device" ,
               "IMEI getting written",
                "MPSS loading completed on Device",
                "QCN loading completed on Device",
                "MBN loading completed on Device",
                "NV loading completed on Device"]

def check_Install_status(option):
    
    if "2" in option:
        print("Checking for meta install")
        check_the_text_file(list_messages[0])
       
    if "3" in option:
        print("Checking for mpss install")
        check_the_text_file(list_messages[1])
    if "4" in option:
        print("checking for IMEI Write")
        check_the_text_file(list_messages[2])
    if "5" in option:
        print("checking for QCN Install")
        check_the_text_file(list_messages[3])
    if "6" in option:
        print("checking for MBN install")
        check_the_text_file(list_messages[4])
    if "7" in option:
        print("checking for NV Install")
        check_the_text_file(list_messages[5])
        
def check_the_text_file(default_msg:str):
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
            #print(content)
            if not default_msg in content:
                words = default_msg.split()
                result = " ".join(words[:2])
                messagebox.showerror("Failure", f"{result} failed! \nPlease Check")
                
    except:
        print("NO such file")
            
        
    
    