import os
import re
import glob
import shutil
from datetime import datetime
import time as time_module
import LogHandler
from Constants import CTM_LOGS_DIR

QSTAF_OUTPUT_BASE = r'C:\Temp\automation\QSTAF\QSTAFpy'
CONTROL_BASE = os.path.join(QSTAF_OUTPUT_BASE, 'Control')
TRAFFIC_BASE = os.path.join(QSTAF_OUTPUT_BASE, 'Traffic')
file_time_dict = {}

timeout = 2 * 60 * 60  # 2 hours
del_timeout = (2* 60 * 60) + 30
SubDirCount=100


def get_sorted_dirs(base):
    sorted_dirs = []
    if os.path.exists(base):
        sorted_dirs = sorted([d for d in os.listdir(base)])
    #print(f'Found directories: {sorted_dirs}')
    return sorted_dirs


def get_base(BASE_DIR):
    base_dir_list = []
    dirs = get_sorted_dirs(BASE_DIR)
    for dir in dirs:
        if os.path.exists(os.path.join(BASE_DIR, dir, 'old_data.txt')):
            continue

        m = re.search(r'(Playlist_)?(\d{4}-\d{2}-\d{2}_\d{2}_\d{2}_\d{2})', dir)
        if m:
            date_str = m.group(2)
            if date_str:
                date = datetime.strptime(date_str, "%Y-%m-%d_%H_%M_%S")
                now = datetime.now()
                if int((now - date).total_seconds()) < timeout:
                    base_dir_list.append(os.path.join(BASE_DIR, dir))
                    continue
        
        csv_files = glob.glob(os.path.join(BASE_DIR, dir) + '\\**\\*.csv', recursive=True)
        for csv in csv_files:
            csv_name = csv.split('\\')[-1]
            m = re.search(r'\[(\d+)\].*csv', csv_name)
            if m:
                date_str = m.group(1)
                date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
                now = datetime.now()
                delta = now - date
                # print(delta)
                if int((now-date).total_seconds()) < timeout:
                    base_dir_list.append(os.path.join(BASE_DIR, dir))
                    break
        else:
            open(os.path.join(BASE_DIR, dir, "old_data.txt"), "w").close()
    return base_dir_list

def get_copy_csv_list(base_dir, csv_patterns):
    csv_copy_list = []
    control_base_list = get_base(base_dir)

    for control_base_dir in control_base_list:
        try:
            subdir_count = sum(1 for entry in os.scandir(control_base_dir) if entry.is_dir())
            if subdir_count > SubDirCount:
                LogHandler.sendLog(f'Skipping {control_base_dir} - too many subdirectories ({subdir_count})')
                continue
        except (OSError, PermissionError) as e:
            LogHandler.sendLog(f'Error accessing {control_base_dir}: {e}')
            continue

        for csv_pattern in csv_patterns:
            csv_files = glob.glob(control_base_dir + csv_pattern, recursive=True)

            current_time = datetime.now()
            for csv in csv_files:
                csv_name = csv.split('\\')[-1]
                if csv_name.startswith('indexing') or csv_name.startswith('consolidated'):
                    continue
                
                m = re.search(r'\[(\d+)\]', csv_name)
                if m:
                    file_time_stamp = m.group(1)
                    file_time = datetime.strptime(file_time_stamp, "%Y%m%d%H%M%S")
                    if int((current_time - file_time).total_seconds()) < timeout:
                        csv_copy_list.append(csv)
    # print(csv_copy_list)
    return csv_copy_list

def get_speedtest_csv_list():
    csv_speedtest_list = []
    speedtest_csv_patterns = ['\\**\\*vpid1111_seqno1_SpeedTest.csv']

    try:
        csv_speedtest_list = get_copy_csv_list(TRAFFIC_BASE, speedtest_csv_patterns)
    except Exception as e:
        print(f'Exception during get_speedtest_csv_list: {e}')

    for csv in csv_speedtest_list:
        #print(f'Copying {csv}')
        shutil.copy(csv, CTM_LOGS_DIR)

def get_total_copy_csv_list():
    csv_copy_list = []
    control_csv_patterns = ['\\**\\*RFBandInfo.csv', '\\**\\*QSH.csv', '\\**\\*QSH_DL_STATS.csv',
                            '\\**\\*QSH_FR_MODE.csv',
                            '\\**\\*QSH_ENL2.csv', '\\**\\*qstaf_monitor_connected_devices.csv',
                            '\\**\\*qstaf_monitor.csv', '\\**\\*qstaf_gps_monitor.csv']
    traffic_csv_patterns = ['\\**\\*Ping.csv', '\\**\\*Zoomcall.csv', '\\**\\*BrowseUrl.csv',
                            '\\**\\*SpeedTest.csv',
                            '\\**\\*HttpDownload.csv', '\\**\\*ftpUpload.csv', '\\**\\*ftpDownload.csv',
                            '\\**\\*GoogleMaps.csv']
    try:
        csv_copy_list = get_copy_csv_list(CONTROL_BASE, control_csv_patterns)
    except Exception as e:
        print(f'Exception during get_control_copy_csv_list: {e}')

    try:
        csv_copy_list.extend(get_copy_csv_list(TRAFFIC_BASE, traffic_csv_patterns))
        
    except Exception as e:
        print(f'Exception during get_control_copy_csv_list: {e}')

    return csv_copy_list


def copy_latest_csv():

    total_csv_copy_list = get_total_copy_csv_list()

    for csv in total_csv_copy_list:
        #print(f'Copying {csv}')
        shutil.copy(csv, CTM_LOGS_DIR)


# Delete old files from CTM_LOGS_DIR, every del_timeout
def delete_old_csv():
    del_csv_list = []
    csv_files = glob.glob(CTM_LOGS_DIR + '\\*.csv', recursive=True)
    current_time = datetime.now()
    for csv in csv_files:
        if csv not in file_time_dict:
            csv_name = csv.split('\\')[-1]
            if csv_name.startswith('index') or csv_name.startswith('consolidated'):
                del_csv_list.append(csv)
                continue
            m = re.search(r'\[(\d+)\]', csv_name)
            if m:
                file_time_stamp = m.group(1)
                file_time = datetime.strptime(file_time_stamp, "%Y%m%d%H%M%S")
                file_time_dict.update({csv : file_time})
        if file_time_dict.get(csv) and (int((current_time - file_time_dict.get(csv)).total_seconds()) > del_timeout): # type: ignore
            del_csv_list.append(csv)
    for del_csv in del_csv_list:
        os.remove(del_csv)


def copy_csv_main():
    try:
        copy_latest_csv()
    except Exception as e:
        print(f'Exception during copy_latest_csv: {e}')

    try:
        delete_old_csv()
    except Exception as e:
        print(f'Exception during delete_old_csv: {e}')


if __name__ == '__main__':
    copy_csv_main()