import os
import json
from datetime import datetime, timedelta


from Constants import CTM_META_DIR,META_JSON_FILE
from FzHandler import list_files,download_file
from JsonHandler import load_prov_json

def get_downloaded_lsit():
    if os.path.exists(META_JSON_FILE):
        with open(META_JSON_FILE, "r", encoding="utf-8") as f:
            downloaded_meta = json.load(f)
    else:
        downloaded_meta = []
    return downloaded_meta

def save_downloaded_meta(file_name):
    downloaded_meta= get_downloaded_lsit() 
    if file_name not in downloaded_meta:  # optional: avoid duplicates
        downloaded_meta.append(file_name)
    
    with open(META_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(downloaded_meta, f, indent=2)


def checK_for_new_meta(device_name):
    
    files_list=list_files(device_name, "Meta",sub_sting="") #Meta eables only auto doownload for Meta only 

    # Time threshold for 24 hours
    now = datetime.now()
    time_24hrs_ago = now - timedelta(hours=24)

    for file_info in files_list:
        file_name = file_info["name"]
        file_size = file_info["size"]
        file_mtime = datetime.strptime(file_info["mtime"], "%Y-%m-%d %H:%M:%S")

        if file_name in get_downloaded_lsit():
            continue  # skip already downloaded

        if file_size >= 1.5 * 1024**3 and file_mtime > time_24hrs_ago:
            try:
                download_file(file_info,load_prov_json().get(f"Meta_path"))
                save_downloaded_meta(file_name)
            except Exception as e:
                print("Download failed, not saving metadata:", e)
