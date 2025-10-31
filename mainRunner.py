
import FzHandler


from JsonHandler import load_prov_json,save_meta_json,load_meta_json
import AutoDownloader 
from EndToEndDevProvsioningController import *
from GUI_modules import MetaMpssDownloadSubFrame





def get_downloaded_lsit():
    
    downloaded_meta = load_meta_json()
    return downloaded_meta

def add_data():
  data = list(get_downloaded_lsit())
  print(type(data))
  data.append("5")
  save_meta_json(data)


def checK_for_new_meta(device_name):

    if device_name==None or device_name=="":
        cfg=load_meta_json()
        device_name=cfg["CPE_META_MPSS"]["meta"]
        print(f"dev_name:{device_name}")

        if device_name=="UNKNOWN":
            return

if __name__ == "__main__":
    AutoDownloader.checK_for_new_meta("")
    AutoDownloader.checK_for_new_CSV()
  
 
  