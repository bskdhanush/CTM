
import FzHandler
from JsonHandler import load_prov_json,save_meta_json,load_meta_json
import AutoDownloader 
from EndToEndDevProvsioningController import *
from GUI_modules import MetaMpssDownloadSubFrame
import re
from pathlib import Path
from CrashHandler import get_operator



def get_downloaded_list():
    
    downloaded_meta = load_meta_json()
    return downloaded_meta

def add_data():
  data = list(get_downloaded_list())
  print(type(data))
  data.append("5")
  save_meta_json(data)


def check_for_new_meta(device_name):

    if device_name==None or device_name=="":
        cfg=load_meta_json()
        device_name=cfg["CPE_META_MPSS"]["meta"]
        print(f"dev_name:{device_name}")

        if device_name=="UNKNOWN":
            return



def replace_ADB_TC_ondevice(TC_ondevice_path: Path, extracted_folder, device_type) -> None:
    operator = "TMO"
    if not TC_ondevice_path.exists():
        raise FileNotFoundError(f"Extracted folder not found: {TC_ondevice_path}")
    
    content = TC_ondevice_path.read_text()
    ADBId = "12344"  # Consider passing this as a parameter
    if not ADBId:
        return 
    
    if operator == 'VZW':
        print(operator + " in vzw loop")
        
        # Uncomment the specific updateWWANProfile line
        content = re.sub(r"//updateWWANProfile\s+0\s+0:1\s+2\s+3\s+0", 
                        "updateWWANProfile 0 0:1 2 3 0", 
                        content)
        
    elif operator == "TMO":
        print(operator)
        content = re.sub(r"updateWWANProfile\s+0\s+0:1\s+2\s+3\s+0", 
                        "//updateWWANProfile 0 0:1 2 3 0", 
                        content)
        print(content)
    else:
        return

    Replacment_sting = "QSTAF_MLO_" + ADBId
    updated_content = re.sub(r"QSTAF_MLO_\w+", Replacment_sting, content)
    TC_ondevice_path.write_text(updated_content)
   
if __name__ == "__main__":
    replace_ADB_TC_ondevice(
        Path(r'D:\Assignments\TC_ondevice.txt'),
        r"C:\CTM\DAPP\Kobuk_CPE_1.1_v1.1.7_1", 
        'kobuk'
    )
 
  