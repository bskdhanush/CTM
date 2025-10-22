import os
import json
from datetime import datetime, timedelta


from Constants import CTM_META_DIR,META_JSON_FILE,CTM_BASE_DIR
from FzHandler import list_files,download_file
from JsonHandler import load_prov_json,save_meta_json,load_meta_json
from CrashHandler import set_naming_convention_from_crash_rename_csv

def get_downloaded_lsit(): 
    cfg =(load_meta_json())
    downloaded_meta=list(cfg["Meta"])
    return downloaded_meta ,cfg

def save_downloaded_meta(file_name):
    downloaded_meta,cfg= get_downloaded_lsit() 
    if file_name not in downloaded_meta:  # optional: avoid duplicates
        downloaded_meta.append(file_name)
        cfg.update({"Meta":downloaded_meta})
        save_meta_json(cfg)


def checK_for_new_meta(device_name):
    
    files_list=list_files(device_name, "Meta",sub_sting="") #Meta eables only auto doownload for Meta only 
    print(f"found LISt: {files_list}" )

    # Time threshold for 24 hours
    now = datetime.now()
    time_24hrs_ago = now - timedelta(hours=24)

    for file_info in files_list:
        file_name = file_info["name"]
        file_size = file_info["size"]
        file_mtime = datetime.strptime(file_info["mtime"], "%Y-%m-%d %H:%M:%S")

        d_list,cfg=get_downloaded_lsit()


        print("Checking")
        if file_name in d_list:
            print(f"Skipping {file_name}")
            continue  # skip already downloaded

        if file_size >= 1.5 * 1024**3 and file_mtime > time_24hrs_ago:
            try:
                print("downloading meta")
                # here file_info is DICT so have to convrt to string 
                download_file(file_name,load_prov_json().get("Meta_path"))
                save_downloaded_meta(file_name)
            except Exception as e:
                print("Download failed, not saving metadata:", e)
  

def checK_for_new_CSV():
    files_list=list_files("CrashRenamingMetaInfo.csv", "Meta",sub_sting="") # here Meta we can search whole incomming
    d,cfg= get_downloaded_lsit()

    if files_list[0]["mtime"]> cfg["CSV"]:
        print(files_list[0]["mtime"],cfg["CSV"])
        try:
            download_file(files_list[0]["name"],CTM_BASE_DIR)
            cfg.update({"CSV":files_list[0]["mtime"]})
            save_meta_json(cfg)
            set_naming_convention_from_crash_rename_csv()
        except Exception as e:
             print("CSV Download failed", e)
  
