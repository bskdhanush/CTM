import time
import subprocess
import re

adb_id = None




def run_command(command):
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
            m = re.search(r'(\w+)\s*device$', output)
            if m:
                adb_id = m.group(1)
    return adb_id

def get_meta_build_info():
    meta = None
    output, stderr = run_command("adb wait-for-device shell cat /firmware/verinfo/Ver_Info.txt | findstr Meta_Build_ID")
    if not output or stderr:
        raise Exception('Meta Build info NOT FOUND')
    else:
        meta = output.split(': ')[1].strip(',')
    return meta

def get_mpss_build_info():
    mpss = None
    output, stderr = run_command("adb wait-for-device shell cat /sys/devices/soc0/images | findstr 11:")
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
        run_command(f"adb wait-for-device shell {command}")
        time.sleep(1)


def connectBackhall():
    run_command("adb root")
    commands = [
	"dmcli eRT setv Device.Cellular.AccessPoint.1.Apn string fast.t-mobile.com",
    "sleep 2",
	"dmcli eRT setv Device.Cellular.AccessPoint.1.X_QCOM.ConnectBackHaul bool true",
	"sleep 2",
	"dmcli eRT setv Device.Cellular.X_QCOM.AutoConnect bool true",
	"sleep 2"
    ]
    run_dmcli_commands(commands)
    
def update_3_slo_config(Config):
    ssid_suffix =''
    adb_id = get_adb_id()
    if Config!="":
        ssid_suffix='_Test'
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

def update_2g_slo_5g6g_mlo_config(Config):
    ssid_suffix =''
    adb_id = get_adb_id()
    if Config!="":
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

def setpassword_bandwiths():
    commands = [
    'dmcli eRT setv Device.WiFi.AccessPoint.1.Security.SAEPassphrase string "12345678"',
    'sleep 2',
    'dmcli eRT setv Device.WiFi.Radio.1.X_CISCO_COM_ApplySetting bool true',
    'sleep 2',

    'dmcli eRT setv Device.WiFi.AccessPoint.2.Security.SAEPassphrase string "12345678"',
    'sleep 2',
    'dmcli eRT setv Device.WiFi.Radio.2.X_CISCO_COM_ApplySetting bool true',
    'sleep 2',

    'dmcli eRT setv Device.WiFi.AccessPoint.17.Security.SAEPassphrase string "12345678"',
    'sleep 2',
    'dmcli eRT setv Device.WiFi.Radio.3.X_CISCO_COM_ApplySetting bool true',
    'sleep 2',

    # ── bandwidth configuration ────────────────────────────
    'dmcli eRT setv Device.WiFi.Radio.1.OperatingChannelBandwidth string 40MHz',
    'sleep 2',
    'dmcli eRT setv Device.WiFi.Radio.1.X_CISCO_COM_ApplySetting bool true',
    'sleep 2',

    'dmcli eRT setv Device.WiFi.Radio.2.OperatingChannelBandwidth string 160MHz',
    'sleep 2',
    'dmcli eRT setv Device.WiFi.Radio.2.X_CISCO_COM_ApplySetting bool true',
    'sleep 2',

    'dmcli eRT setv Device.WiFi.Radio.3.OperatingChannelBandwidth string 320MHz',
    'sleep 2',
    'dmcli eRT setv Device.WiFi.Radio.3.X_CISCO_COM_ApplySetting bool true',
    'sleep 2',
    ]
    run_dmcli_commands(commands)

def update_5g_slo_2g6g_mlo_config():
    pass

def update_6g_slo_2g5g_mlo_config():
    pass

def update_3_mlo_config():
    pass

def update_cpe_wifi_config(wifi_config,config):
    # Read Meta
    try:
        meta = get_meta_build_info()
    except Exception as e:
        raise Exception(e)

    if meta and 'LE.2.2' in meta:
        # RDKB, use dmcli commands

        if wifi_config == 0:
            update_3_slo_config(config)
        elif wifi_config == 1:
            update_2g_slo_5g6g_mlo_config(config)

    elif meta and 'LE.1.2' in meta:
        # LE.1.2 - QCMAP_CLI
        pass