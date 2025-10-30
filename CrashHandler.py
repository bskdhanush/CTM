import os
import socket
import json
import glob
from pathlib import Path
import re
import subprocess
from datetime import date
import datetime
import pandas as pd
from GUI_modules import CrashForecastPage
from JsonHandler import load_json, load_prov_json, save_prov_json
from EndToEndDevProvsioningController import get_provisioning_base
from WifiController import get_adb_id
from Threading import start_thread
from Constants import CTM_LOGS_DIR, DEFAULT_CRASHDUMP, CRASHDUMP_ROOT_PCAT

seven_zip_path = r'C:\Program Files\7-Zip\7z.exe'

def crash_forecast(crash_path, timestamp):
    if crash_path != "null":
        fst_id = ''
        try:
            crash_forecast_exe_path = get_provisioning_base()
            cfg = load_prov_json()
            fst_id = cfg.get('fst_id', '')
            exe_name = "crash_forecast.exe"
            magic_number = CrashForecastPage.get_magic_string()
            _, _, _, operator, _ = get_naming_convention()
            command = [
                f"{os.path.join(crash_forecast_exe_path, exe_name)}", # type: ignore
                '-p', crash_path,
                '-m', magic_number
            ]
            subprocess.Popen(
                ['cmd.exe', '/c', 'start', 'cmd.exe', '/k',
                 f"{os.path.join(crash_forecast_exe_path, exe_name)}", # type: ignore
                 '-p', crash_path,
                 '-m', magic_number
                 ]
            )
            result = subprocess.run(command, capture_output=True, text=True)
            result_stdout = result.stdout
        except Exception as e:
            print(f'Exception during crash_forecast : {e}')
            result_stdout = ''

        root_cause = 'Root Not found'
        try:
            for line in result_stdout.split('\n'):
                m = re.search(r'"Root Cause":.*\"(.*)\"', line)

                if m:
                    print(f'Root Cause: {m.group(1)}')
                    root_cause = m.group(1)
                    break
        except Exception as e:
            print(f'Exception during Root Causing in crash_forecast: {e}')

        try:
            adb_id = get_adb_id()
        except Exception as e:
            print(f'Exception during get_adb_id in crash_forecast: {e}')
            adb_id = ''
        print("added data to fields")
        crash_info_dict = {
            'ADB_ID': [adb_id],
            'CRASH_PATH': [crash_path],
            'TIMESTAMP': [timestamp],
            'ROOT_CAUSE': [root_cause],
            'FST_ID': [fst_id],
            'ZIP_STATUS': False
        }
        print("Starting to edit CSV")
        create_crash_meta_info_csv(crash_info_dict)
        print("DOne edit csv")
    else:
        print("[INFO] Not a valid crash path.")

def create_crash_meta_info_csv(crash_info_dict):
    # Creates CrashMetaInfo.csv with columns
    # crash_count, adb_id, crash_path, timestamp, root_cause, fst_id

    from CopyCsv import CONTROL_BASE, copy_csv_to_latest_folder
    
    df = pd.DataFrame(crash_info_dict)
    crash_meta_info_csv = os.path.join(CTM_LOGS_DIR, 'CrashMetaInfo.csv')
    if os.path.exists(crash_meta_info_csv):
        df_csv = pd.read_csv(crash_meta_info_csv, index_col=False)
        df = pd.concat([df_csv, df], axis=0, ignore_index=True)
        df.drop_duplicates(subset='CRASH_PATH', keep='last', inplace=True)
        df = df.sort_values(by=['TIMESTAMP'], ascending=False)
        os.remove(crash_meta_info_csv)
    df.to_csv(crash_meta_info_csv, index=False)

    copy_csv_to_latest_folder(crash_meta_info_csv, CONTROL_BASE)

    # display_crash_table(crash_meta_info_csv)


def zip_and_upload_crash_dump(crash_dir_list):
    # Goes through CrashMetaInfo.csv and triggers zip & upload for each row
    # Update CrashMetaInfo.csv by deleting corresponding row -> display_crash_table
    from FzHandler import file_upload
    df = pd.read_csv(os.path.join(CTM_LOGS_DIR, 'CrashMetaInfo.csv'))

    for index, row in df.iterrows():
            
        crash_path = row.get("CRASH_PATH")
        if crash_path in crash_dir_list:

            if crash_path and os.path.exists(crash_path):
                new_crash_path = None
                try:
                    crash_base = os.path.dirname(crash_path)
                    orig_crash_name = os.path.basename(crash_path)
                    count = 1
                    crash_name = get_crash_naming(orig_crash_name, count)
                    if not crash_name:
                        print('Could not retrieve correct naming convention. Pls check')
                        continue
                    new_crash_path = os.path.join(crash_base, crash_name)
                    while find_folder(DEFAULT_CRASHDUMP, crash_name) or find_folder(CRASHDUMP_ROOT_PCAT, crash_name):
                        count = count + 1
                        crash_name = get_crash_naming(orig_crash_name, count)
                        if not crash_name:
                            print('Could not retrieve correct naming convention. Pls check')
                            new_crash_path = None
                            break
                        new_crash_path = os.path.join(crash_base, crash_name)
                except Exception as e:
                    print(f'Exception while retrieving crash naming: {e}')

                if not new_crash_path:
                    continue

                try:
                    os.rename(crash_path, new_crash_path)
                    update_crash_entry(crash_path, new_crash_path)
                except Exception as e:
                    print(f'Exception during renaming crash path and updating in csv: {e}')

                if os.path.exists(new_crash_path):
                    # Zip
                    output_zip = os.path.join(os.path.dirname(new_crash_path), f'{crash_name}.7z')
                    if not get_zip_status(new_crash_path):
                        try:
                            print(f'Zipping {output_zip}')
                            zip_command = [seven_zip_path, 'a', output_zip, new_crash_path]
                            subprocess.run(zip_command, capture_output=True, text=True)

                            update_crash_zip_status(os.path.join(new_crash_path)
                        except Exception as e:
                            print(f'Exception during zipping crash dump: {e}')

                    print(f'Uploading {output_zip}')
                    try:
                        upload_result = file_upload(output_zip, f"crash_upload/{crash_name}.7z")
                        if upload_result:
                            remove_crash_entry(crash_path)
                    except Exception as e:
                        print(f'Exception during uploading {output_zip}')


def find_folder(base_path, folder_name):
    for root, dirs, files in os.walk(base_path):
        if folder_name in dirs:
            return os.path.join(root, folder_name)
    return None
    

def forecast_crashes(crash_dir_list):
    # cfg = load_json()
    # normal_crash_path = cfg.get("previous_crash_dir", "null")
    # rdkb_crash_path = cfg.get("previous_rdkbcrash_dir", "null")
    # magic_number = CrashForecastPage.get_magic_string()
    #Choose which to run, or run both if needed
    # if normal_crash_path:
    for directory in crash_dir_list:
        print(directory)
    # Path objects have .stat() as a method
        time_stamp = datetime.datetime.fromtimestamp(os.stat(directory).st_mtime).strftime("%Y-%m-%dT%H:%M:%S")
        print(time_stamp, directory)
        start_thread(crash_forecast, "Crash Dump forecast", crash_path=directory, timestamp=time_stamp)
    # if rdkb_crash_path:
    #     crash_forecast(rdkb_crash_path)  # Uncomment if needed


def get_naming_convention():
    cfg = load_prov_json()
    market = cfg.get("market", None)
    name = cfg.get("name", None)
    fst_id = cfg.get("fst_id", None)
    operator = cfg.get("operator", None)
    tdc_serial = cfg.get("tdc_serial", None)
    # market="LV-CPE "
    # name="kiran"
    # fst_id="sdx-asdjfjsdl-7887"
    return market, name, fst_id, operator, tdc_serial

def set_naming_convention(market, name, fst_id, operator, tdc_serial, magic_string=None):
    print(f'market: {market}, name: {name}, fst_id: {fst_id}, operator: {operator}, tdc_serial: {tdc_serial}')
    cfg = load_prov_json()
    if market:
        cfg["market"] = market
    if name:
        cfg["name"] = name
    if fst_id:
        cfg["fst_id"] = fst_id
    if operator:
        cfg["operator"] = operator
    if tdc_serial:
        cfg["tdc_serial"] = tdc_serial
    if magic_string:
        cfg["magic_string"] = magic_string
    save_prov_json(cfg)

def set_naming_convention_from_crash_rename_csv():
    from Constants import CRASH_RENAME_META_CSV
    from WifiController import get_adb_id, get_mpss_build_info, get_meta_build_info

    market = name = fst_id = operator = tdc_serial = magic_string = None

    if os.path.exists(CRASH_RENAME_META_CSV):
        df_crash_rename = pd.read_csv(CRASH_RENAME_META_CSV, index_col=False)
        _adb_id = get_adb_id()
        _mpss_build = get_mpss_build_info()
        _meta_build = get_meta_build_info().strip('"')
        df_one = df_crash_rename[(df_crash_rename['META'] == _meta_build) & (df_crash_rename['MPSS'] == _mpss_build)]

        hostname = socket.gethostname()
        host_pool_mapping = json.loads(df_one['HOST_POOL_MAPPING'].iloc[0])
        market = host_pool_mapping.get(hostname)

        name = 'Kiran' if ((market in ['LV-CPE', 'Seattle-CPE', 'Dallas-CPE-SA']) or (hostname in ['LAPTOP-IDGK1E3S', 'DESKTOP-8FLRVQK', 'Mohan', 'mstft20-52'])) else 'Aniket'

        adb_tdc_map = json.loads(df_one['ADB_TDC_MAPPING'].iloc[0])
        tdc_serial = adb_tdc_map.get(_adb_id)

        fst_id = df_one['FST_ID'].iloc[0]

        magic_string = df_one['MAGIC_STRING'].iloc[0]

        operator = get_operator()

        set_naming_convention(market, name, fst_id, operator, tdc_serial, magic_string)


def get_operator():
    from Constants import CTM_LOGS_DIR
    operator = None
    control_meta_csv_files = glob.glob(CTM_LOGS_DIR + '\\*control_metadata.csv', recursive=True)
    if control_meta_csv_files:
        meta_csv = sorted(control_meta_csv_files, reverse=True)[0]
        df_operator = pd.read_csv(meta_csv, index_col=False)
        if isinstance(df_operator, pd.DataFrame):
            operator = df_operator['OPERATOR'].iloc[0]
    return operator
    
def get_crash_naming(orig_crash_name='', count=1):
    crash_name = None
    date_folder = ''
    m = re.search(r'^(\d{4})(\d{4})-(\d+)', orig_crash_name)
    if m:
        date_folder = f'{m.group(2)}{m.group(1)}'
    else:
        date_folder = date.today()
        date_folder = date_folder.strftime("%m%d%Y")
    # count = 1
    market, name, fst_id, operator, tdc_serial = get_naming_convention()

    if not market:
        print('market is not valid. Pls check')
    if not name:
        print('name is not valid. Pls check')
    if not fst_id:
        print('fst_id is not valid. Pls check')
    # if not date_folder:
    #     print('date_folder is not valid. Pls check')
    if not operator:
        print('operator is not valid. Pls check')
    if not tdc_serial:
        print('tdc_serial is not valid. Pls check')

    if market and name and fst_id and operator and tdc_serial:
        crash_name = f"{market}_{name}_{fst_id}_{date_folder}_{operator}_{count}_{tdc_serial}_LAN_DRI"
        crash_name = re.sub(r'\s+', '', crash_name)
    return crash_name

def get_zip_status(crash_path):
    result = None
    crash_meta_info_csv = os.path.join(CTM_LOGS_DIR, 'CrashMetaInfo.csv')
    if os.path.exists(crash_meta_info_csv):
        df_csv = pd.read_csv(crash_meta_info_csv, index_col=False)
        result = df_csv[(df_csv['CRASH_PATH'] == crash_path) & (df_csv['ZIP_STATUS'] == True)]
    else:
        print(f'{crash_meta_info_csv} does not exist')
    return result

def update_crash_zip_status(crash_path):
    print(f'Updating zip-flag for {crash_path} in CrashMetaInfo.csv')
    crash_meta_info_csv = os.path.join(CTM_LOGS_DIR, 'CrashMetaInfo.csv')
    if os.path.exists(crash_meta_info_csv):
        df_csv = pd.read_csv(crash_meta_info_csv, index_col=False)
        df_csv.loc[df_csv['CRASH_PATH'] == crash_path, 'ZIP_STATUS'] = True
        df_csv = df_csv.sort_values(by=['TIMESTAMP'], ascending=False)
        os.remove(crash_meta_info_csv)
        df_csv.to_csv(crash_meta_info_csv, index=False)
    else:
        print(f'{crash_meta_info_csv} does not exist')

def update_crash_entry(old_crash_path, new_crash_path):
    print(f'{old_crash_path} will be replaced with {new_crash_path} from CrashMetaInfo.csv')
    crash_meta_info_csv = os.path.join(CTM_LOGS_DIR, 'CrashMetaInfo.csv')
    if os.path.exists(crash_meta_info_csv):
        df_csv = pd.read_csv(crash_meta_info_csv, index_col=False)
        df_csv['CRASH_PATH'] = df_csv['CRASH_PATH'].replace(old_crash_path, new_crash_path)
        df_csv = df_csv.sort_values(by=['TIMESTAMP'], ascending=False)
        os.remove(crash_meta_info_csv)
        df_csv.to_csv(crash_meta_info_csv, index=False)
    else:
        print(f'{crash_meta_info_csv} does not exist')

def remove_crash_entry(filepath):
    print(f'{filepath} will be removed from CrashMetaInfo.csv')
    crash_meta_info_csv = os.path.join(CTM_LOGS_DIR, 'CrashMetaInfo.csv')
    df_csv = pd.DataFrame()
    if os.path.exists(crash_meta_info_csv):
        df_csv = pd.read_csv(crash_meta_info_csv, index_col=False)
        df_csv = df_csv[df_csv['CRASH_PATH'] != filepath]
        df_csv = df_csv.sort_values(by=['TIMESTAMP'], ascending=False)
        os.remove(crash_meta_info_csv)
    df_csv.to_csv(crash_meta_info_csv, index=False)

def remove_crash_entries(filepaths):
    for filepath in filepaths:
        remove_crash_entry(filepath)
        
if __name__ == "__main__":
    pass
    #print(get_crash_naming())
