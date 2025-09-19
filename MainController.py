# MainController.py
from __future__ import annotations
from gc import callbacks
import sys
import subprocess
import time
from datetime import datetime
import ctypes
from tkinter import messagebox
import json, threading, time
import logging

import ADBController
import KillProcess
import StartTestCase
import QutsController
import WifiController
import GUI as gui
import CrashCountController as cc
import JsonHandler as JH
import psutil
import yaml
import glob
import pandas as pd

# ── NEW IMPORT ────────────────────────────────────────────────────────────────
# We need to know when to skip updates:
import os

# Constants for batch file directories and names
CMD_DIR_CONTROL  = r"C:\QSTAF\QSTAFpy\bin\Control_laptop\Windows"
BAT_FILE_CONTROL = "Run_framework.bat"
CMD_DIR_TRAFFIC  = r"C:\QSTAF\QSTAFpy\bin\Traffic_laptop\Windows"
BAT_FILE_TRAFFIC = "Run_framework.bat"
CMD_DIR_AWS      = r"C:\QSTAF\QSTAFpy\bin"
BAT_FILE_AWS     = "aws_s3_uploder.bat"
QSTAF_file_path  =r"C:\QSTAF\QSTAFpy\version.txt"
CONFIG_YAML = r"C:\QSTAF\QSTAFpy\config\config.yaml"
CONFIG_1_ITERATION_YAML = r"C:\QSTAF\QSTAFpy\config\config_1_iteration.yaml"
TC_SPEEDTEST = r"C:\QSTAF\QSTAFpy\test_cases\Traffic\SpeedTest.txt"
RUN_SPEEDTEST_BAT = r"C:\QSTAF\QSTAFpy\bin\Traffic_laptop\Windows\Run_SpeedTest.bat"
TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S"
MODES = ("control", "traffic")
DEFAULT_TIMER_HOURS = 6
LOG_DIR = r'C:\QSTAF\CTM_logs'

# CrashCountController.run_watch()

# Set up logging for debugging EXE issues
if getattr(sys, 'frozen', False):
    # ensure both crashDump and logs folders exist
    os.makedirs(JH.LOG_DIR, exist_ok=True)

    # redirect stderr into a separate fileg
    sys.stderr = open(os.path.join(JH.LOG_DIR, "app_errors.log"), "w")

def log_exception(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
sys.excepthook = log_exception

def get_qstaf_version():
    """Read and return the version string from the given text file."""
    try:
        with open(QSTAF_file_path, 'r', encoding='utf-8') as f:
            # strip off any whitespace/newlines
            return f.read()
    except Exception as e:
        # fallback if file’s missing or unreadable
        return "Unknown"

def get_meta_mpss():
    meta = "UNKNOWN"
    mpss = "UNKNOWN"
    try:
        meta = WifiController.get_meta_build_info()
    except Exception as e:
        print(f'Exception while reading Meta: {e}')
    try:
        mpss = WifiController.get_mpss_build_info()
    except Exception as e:
        print(f'Exception while reading MPSS: {e}')

    return meta, mpss

def get_executable_dir():
    """Get the directory where the executable is located, works for both .py and .exe"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as Python script
        return os.path.dirname(os.path.abspath(__file__))

def is_running_as_exe():
    """Check if we're running as a compiled executable"""
    return getattr(sys, 'frozen', False)

def ensure_admin():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            if is_running_as_exe():
                # If running as EXE, restart the EXE with admin privileges
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
            else:
                # If running as Python script
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
            sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Admin check failed: {e}")
        sys.exit(1)

def start_framework(mode):
    if mode.lower() == 'control':
        try:
            StartTestCase.start_tests(CMD_DIR_CONTROL, BAT_FILE_CONTROL,'Control')
            JH.set_time(mode)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    elif mode.lower() == 'traffic':
        try:
            StartTestCase.start_tests(CMD_DIR_TRAFFIC, BAT_FILE_TRAFFIC,'Traffic')
            JH.set_time(mode)
        except Exception as e:
            messagebox.showerror("Error", str(e))

def stop_framework(mode):
    found = KillProcess.stop_all_tests(mode)
    JH.rest_framework_timestamps(mode)
    msg = "All processes stopped." if found else "No processes found to stop."
    print(msg)

def run_s3_uploader():
    try:
        StartTestCase.start_tests(CMD_DIR_AWS, BAT_FILE_AWS,None)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def restart_quts_pcat_qxdm():
    def show_status(msg: str):
        print(msg)
    QutsController.restart_quts_pcat_qxdm(callback=show_status)
    

def check_restart_timer():
    """
    Every 5 minutes, for each mode:
      - load config
      - if timestamp is null → ignore that mode entirely
      - else if elapsed >= timer → restart and update timestamp
    """
    while True:
        reset_start_timestamp()
        cfg = JH.load_json()
        # compute relaunch period in seconds
        relaunch_timer = cfg.get("relaunch_timer", DEFAULT_TIMER_HOURS)
        try:
            hrs = int(relaunch_timer)
        except (TypeError, ValueError):
            hrs = DEFAULT_TIMER_HOURS
        relaunch_timer = hrs * 3600

        now = datetime.now()
        now_str = now.strftime(TIMESTAMP_FMT)

        for mode in MODES:
            ts_str = cfg.get(f"{mode}_start_timestamp")

            # **IGNORE** if no timestamp or explicitly "null"
            if not ts_str or ts_str.lower() == "null":
                print(f"invalid time stamp found for {mode}")
                continue

            # parse & check elapsed
            start_time = datetime.strptime(ts_str, TIMESTAMP_FMT)
            elapsed = (now - start_time).total_seconds()
            if elapsed >= relaunch_timer:
                stop_framework(mode)
                time.sleep(10)
                start_framework(mode)
                
        time.sleep(120)


def run_app() -> None:
    """Entry‑point called by QSTAF_Tool.exe"""
    # 1) Require admin
    ensure_admin()

    #commont the below line and uncomment step 2 to check for updates
    gui.launch_gui()

    '''
    # 2) One‑time update check unless the flag is present
    if "--skip-updates" not in sys.argv:
        if is_running_as_exe():
            if check_for_updates_integrated():
                # New version will relaunch, so stop here
                return
        else:
            # Running from .py – spawn updater in separate console
            updater = os.path.join(get_executable_dir(), "CheckUpdates.py")
            if os.path.exists(updater):
                subprocess.Popen(
                    ["cmd", "/c", "start", "", sys.executable, updater],
                    shell=False
                )
                sys.exit(0)

    # 3) Fire up the GUI
    gui.launch_gui()
    '''

        
def start_Pact_only():
    print("pcat called")
    QutsController.start_app(QutsController.PCAT_PATH,"PCATApp.exe")

def start_QXDM_only():
    print("QXDM called")
    QutsController.start_app(QutsController.QXDM_PATH,"QXDM.exe")

def start_all():
    QutsController.start_quts()
    start_Pact_only()
    start_QXDM_only()

def stop_pcat_only():
    print("Stopped pcat")
    subprocess.run("taskkill /IM PCATApp.exe /F", shell=True)

def stop_qxdm_only():
    print("Stopped qxdm")
    subprocess.run("taskkill /IM QXDM.exe /F", shell=True)

def stop_all_tools_Framework():
    stop_framework(mode="control")
    stop_framework(mode="")
    subprocess.run("taskkill /IM PCATApp.exe /F", shell=True)
    subprocess.run("taskkill /IM QXDM.exe /F", shell=True)

   
#---------to collect logs to txt------------------------
'''
LOG_DIR.mkdir(parents=True, exist_ok=True) 
LOG_PATH = LOG_DIR / "qstaf_tool.log" 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler()          # still prints to console if visible
    ],
)
log = logging.getLogger(__name__)
builtins.print = lambda *a, **kw: log.info(" ".join(map(str, a)))
'''

# to be implemented
def is_running(mode):
    """Return True if mode process is running. Else False"""
    found = False
    if mode == "control":
        keywords = ["control "]
    else:
        keywords = ["traffic "]

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline']).lower()
            if any(keyword in cmdline for keyword in keywords):
                found = True
                break
        except Exception:
            pass
    return found

def reset_start_timestamp():
    """ Resets start_time stamp to null in json if not running"""
    if not is_running('control'):
        cfg = JH.load_json()
        cfg[f"control_start_timestamp"] = "null"
        JH.save_json(cfg)

    if not is_running('traffic'):
        cfg = JH.load_json()
        cfg[f"traffic_start_timestamp"] = "null"
        JH.save_json(cfg)

def SpeedTest(iterationCount, callback=None):
    # Create CONFIG_1_ITERATION_YAML if does not exist

    print(f"iterationCount: {iterationCount}")
    try:
        if not os.path.exists(CONFIG_1_ITERATION_YAML):
            if os.path.exists(CONFIG_YAML):
                with open(CONFIG_YAML, 'r') as f:
                    config = yaml.safe_load(f)

                # Update fields
                config['traffic']['max_main_executions'] = 1
                config['traffic']['iteration_method'] = 'ByCount'
                config['traffic']['iteration_count'] = 1
                config['traffic']['playlist'] = False
                config['traffic']['playlist_data'][0]['file_location'] = r'C:\QSTAF\QSTAFpy\test_cases\Traffic\SpeedTest.txt'

                # Save the updated content back to the file
                with open(CONFIG_1_ITERATION_YAML, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)


        if not os.path.exists(TC_SPEEDTEST):
            with open(TC_SPEEDTEST, 'w') as f:
                f.write("SpeedTest 1111 1:2")

        if not os.path.exists(RUN_SPEEDTEST_BAT):
            with open(RUN_SPEEDTEST_BAT, 'w') as f:
                f.write("""@echo off
                    call C:\\QSTAF\\myenv\\Scripts\\activate.bat
                    
                    set config_file=..\\..\\..\\config\\config_1_iteration.yaml
                    set test_file=..\\..\\..\\test_cases\\Traffic\\SpeedTest.txt
                    
                    :argument_loop
                    if "%~1"=="-c" (
                      set config_file=%~2
                      shift
                      shift
                    ) else if "%~1"=="-t" (
                      set test_file=%~2
                      shift
                      shift
                    ) else (
                      goto :end_args
                    )
                    goto :argument_loop
                    
                    :end_args
                    
                    py C:\\QSTAF\\QSTAFpy\\src\\core\\Main.py -m traffic -c %config_file% -t %test_file%""")
                
    except Exception as e:
        print(f'Exception updating config yaml: {e}')

    try:
        if iterationCount >1:
            with open(CONFIG_1_ITERATION_YAML, 'r') as f:
                    config = yaml.safe_load(f)

            config['traffic']['iteration_count'] = iterationCount

                # Save the updated content back to the file
            with open(CONFIG_1_ITERATION_YAML, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        else: 
            with open(CONFIG_1_ITERATION_YAML, 'r') as f:
                    config = yaml.safe_load(f)

            config['traffic']['iteration_count'] =1

                # Save the updated content back to the file
            with open(CONFIG_1_ITERATION_YAML, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

        StartTestCase.start_bat_and_watch_stdout(CMD_DIR_TRAFFIC, 'Run_SpeedTest.bat',callback) #, 'traffic'
    except Exception as e:
        messagebox.showerror("Error", str(e))

    try:
        get_all_speedtest_results()
    except Exception as e:
        print(f'Exception during get_all_speedtest_results: {e}')


def get_all_speedtest_results():

    speedtest_list = []

    speedtest_csvs = glob.glob(LOG_DIR + '\\**\\*vpid1111_seqno1_SpeedTest.csv', recursive=True)

    df_csv = pd.DataFrame()
    for speedtest_csv in speedtest_csvs:
        try:
            df_csv = pd.concat([df_csv, pd.read_csv(speedtest_csv)], axis=0)
        except Exception as e:
            print(f'Exception during speedtest df_csv: {e}')
    if not df_csv.empty:
        df_csv = df_csv.sort_values(by=['end_time'], ascending=False)
        df_csv = df_csv[df_csv['result'] == 'Pass']
    if len(df_csv) > 10:
        df_csv = df_csv.head(10)


    dl_stats_csvs = glob.glob(LOG_DIR + '\\**\\*QSH_DL_STATS.csv', recursive=True)

    dl_stats_df = pd.DataFrame()
    rfband_df = pd.DataFrame()
    for dl_stats_csv in dl_stats_csvs:
        try:
            dl_stats_df = pd.concat([dl_stats_df, pd.read_csv(dl_stats_csv)], axis=0)
        except Exception as e:
            print(f'Exception during dl_stats_df: {e}')

    if not dl_stats_df.empty:
        try:
            dl_stats_df = dl_stats_df.sort_values(by=['DEVICE_TIMESTAMP'])
            dl_stats_df['TIME_DIFF'] = abs((pd.to_datetime(dl_stats_df['DEVICE_TIMESTAMP'])) - pd.to_datetime(
                dl_stats_df['DEVICE_TIMESTAMP'].shift(1, fill_value=0)))
            dl_stats_df['MICRO_SEC'] = dl_stats_df['TIME_DIFF'].apply(lambda x: x.value / 1000)
            dl_stats_df.loc[0, 'MICRO_SEC'] = 0
            dl_stats_df['INDEX'] = (dl_stats_df['MICRO_SEC'] - 10000).gt(0).cumsum() - 1
            rfband_df = dl_stats_df.groupby('INDEX')['BAND'].apply(lambda x: '+'.join(x)).reset_index()
            rfband_df = rfband_df.merge(dl_stats_df[['INDEX', 'TIMESTAMP']], on='INDEX', how='left')
            rfband_df = rfband_df.drop_duplicates(subset='INDEX')
        except Exception as e:
            print(f'Exception during rfband_rf : {e}')

    gps_monitor_csvs = glob.glob(os.path.join(LOG_DIR, '**', '*qstaf_gps_monitor.csv'), recursive=True)
    gps_df = pd.DataFrame()
    for gps_monitor_csv in gps_monitor_csvs:
        try:
            print(gps_monitor_csv)
            gps_df = pd.concat([gps_df, pd.read_csv(gps_monitor_csv, header=None, names=['TIMESTAMP', 'LATITUDE', 'LONGITUDE', 'ALTITUDE'])], ignore_index=True, axis=0)
        except Exception as e:
            print(f'Exception during gps_df: {e}')
    if not gps_df.empty:
        gps_df = gps_df.sort_values(by=['TIMESTAMP'], ascending=False)
    time_window = pd.Timedelta(minutes=5)

    for i in range(len(df_csv)):
        try:
            speedtest_dict = {
                'DL': df_csv['download_speed_Mbps'].iloc[i],
                'UL': df_csv['upload_speed_Mbps'].iloc[i],
                'BAND': 'UNKNOWN',
                'ADBID': df_csv['Metadata_device'].iloc[i],
                'START_TIMESTAMP': df_csv['start_time'].iloc[i],
                'TIMESTAMP': df_csv['end_time'].iloc[i]
            }
            if not gps_df.empty:
                gps_df_filtered = gps_df[(pd.to_datetime(gps_df['TIMESTAMP'], format='%Y-%m-%d %H:%M:%S.%f') >= pd.to_datetime(speedtest_dict['TIMESTAMP'], format='%Y-%m-%d_%H_%M_%S') - time_window) & (pd.to_datetime(gps_df['TIMESTAMP'], format='%Y-%m-%d %H:%M:%S.%f') <= pd.to_datetime(speedtest_dict['TIMESTAMP'], format='%Y-%m-%d_%H_%M_%S') + time_window)]

                if not gps_df_filtered.empty:
                    closest = gps_df_filtered.loc[
                        (pd.to_datetime(gps_df_filtered['TIMESTAMP'], format='%Y-%m-%d %H:%M:%S.%f') - pd.to_datetime(
                            speedtest_dict['TIMESTAMP'], format='%Y-%m-%d_%H_%M_%S')).abs().idxmin()]
                    speedtest_dict['LOCATION'] = f'{closest['LATITUDE'].replace('latitude: ', '')}, {closest['LONGITUDE'].replace('longitude: ', '')}'
                else:
                    speedtest_dict['LOCATION'] = 'UNKNOWN'
            else:
                speedtest_dict['LOCATION'] = 'UNKNOWN'
        except Exception as e:
            print(f'Exception during Speedtest LOCATION for entry-{i}: {e}')
            speedtest_dict['LOCATION'] = 'UNKNOWN'


        try:
            speedtest_timestamp = None
            if not rfband_df.empty:
                rfband_df_filtered = rfband_df[
                    (pd.to_datetime(rfband_df['TIMESTAMP'], format='%Y-%m-%d %H:%M:%S') >= pd.to_datetime(
                        speedtest_dict['START_TIMESTAMP'], format='%Y-%m-%d_%H_%M_%S')) & (
                            pd.to_datetime(rfband_df['TIMESTAMP'], format='%Y-%m-%d %H:%M:%S') <= pd.to_datetime(
                        speedtest_dict['TIMESTAMP'], format='%Y-%m-%d_%H_%M_%S'))]

                if not rfband_df_filtered.empty:
                    speedtest_dict['BAND'] = rfband_df_filtered.loc[rfband_df_filtered['BAND'].str.len().idxmax()]['BAND']
                    speedtest_timestamp = pd.to_datetime(rfband_df_filtered.loc[rfband_df_filtered['BAND'].str.len().idxmax()]['TIMESTAMP'], format='%Y-%m-%d %H:%M:%S')
                else:
                    speedtest_dict['BAND'] = 'UNKNOWN'

            else:
                speedtest_dict['BAND'] = 'UNKNOWN'
        except Exception as e:
            print(f'Exception during Speedtest BAND for entry-{i}: {e}')
            speedtest_dict['BAND'] = 'UNKNOWN'

        # Getting the Connectivity_Mode from RF Band Info
        try:
            rfbandinfo_df = pd.DataFrame()
            rfbandinfo_csvs = glob.glob(LOG_DIR + '\\**\\*RFBandInfo.csv', recursive=True)
            for rfbandinfo_csv in sorted(rfbandinfo_csvs):
                rfbandinfo_df = pd.concat([rfbandinfo_df, pd.read_csv(rfbandinfo_csv)], axis=0)
            if not rfbandinfo_df.empty:
                rfbandinfo_df = rfbandinfo_df.sort_values(by=["Timestamp"], ascending=False)
                if speedtest_timestamp:
                    df_temp = rfbandinfo_df[pd.to_datetime(rfbandinfo_df['Timestamp'], format='%Y-%m-%d %H:%M:%S') < speedtest_timestamp]
                    if isinstance(df_temp, pd.DataFrame) and not df_temp.empty:
                        conn_mode = df_temp.iloc[0]['Connectivity_Mode']
                        if speedtest_dict['BAND'] != 'UNKNOWN':
                            speedtest_dict['BAND'] = f"{conn_mode}_{speedtest_dict['BAND']}"
        except Exception as e:
            print(f'Exception during Speedtest rfbandinfo_df: {e}')
        speedtest_list.append(speedtest_dict)

    cfg = JH.load_json()
    cfg["SpeedTestData"] = speedtest_list
    JH.save_json(cfg)
    print("Speedtest results collected and saved to JSON.")





# def check_wifi_type(toggle_var,wifi_config):
#     #set_wifi_config(wifi_config, toggle_var)
#     if toggle_var == "OWRT" and wifi_config == 0: # 3 SLO
#         print(f"OWRT 3 SLO selected {toggle_var, wifi_config}")
#         WifiController.update_cpe_wifi_config(toggle_var,wifi_config,"") #test SSID
#          #method call here
#     elif toggle_var == "OWRT" and wifi_config == 1: # 2G SLO + 5G-6G MLO
#         print(f"OWRT 2G SLO + 5G-6G MLO selected {toggle_var, wifi_config}")
#         WifiController.update_cpe_wifi_config(toggle_var,wifi_config,"") #test SSID
#     elif toggle_var == "RDKB":
#         print(f"RDKB selected {toggle_var, wifi_config}")
#         WifiController.connectBackhaul()
#         WifiController.setpassword_bandwidths_rdkb()
         

# def check_Rename_SSID(toggle_var,wifi_config,rename_type):
#     if toggle_var == "OWRT" and wifi_config == 0: # 3 SLO
#         if rename_type == "_":  #test SSID
#             print(f"OWRT 3 SLO selected with test SSID")
#             WifiController.update_cpe_wifi_config(toggle_var,wifi_config,rename_type)
#         else:
#             print(f"OWRT 3 SLO selected with default SSID")
#             WifiController.update_cpe_wifi_config(toggle_var,wifi_config,rename_type)
#         #method call here
#     elif toggle_var == "OWRT" and wifi_config == 1: # 2G SLO + 5G-6G MLO  
#         if rename_type == "_":  #test SSID
#             print(f"OWRT 2G SLO + 5G-6G MLO selected with test SSID")
#             WifiController.update_cpe_wifi_config(toggle_var,wifi_config, "_")
#         else:
#             print(f"OWRT 2G SLO + 5G-6G MLO with default SSID")
#             WifiController.update_cpe_wifi_config(toggle_var,wifi_config, "")

#     elif toggle_var == "RDKB":
#         if rename_type == "_":  #test SSID
#             WifiController.update_cpe_wifi_config(toggle_var,wifi_config, "_")
#         else:
#             WifiController.update_cpe_wifi_config(toggle_var,wifi_config, "")
       
        


    


def main() -> None:
    ADBController.save_to_json("--")
    
    t3 = threading.Thread(
        target=ADBController.run_adb_track_devices,
        daemon=True  # auto‑stops when the main program exits
    )
    t3.start()

    # Start the watcher in a daemon thread
    t = threading.Thread(
        target=cc.run_watchdog,
        daemon=True        # auto‑stops when the main program exits
    )
    t.start()
    
    
    t2 = threading.Thread(
        target=check_restart_timer,
        daemon=True  # auto‑stops when the main program exits
    )
    t2.start()

    
 
    # Launch GUI (must stay on the main thread on Windows/macOS)
    run_app()

if __name__ == "__main__":
    main()
