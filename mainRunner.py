
import FzHandler


from JsonHandler import load_prov_json,save_meta_json,load_meta_json
from AutoDownloader import checK_for_new_meta ,checK_for_new_CSV
from EndToEndDevProvsioningController import *





def get_downloaded_lsit():
    
    downloaded_meta = load_meta_json()
    return downloaded_meta

def add_data():
  data = list(get_downloaded_lsit())
  print(type(data))
  data.append("5")
  save_meta_json(data)


if __name__ == "__main__":
  cofig= get_data_Meta_Mpss_txt()
  print(cofig)
 
  