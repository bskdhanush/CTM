import time
import subprocess
import re
import os
import json
from Constants import CTM_CONFIG_DIR

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the base path to the config directory
template_path = os.path.join(script_dir, "config")
output_config_path = r"C:\QSTAF\CTM_logs\config"

# Ensure the output directory exists
os.makedirs(output_config_path, exist_ok=True)

adb_id = None

def run_command(command ):
    output = None
    stderr = None
    max_attempts = 3

    for _ in range(max_attempts):
        try:
            
            print(f"Executing command: {command}")
            process = subprocess.Popen(command,
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stderr:
                print(f"Error: {stderr.decode('utf-8').strip()}")
                time.sleep(1)
                continue
            else:
                output = stdout.decode('utf-8').strip()
                print(f"Command output: {output}")
                break
        except Exception as e:
            print(f"Exception with command {command} : {e}")
    else:
        print(f"{command} failed after max re-attempts")
    return output, stderr

def get_adb_id():
    global adb_id
    if not adb_id:
        output, stderr = run_command("adb devices")
        if not output or stderr:
            raise Exception('adb id NOT FOUND')
        else:
            m = re.search(r'(\w+)\s*(device|offline)$', output)
            if m:
                adb_id = m.group(1)
    return adb_id

# def get_adb_id() -> str | None:
#     """
#     Returns the first **healthy** ADB serial or None if no devices are connected.
#     A healthy line looks like:  84a07517\tdevice
#     """
#     try:
#         proc = subprocess.run(
#             ["adb", "devices"],
#             capture_output=True,
#             text=True,
#             timeout=5,
#             check=False,
#         )
#     except FileNotFoundError:
#         print("ADB executable not found in PATH")
#         return None

#     lines = proc.stdout.strip().splitlines()

#     for line in lines[1:]:                # skip the header
#         parts = line.strip().split()
#         if len(parts) >= 2 and parts[1] == "device":
#             return parts[0]               # healthy transport

#     # No healthy device lines ► optional: kick the server
#     # subprocess.run(["adb", "kill-server"])
#     return None

def get_meta_build_info():
    meta = None
    run_command("adb root")
    output, stderr = run_command("adb shell cat /firmware/verinfo/Ver_Info.txt | findstr Meta_Build_ID")
    if not output or stderr:
        print('Meta Build info NOT FOUND')
    else:
        meta = output.split(': ')[1].strip(',').strip('"')
    return meta

def get_mpss_build_info():
    mpss = None
    #run_command("adb root")
    output, stderr = run_command("adb shell cat /sys/devices/soc0/images | findstr 11:")
    if not output or stderr:
        raise Exception('MPSS Build info NOT FOUND')
    else:
        m = re.search(r'CRM:\s*11:(.*)', output)
        if m:
            mpss = m.group(1)
    return mpss

def run_dmcli_commands(commands):
    run_command("adb root")
    for command in commands:
        run_command(f"adb shell {command}")
        time.sleep(3)


def connectBackhaul():
    run_command("adb root")
    commands = [
        "dmcli eRT setv Device.Cellular.AccessPoint.1.Apn string fast.t-mobile.com",
        "dmcli eRT setv Device.Cellular.AccessPoint.1.X_QCOM.ConnectBackHaul bool true",
        "dmcli eRT setv Device.Cellular.X_QCOM.AutoConnect bool true"
    ]
    run_dmcli_commands(commands)

def update_3_slo_config_owrt(config):
    ssid_suffix = ''
    json_content = ''
    adb_id = get_adb_id()
    if not adb_id:
        adb_id = ''
    if config == 'Test_SSID':
        ssid_suffix = '_Test'

    file_to_check = os.path.join(output_config_path, f'OWRT_TC_ondevice_3slo_{adb_id}{ssid_suffix}.json')
    template_file = os.path.join(template_path, 'OWRT_TC_ondevice_3slo_SDx75.json')       

    if not os.path.exists(file_to_check):
        with open(template_file, 'r') as f:
            json_content = f.read()
        updated_json_content = json_content.replace('_SLO', f'_SLO_{adb_id}{ssid_suffix}')
        with open(file_to_check, 'w') as f:
            f.write(updated_json_content)

    run_command("adb root")
    run_command(f"adb push {file_to_check} /data/dapp/TC_ondevice.json")
    run_command("adb reboot")

def update_2g5g_mlo_config_owrt(config):
    ssid_suffix = ''
    json_content = ''
    adb_id = get_adb_id()
    if not adb_id:
        adb_id = ''
    if config == 'Test_SSID':
        ssid_suffix = '_Test'

    file_to_check = os.path.join(output_config_path, f'OWRT_TC_ondevice_25mlo_{adb_id}{ssid_suffix}.json')
    template_file = os.path.join(template_path, 'OWRT_TC_ondevice_25mlo_SDx75.json')   

    if not os.path.exists(file_to_check):
        with open(template_file, 'r') as f:
            json_content = f.read()
        updated_json_content = json_content.replace('_MLO', f'_MLO_{adb_id}{ssid_suffix}')
        with open(file_to_check, 'w') as f:
            f.write(updated_json_content)
    
    run_command("adb root")
    run_command(f"adb push {file_to_check} /data/dapp/TC_ondevice.json")
    print("Pushed OWRT_TC_ondevice_25mlo.json")
    run_command("adb reboot")
    print("done")

def update_3_mlo_config_owrt(config):
    print("OWRT 3 MLO selected with test SSID")


def update_3_mlo_config_kobuk(config):
    print("Kobuk 3 MLO selected with test SSID")
    config_json = os.path.join(CTM_CONFIG_DIR, 'config.json')
    if config == "Test_SSID":
        mlo_config_json = os.path.join(CTM_CONFIG_DIR, 'mlo_config_test.json')
    else:
        mlo_config_json = os.path.join(CTM_CONFIG_DIR, 'mlo_config.json')

    if not os.path.exists(mlo_config_json):
        prefix = ""
        if config == "Test_SSID":
            prefix = "_test"

        _adb_id = get_adb_id()
        ssid = f"QSTAF_MLO_{_adb_id}{prefix}"

        mlo_json_data = {
            "4": {
                "command": "enableMLO",
                "input": {
                    "band_config": "2_5_6",
                    "ssid": ssid,
                    "encryption": "ccmp",
                    "password": "12345678",
                    "wpa3_flag": True,
                    "Metadata": {
                        "vpid": 0,
                        "start_delay": "0:1"
                    }
                }
            }
        }

        with open(mlo_config_json, "w") as json_file:
            json.dump(mlo_json_data, json_file, indent=4)

    if not os.path.exists(config_json):
        config_json_data = {
            "iteration_count": 1,
            "TC_list": ["TC1.json"],
            "Randomize": False,
            "Report_Headers": ["StepNo", "Itr", "seqno","subiteration", "command", "start_time", "end_time","result", "input", "vpid","blocking", "start_delay", "Metadata","file_size","time_taken_sec","throughput_bps"],
            "execute_once_api": ["enableMLO"],
            "qstaflog_max_size_MB": 5000
        }
        with open(config_json, "w") as json_file:
            json.dump(config_json_data, json_file, indent=4)

    run_command("adb shell mkdir /data/dapp/wlan")
    run_command("adb shell cp /data/dapp/qstaf.kb.* /data/dapp/wlan/")

    run_command(f"adb push {config_json} /data/dapp/wlan/")
    run_command(f"adb push {config_json} /")  # to be removed in next Dapp release
    run_command(f"adb push {mlo_config_json} /data/dapp/wlan/")
    if config == "Test_SSID":
        run_command(command=f"adb shell /data/dapp/wlan/qstaf.kb.* /data/dapp/wlan/mlo_config_test.json")
    else:
        run_command(command=f"adb shell /data/dapp/wlan/qstaf.kb.* /data/dapp/wlan/mlo_config.json")
    # run_command(f"adb shell /data/dapp/wlan/qstaf.kb.* /data/dapp/wlan/{mlo_config_json} /data/dapp/wlan/{config_json}")  # to be changed to in next Dapp release


def update_2_mlo_config_kobuk(config):
   # template_file = os.path.join(template_path, 'OWRT_TC_ondevice_2_mlo_KOBUK.json') 
   print("Kobuk 2 MLO selected with test SSID")


def update_3_slo_config_rdkb(config):
    ssid_suffix = ''
    adb_id = get_adb_id()
    if config == "Test":
        ssid_suffix = '_Test'
    slo_2g_ssid = f'QSTAF_2G_SLO_{adb_id}{ssid_suffix}'
    slo_5g_ssid = f'QSTAF_5G_SLO_{adb_id}{ssid_suffix}'
    slo_6g_ssid = f'QSTAF_6G_SLO_{adb_id}{ssid_suffix}'     
    run_command("adb root")
    commands = [
        # Break 5G+6G MLO -> into SLO links
        "dmcli eRT setv Device.WiFi.SSID.2.MLDUnit int -1",
        "dmcli eRT setv Device.WiFi.SSID.17.MLDUnit int -1",
        "dmcli eRT setv Device.WiFi.Radio.2.X_CISCO_COM_ApplySetting bool true",
        "dmcli eRT setv Device.WiFi.Radio.3.X_CISCO_COM_ApplySetting bool true",

        # Rename SSID names,
        f"dmcli eRT setv Device.WiFi.SSID.1.SSID string {slo_2g_ssid}",
        "dmcli eRT setv Device.WiFi.Radio.1.X_CISCO_COM_ApplySetting bool true",
       
        f"dmcli eRT setv Device.WiFi.SSID.2.SSID string {slo_5g_ssid}",
        "dmcli eRT setv Device.WiFi.Radio.2.X_CISCO_COM_ApplySetting bool true",
       
        f"dmcli eRT setv Device.WiFi.SSID.17.SSID string {slo_6g_ssid}",
        "dmcli eRT setv Device.WiFi.Radio.3.X_CISCO_COM_ApplySetting bool true"
    ]
    run_dmcli_commands(commands)
    if config == 'Config_SSID':
        setpassword_bandwidths_rdkb()

def update_2g_slo_5g6g_mlo_config_rdkb(config):
    ssid_suffix =''
    adb_id = get_adb_id()
    if config == "Test_SSID":
        ssid_suffix = '_test'
    slo_ssid = f'QSTAF_2G_SLO_{adb_id}{ssid_suffix}'
    mlo_ssid = f'QSTAF_MLO_{adb_id}{ssid_suffix}'
    commands = [
        f"dmcli eRT setv Device.WiFi.SSID.1.SSID string {slo_ssid}",
        "dmcli eRT setv Device.WiFi.Radio.1.X_CISCO_COM_ApplySetting bool true",
        
        f"dmcli eRT setv Device.WiFi.SSID.2.SSID string {mlo_ssid}",
        "dmcli eRT setv Device.WiFi.Radio.2.X_CISCO_COM_ApplySetting bool true",
        
        f"dmcli eRT setv Device.WiFi.SSID.17.SSID string {mlo_ssid}",
        "dmcli eRT setv Device.WiFi.Radio.3.X_CISCO_COM_ApplySetting bool true"
    ]
    run_dmcli_commands(commands)
    if config == 'Config_SSID':
        setpassword_bandwidths_rdkb()

def setpassword_bandwidths_rdkb():
    commands = [
        'dmcli eRT setv Device.WiFi.AccessPoint.1.Security.SAEPassphrase string "12345678"',
        'dmcli eRT setv Device.WiFi.Radio.1.X_CISCO_COM_ApplySetting bool true',
        
        'dmcli eRT setv Device.WiFi.AccessPoint.2.Security.SAEPassphrase string "12345678"',
        'dmcli eRT setv Device.WiFi.Radio.2.X_CISCO_COM_ApplySetting bool true',
        
        'dmcli eRT setv Device.WiFi.AccessPoint.17.Security.SAEPassphrase string "12345678"',
        'dmcli eRT setv Device.WiFi.Radio.3.X_CISCO_COM_ApplySetting bool true',
       
                                                                                                                         
        'dmcli eRT setv Device.WiFi.Radio.1.OperatingChannelBandwidth string 40MHz',
        'dmcli eRT setv Device.WiFi.Radio.1.X_CISCO_COM_ApplySetting bool true',
        

        'dmcli eRT setv Device.WiFi.Radio.2.OperatingChannelBandwidth string 160MHz',
        'dmcli eRT setv Device.WiFi.Radio.2.X_CISCO_COM_ApplySetting bool true',
        

        'dmcli eRT setv Device.WiFi.Radio.3.OperatingChannelBandwidth string 320MHz',
        'dmcli eRT setv Device.WiFi.Radio.3.X_CISCO_COM_ApplySetting bool true'
    ]
    run_dmcli_commands(commands)

def update_5g_slo_2g6g_mlo_config():
    pass

def update_6g_slo_2g5g_mlo_config():
    pass

def update_3_mlo_config():
    pass

def update_cpe_wifi_config(toggle_var,wifi_config,config):
    # Read Meta
    try:
        meta = get_meta_build_info()
    except Exception as e:
         raise Exception(e)

    if meta and 'LE.2.2' in meta:
        if toggle_var == 'RDKB':
            # RDKB, use dmcli commands

            if wifi_config == 0:
                update_3_slo_config_rdkb(config)
            elif wifi_config == 1:
                update_2g_slo_5g6g_mlo_config_rdkb(config)
            elif wifi_config == 2:
                #update_3_mlo_config_rdkb(config)
                pass

    elif meta and 'LE.1.2' in meta:
        if toggle_var == 'OWRT':
            # LE.1.2 - QCMAP_CLI
            if wifi_config == 0:
                update_3_slo_config_owrt(config)
            elif wifi_config == 1:
                update_2g5g_mlo_config_owrt(config)
            elif wifi_config == 2:
                update_3_mlo_config_owrt(config)

    elif toggle_var == 'Kobuk':
        if wifi_config == 0:
            update_3_mlo_config_kobuk(config)
        elif wifi_config == 1:
            update_2_mlo_config_kobuk(config)
         