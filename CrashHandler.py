import os
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
from FzHandler import file_upload
from Threading import start_thread
from Constants import CTM_LOGS_DIR

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

        crash_info_dict = {
            'ADB_ID': [adb_id],
            'CRASH_PATH': [crash_path],
            'TIMESTAMP': [timestamp],
            'ROOT_CAUSE': [root_cause],
            'FST_ID': [fst_id]
        }
        create_crash_meta_info_csv(crash_info_dict)

    else:
        print("[INFO] Not a valid crash path.")

def create_crash_meta_info_csv(crash_info_dict):
    # Creates CrashMetaInfo.csv with columns
    # crash_count, adb_id, crash_path, timestamp, root_cause, fst_id

    df = pd.DataFrame(crash_info_dict)
    crash_meta_info_csv = os.path.join(CTM_LOGS_DIR, 'CrashMetaInfo.csv')
    if os.path.exists(crash_meta_info_csv):
        df_csv = pd.read_csv(crash_meta_info_csv, index_col=False)
        df = pd.concat([df_csv, df], axis=0)
        os.remove(crash_meta_info_csv)
    df.to_csv(crash_meta_info_csv, index=False)

    # display_crash_table(crash_meta_info_csv)


def zip_and_upload_crash_dump():
    # Goes through CrashMetaInfo.csv and triggers zip & upload for each row
    # Update CrashMetaInfo.csv by deleting corresponding row -> display_crash_table
    df = pd.read_csv(os.path.join(CTM_LOGS_DIR, 'CrashMetaInfo.csv'))

    for index, row in df.iterrows():
        try:
            crash_name = get_crash_naming()
            crash_path = row.get("CRASH_PATH")
            if crash_path:
                # crash_folder = os.path.basename(crash_path)
                crash_base = os.path.dirname(crash_path)
                new_crash_path = os.path.join(crash_base, crash_name)
                if os.path.exists(crash_path):
                    os.rename(crash_path, new_crash_path)

                # Zip
                if os.path.exists(new_crash_path):
                    output_zip = os.path.join(os.path.dirname(new_crash_path), f'{crash_name}.7z')
                    zip_command = [seven_zip_path, 'a', output_zip, new_crash_path]

                    subprocess.run(zip_command, capture_output=True, text=True)

                    file_upload(output_zip, "crash_upload")
        except Exception as e:
            print(f'Exception during zip_and_upload_crash_dump: {e}')


def get_crash_path():
    cfg = load_json()
    normal_crash_path = cfg.get("previous_crash_dir", "null")
    # rdkb_crash_path = cfg.get("previous_rdkbcrash_dir", "null")
    # magic_number = CrashForecastPage.get_magic_string()

    # Choose which to run, or run both if needed
    if normal_crash_path:
        time_stamp = datetime.datetime.fromtimestamp(normal_crash_path.stat().st_mtime).isoformat()
        start_thread(crash_forecast,"Crash Dump forecast", daemon=True, crash_path=normal_crash_path, timestamp=time_stamp)
    # if rdkb_crash_path:
    #     crash_forecast(rdkb_crash_path)  # Uncomment if needed


def get_naming_convention():
    cfg = load_prov_json()
    market = cfg.get("market", "null")
    name = cfg.get("name", "null")
    fst_id = cfg.get("fst_id", "null")
    operator = cfg.get("operator", "null")
    tdc_serial = cfg.get("tdc_serial", "null")
    # market="LV-CPE "
    # name="kiran"
    # fst_id="sdx-asdjfjsdl-7887"
    return market, name, fst_id, operator, tdc_serial

def set_naming_convention(market, name, fst_id, operator, tdc_serial):
    # cfg = load_json(PROV_FILE)
    cfg = load_prov_json()
    cfg["market"] = market
    cfg["name"] = name
    cfg["fst_id"] = fst_id
    cfg["operator"] = operator
    cfg["tdc_serial"] = tdc_serial
    save_prov_json(cfg)

def get_crash_naming():
    today = date.today()
    today = today.strftime("%m%d%Y")
    count = 1
    market, name, fst_id, operator, tdc_serial = get_naming_convention()
    
    crash_name = f"{market}_{name}_{fst_id}_{today}_{operator}_{count}_{tdc_serial}_LAN_DRI"
    crash_name = re.sub(r'\s+', '', crash_name)
    return crash_name
    

if __name__ == "__main__":
    print(get_crash_naming())
