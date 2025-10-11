import os
import re
import time
import subprocess
import shutil
import QSTAFInstaller
from WifiController import get_adb_id, run_command

# To-do: Set PROV_BASE from json. Update json from user selected path from UI
PROV_BASE = r'C:\Dropbox\BuildLoadProvisioning\CTM_Prov_Base'
META_MPSS_TXT = os.path.join(PROV_BASE, 'META_MPSS.txt')
MPSS_BASE = r'C:\temp\mpss'
META_BASE = r'C:\temp\meta'

def remove_dir(dir):
    if os.path.exists(dir):
        try:
            shutil.rmtree(dir)
        except Exception as e:
            print(f'Exception during remove_dir({dir}): {e}')

def update_mpss_in_config(mpss_path, meta_mpss_txt):
    with open(meta_mpss_txt, 'r') as f:
        lines = f.readlines()
    with open(meta_mpss_txt, 'w') as f:
        for line in lines:
            m = re.search(r'(.*KOBUK_MPSS\s*=\s*).*(\s*)', line)
            if m:
                f.write(f'{m.group(1)}{mpss_path}{m.group(2)}')
            else:
                f.write(line)

def update_meta_in_config(meta_path, meta_mpss_txt):
    with open(meta_mpss_txt, 'r') as f:
        lines = f.readlines()
    with open(meta_mpss_txt, 'w') as f:
        for line in lines:
            m = re.search(r'(.*KOBUK_META\s*=\s*).*(\s*)', line)
            if m:
                f.write(f'{m.group(1)}{meta_path}{m.group(2)}')
            else:
                f.write(line)

def load_meta_from_path(filepath):
    # Update filepath for Meta in META_MPSS.txt and trigger load
    filepath = os.path.normpath(filepath)
    print(f'Meta Path: {filepath}')
    update_meta_in_config(filepath, META_MPSS_TXT)
    trigger_prov_meta(PROV_BASE)

def load_meta_from_zip(filepath):
    # Extract META zip, update META_MPSS.txt and trigger load
    print(f"Meta zip: {filepath}")
    if filepath.endswith(".7z"):
        META_ID = os.path.basename(filepath).strip(".7z")
    if filepath.endswith(".zip"):
        META_ID = os.path.basename(filepath).strip(".zip")

    META_PATH = os.path.join(META_BASE, META_ID)
                                 
    remove_dir(META_PATH)
    os.makedirs(META_PATH)

    QSTAFInstaller._extract_zip(filepath, META_PATH) # type: ignore
    update_meta_in_config(META_PATH, META_MPSS_TXT)
    trigger_prov_meta(PROV_BASE)

def load_mpss_from_path(filepath):
    # Update filepath for MPSS in META_MPSS.txt and trigger load
    filepath = os.path.normpath(filepath)
    print(f'MPSS Path: {filepath}')
    update_mpss_in_config(filepath, META_MPSS_TXT)
    trigger_prov_mpss(PROV_BASE)

def load_mpss_from_zip(filepath):
    # Extract MPSS zip, update META_MPSS.txt and trigger load
    print(f"Mpss zip: {filepath}")
    if filepath.endswith(".7z"):
        MPSS_ID = os.path.basename(filepath).strip(".7z")
    if filepath.endswith(".zip"):
        MPSS_ID = os.path.basename(filepath).strip(".zip")

    MPSS_PATH = os.path.join(MPSS_BASE, MPSS_ID)
    remove_dir(MPSS_PATH)
    os.makedirs(MPSS_PATH)

    QSTAFInstaller._extract_zip(filepath, MPSS_PATH) # type: ignore
    update_mpss_in_config(MPSS_PATH, META_MPSS_TXT)
    trigger_prov_mpss(PROV_BASE)

def trigger_prov_mpss(PROV_BASE):
    os.chdir(PROV_BASE)
    remove_dir(os.path.join(PROV_BASE, 'MPSS'))
    try:
        adb_id = get_adb_id()
    except Exception as e:
        print(f'Exception during get_adb_id: {e}')
    remove_dir(os.path.join(PROV_BASE, adb_id)) # type: ignore

    command = [
        'python', 'End_to_End_device_configuration.py',
        "--project", "2",
        "--option", "3",
        "--meta_option", "2",
        "--device_serial", "m"
    ]
    subprocess.run(command, shell=True)
    print("MPSS Upgrade launched in a new cmd prompt")

def trigger_prov_meta(PROV_BASE):
    os.chdir(PROV_BASE)
    command = [
        'python', 'End_to_End_device_configuration.py',
        "--project", "2",
        "--option", "2",
        "--meta_option", "2",
        "--device_serial", "m"
    ]
    subprocess.run(command, shell=True)
    print("Meta Upgrade launched in a new cmd prompt")


def load_qcn():
    os.chdir(PROV_BASE)
    command = [
        'python', 'End_to_End_device_configuration.py',
        "--project", "2",
        "--option", "4",
        "--meta_option", "2",
        "--device_serial", "m"
    ]
    subprocess.run(command, shell=True)
    print('Load_QCN launched in a new cmd prompt')


def update_mbn_in_config(mbn, meta_mpss_txt):
    with open(meta_mpss_txt, 'r') as f:
        lines = f.readlines()
    with open(meta_mpss_txt, 'w') as f:
        for line in lines:
            m = re.search(r'(.*MBN_SW\s*=\s*).*(\s*)', line)
            if m:
                f.write(f'{m.group(1)}{mbn}{m.group(2)}')
            else:
                f.write(line)

def activate_mbn(operator):
    os.chdir(PROV_BASE)
    operator_dict = {
        'TMO': 'Commercial-TMO',
        'VZW': 'CDMAless-Verizon',
        'ATT': 'VoLTE-ATT'
    }
    if operator_dict.get(operator):
        update_mbn_in_config(operator_dict.get(operator), META_MPSS_TXT)
        command = [
            'python', 'End_to_End_device_configuration.py',
            "--project", "2",
            "--option", "5",
            "--meta_option", "2",
            "--device_serial", "m"
        ]
        subprocess.run(command, shell=True)
        print("MBN Activation launched in a new cmd prompt")
    
def deactivate_mbn():
    pass
    
def write_nv():
    os.chdir(PROV_BASE)
    command = [
        'python', 'End_to_End_device_configuration.py',
        "--project", "2",
        "--option", "6",
        "--meta_option", "2",
        "--device_serial", "m"
    ]
    subprocess.run(command, shell=True)
    print("NV Load launched in a new cmd prompt")
    
def full_provisioning():
    os.chdir(PROV_BASE)
    command = [
        'python', 'End_to_End_device_configuration.py',
        "--project", "2",
        "--option", "2,3,4,5,6",
        "--meta_option", "2",
        "--device_serial", "m"
    ]
    subprocess.run(command, shell=True)
    print("Full Provisioning launched in a new cmd prompt")

def load_fota(filepath):
    # Push FOTA zip to device and trigger load in recovery mode
    print(f"FOTA Zip: {filepath}")
    os.chdir(PROV_BASE)
    if not os.path.exists('command'):
        print(f'FOTA-command does not exist in {PROV_BASE}. Please check.')
    else:
        run_command(f"adb push command /cache/recovery/command")
        run_command(f"adb push {filepath} /data/update.zip")
        run_command('adb reboot recovery')
        time.sleep(1)
        ref_time = time.time()
        while get_adb_id() is None and time.time() < ref_time + 60:
            time.sleep(1)
        if get_adb_id():
            print(f'FOTA upgraded successfully')
        else:
            print(f'FOTA upgrade failed')