
from datetime import datetime, timedelta

from Constants import CTM_BASE_DIR
import FzHandler 
from JsonHandler import load_prov_json,save_meta_json,load_meta_json
from CrashHandler import set_naming_convention_from_crash_rename_csv
from GUI_modules import CrashForecastPage



def get_downloaded_list():
    """Load downloaded files from JSON"""
    cfg = (load_meta_json())
    downloaded_meta = cfg.get("Meta", {})
    
    return downloaded_meta, cfg



def save_downloaded_meta(file_name, file_mtime):
    """Save file name with modification time"""
    downloaded_meta, cfg = get_downloaded_list()
    
    # Update Meta dictionary with filename and mtime
    if "Meta" not in cfg:
        cfg["Meta"] = {}
    
    cfg["Meta"][file_name] = file_mtime
    
    save_meta_json(cfg)



def check_for_new_meta(device_name, download_status_label_update):

    if device_name==None or device_name=="":
        cfg=load_meta_json()
        device_name=cfg["CPE_META_MPSS"]["meta"]

        if device_name=="UNKNOWN":
            return

    
    files_list = FzHandler.list_files(device_name, "Meta", "")  # Meta enables only auto download for Meta only 
    #print(f"found LISt: {files_list}")

    # Time threshold for 24 hours
    now = datetime.now()
    time_24hrs_ago = now - timedelta(hours=24)

    for file_info in files_list:
        file_name = file_info["name"]
        file_size = file_info["size"]
        file_mtime = datetime.strptime(file_info["mtime"], "%Y-%m-%d %H:%M:%S")

        downloaded_meta, cfg = get_downloaded_list()

        print(f"Checking {file_name , file_mtime}")
        
        # Check if file is already in downloaded list
        if file_name in downloaded_meta:
            stored_mtime_str = downloaded_meta[file_name]
            stored_mtime = datetime.strptime(stored_mtime_str, "%Y-%m-%d %H:%M:%S")
            
            # If modification time is the same or older, skip
            if file_mtime <= stored_mtime:
                print(f"Skipping {file_name} (same or older version)")
                continue
            else:
                # File has newer modification time, proceed to re-download
                print(f"File {file_name} has been updated, re-downloading")
        
        # Download conditions: file NOT in list OR file has newer mtime
        # Additional requirements: file size >= 1.5 GB AND uploaded in last 24 hours
        if file_size >= 1.5 * 1024**3 and file_mtime > time_24hrs_ago:
            try:
                print(f"Downloading meta: {file_name}")
                #download_file(remote_filename, local_dir, PageName:str, download_status_label_update, timestamp)
                FzHandler.download_file(file_name, load_prov_json().get("Meta_path"),"Meta",download_status_label_update, file_info["mtime"])
                # Save with string format of mtime
                #save_downloaded_meta(file_name, file_info["mtime"])
            except Exception as e:
                print(f"Download failed for {file_name}, not saving metadata:", e)
  

def check_for_new_csv(download_status_label_update):
    try:
        files_list = FzHandler.list_files("", "Meta","CrashRenamingMetaInfo.csv") # here Meta we can search whole incomming
        d, cfg = get_downloaded_list()
    except Exception as e:
        print(f'Exception during list_files in check_for_new_csv: {e}')
    if files_list:
        print(f"serverTime stamp :{files_list[0]["mtime"]} \n json time stamp:{cfg["CSV"]}")

        #print(files_list)
        if files_list[0]["mtime"]> cfg["CSV"]:
            print(files_list[0]["mtime"],cfg["CSV"])
            try:
                #download_file(remote_filename, local_dir, PageName:str, download_status_label_update, timestamp)
                FzHandler.download_file(files_list[0]["name"],CTM_BASE_DIR, "",download_status_label_update,"")
            except Exception as e:
                print(f"Exception during download_file: {e}")
            else:
                try:
                    cfg.update({"CSV":files_list[0]["mtime"]})
                    save_meta_json(cfg)
                    set_naming_convention_from_crash_rename_csv(CrashForecastPage.log_box)
                except Exception as e:
                    print(f"Exception during set_naming_convention_from_crash_rename_csv: {e}")