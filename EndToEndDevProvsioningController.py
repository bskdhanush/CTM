import os
import re
import time
import subprocess
import shutil
import QSTAFInstaller
import py7zr
from pathlib import Path
from WifiController import get_adb_id, run_command
from JsonHandler import load_prov_json
from Constants import CTM_META_DIR, CTM_MPSS_DIR


def get_provisioning_base():
    cfg = load_prov_json()
    if cfg.get('provisioning_path') and cfg.get('provisioning_path') != 'No path Selected':
        return cfg.get('provisioning_path')
    else:
        print(f'provisioning_path is not configured. Please check')
        return None

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

def load_meta_from_path(filepath,Pgname):
    # Update filepath for Meta in META_MPSS.txt and trigger load
    if filepath=="":
        return
    PROV_BASE = get_provisioning_base()
    if PROV_BASE:
        META_MPSS_TXT = os.path.join(PROV_BASE, 'META_MPSS.txt')
        filepath = os.path.normpath(filepath)
        print(f'Meta Path: {filepath}')
        update_meta_in_config(filepath, META_MPSS_TXT)
        if Pgname:
            trigger_prov_meta(PROV_BASE)

def load_meta_from_zip(filepath,Pgname):
    if filepath=="":
        return
    # Extract META zip, update META_MPSS.txt and trigger load
    print(f"Meta zip: {filepath}")
    PROV_BASE = get_provisioning_base()
    if PROV_BASE:
        META_MPSS_TXT = os.path.join(PROV_BASE, 'META_MPSS.txt')
        META_ID = ''
        if filepath.endswith(".7z"):
            META_ID = os.path.basename(filepath).strip(".7z")
        if filepath.endswith(".zip"):
            META_ID = os.path.basename(filepath).strip(".zip")
        META_PATH = os.path.join(CTM_META_DIR, META_ID)



        remove_dir(META_PATH)
        os.makedirs(META_PATH)
        
        if filepath.endswith(".7z"):
            print("Starting 7z extraction... This may take several minutes for large files")
            QSTAFInstaller._extract_7z_with_cli(filepath, Path(META_PATH)) 
            print("Extraction completed")
        elif filepath.endswith(".zip"):
            QSTAFInstaller._extract_zip(filepath, Path(META_PATH))
        update_meta_in_config(META_PATH, META_MPSS_TXT)
        # if its from meta triger else just update the meta_mpss_txt
        print(Pgname)
        if Pgname:
            trigger_prov_meta(PROV_BASE)

def load_mpss_from_path(filepath,Pgname):
    if filepath=="":
        return
    # Update filepath for MPSS in META_MPSS.txt and trigger load
    PROV_BASE = get_provisioning_base()
    if PROV_BASE:
        META_MPSS_TXT = os.path.join(PROV_BASE, 'META_MPSS.txt')
        filepath = os.path.normpath(filepath)
        print(f'MPSS Path: {filepath}')
        update_mpss_in_config(filepath, META_MPSS_TXT)
        if Pgname:
            trigger_prov_mpss(PROV_BASE)

def load_mpss_from_zip(filepath,Pgname):
    if filepath=="":
        return
    # Extract MPSS zip, update META_MPSS.txt and trigger load
    print(f"Mpss zip: {filepath}")
    PROV_BASE = get_provisioning_base()
    if PROV_BASE:
        META_MPSS_TXT = os.path.join(PROV_BASE, 'META_MPSS.txt')
        MPSS_ID = ''
        if filepath.endswith(".7z"):
            MPSS_ID = os.path.basename(filepath).strip(".7z")
        if filepath.endswith(".zip"):
            MPSS_ID = os.path.basename(filepath).strip(".zip")
        MPSS_PATH = os.path.join(CTM_MPSS_DIR, MPSS_ID)
        remove_dir(MPSS_PATH)
        os.makedirs(MPSS_PATH)

        if filepath.endswith(".7z"):
            print("Starting 7z extraction... This may take several minutes for large files")
            QSTAFInstaller._extract_7z_with_cli(filepath, Path(MPSS_PATH)) 
            print("Extraction completed")
        elif filepath.endswith(".zip"):
            QSTAFInstaller._extract_zip(filepath, Path(MPSS_PATH))
        update_meta_in_config(MPSS_PATH, META_MPSS_TXT)
        # if its from Mpss triger else just update the meta_mpss_txt
        if Pgname:
            trigger_prov_meta(PROV_BASE)
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
    PROV_BASE = get_provisioning_base()
    if PROV_BASE:
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

def activate_mbn(operator,Pgname):
    PROV_BASE = get_provisioning_base()
    if PROV_BASE:
        META_MPSS_TXT = os.path.join(PROV_BASE, 'META_MPSS.txt')
        os.chdir(PROV_BASE)
        operator_dict = {
            'TMO': 'Commercial-TMO',
            'VZW': 'CDMAless-Verizon',
            'ATT': 'VoLTE-ATT'
        }
        if operator_dict.get(operator):
            update_mbn_in_config(operator_dict.get(operator), META_MPSS_TXT)
            if Pgname:
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
    PROV_BASE = get_provisioning_base()
    if PROV_BASE:
        os.chdir(PROV_BASE)
        command = [
            'python', 'End_to_End_device_configuration.py',
            "--Project", "2",
            "--option", "6",
            "--meta_option", "2",
            "--device_serial", "m"
        ]
        subprocess.run(command, shell=True)
        print("NV Load launched in a new cmd prompt")
    
def full_provisioning():
    PROV_BASE = get_provisioning_base()
    if PROV_BASE:
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
    PROV_BASE = get_provisioning_base()
    if PROV_BASE:
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


def get_data_Meta_Mpss_txt():
    PROV_BASE = get_provisioning_base()
    if PROV_BASE:
        META_MPSS_TXT = os.path.join(PROV_BASE, 'META_MPSS.txt')
        config = {}
        with open(META_MPSS_TXT, 'r') as file:
            for line in file:
                line = line.strip()  # Remove whitespace
                if '=' in line:  # Check if line contains '='
                    key, value = line.split('=', 1)  # Split at first '='
                    config[key.strip()] = value.strip()
    return config

  
