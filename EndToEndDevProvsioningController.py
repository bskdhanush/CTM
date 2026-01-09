import os
import re
import textwrap
import time
import subprocess
import shutil
import QSTAFInstaller
from pathlib import Path
from CheckDeviceProvsionStatus import check_META_install_status,check_MPSS_install_status
from WifiController import get_adb_id, run_command, get_meta_build_info
from JsonHandler import load_prov_json
from Constants import CTM_META_DIR, CTM_MPSS_DIR
import py7zr


def get_project_name():
    project = None
    meta_build = get_meta_build_info()
    if isinstance(meta_build, str) and 'kobuk' in meta_build.lower():
        project = "2"
    elif isinstance(meta_build, str) and 'pinnacles' in meta_build.lower():
        project = "1"
    else:
        print("Kobuk or Pinnacles Meta NOT detected from device")
    return project

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
    meta_build = get_meta_build_info()
    pattern = None
    if meta_build:
        if 'kobuk' in meta_build.lower():
            pattern = "(.*KOBUK_MPSS\s*=\s*).*(\s*)"
        elif 'pinnacles' in meta_build.lower():
            pattern = "(.*PINNACLES_MPSS\s*=\s*).*(\s*)"

        if pattern:
            with open(meta_mpss_txt, 'r') as f:
                lines = f.readlines()
            with open(meta_mpss_txt, 'w') as f:
                for line in lines:
                    # m = re.search(r'(.*KOBUK_MPSS\s*=\s*).*(\s*)', line)
                    m = re.search(f'{pattern}', line)
                    if m:
                        f.write(f'{m.group(1)}{mpss_path}{m.group(2)}')
                    else:
                        f.write(line)
        else:
            print(f"update_mpss_in_config: pattern not found in {meta_mpss_txt}")
    else:
        print("update_mpss_in_config: MPSS Build info not found")

def update_meta_in_config(meta_path, meta_mpss_txt):
    meta_build = get_meta_build_info()
    pattern = None
    if meta_build:
        if 'kobuk' in meta_build.lower():
            pattern = "(.*KOBUK_META\s*=\s*).*(\s*)"
        elif 'pinnacles' in meta_build.lower():
            pattern = "(.*PINNACLES_META\s*=\s*).*(\s*)"

        if pattern:
            with open(meta_mpss_txt, 'r') as f:
                lines = f.readlines()
            with open(meta_mpss_txt, 'w') as f:
                for line in lines:
                    # m = re.search(r'(.*KOBUK_META\s*=\s*).*(\s*)', line)
                    m = re.search(f"{pattern}", line)
                    if m:
                        f.write(f'{m.group(1)}{meta_path}{m.group(2)}')
                    else:
                        f.write(line)
        else:
            print(f"update_meta_in_config: pattern not found in {meta_mpss_txt}")
    else:
        print("update_meta_in_config: Meta Build info not found")



def load_meta_from_path(filepath,Pgname):
    # Update filepath for Meta in META_MPSS.txt and trigger load
    if filepath == "":
        return
    PROV_BASE = get_provisioning_base()
    if PROV_BASE:
        META_MPSS_TXT = os.path.join(PROV_BASE, 'META_MPSS.txt')
        filepath = os.path.normpath(filepath)
        print(f'Meta Path: {filepath}')
        update_meta_in_config(filepath, META_MPSS_TXT)
        if Pgname:
            trigger_prov_meta(PROV_BASE)

def load_meta_from_zip(filepath,Pgname,status_lable):
    if filepath == "":
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
        status_lable.set(f"Pls wait,Unzipping META to: {filepath}")
        if filepath.endswith(".7z"):
            try:
                print("Starting 7z extraction... This may take several minutes for large files")
               # QSTAFInstaller._extract_7z_with_cli(filepath, Path(CTM_META_DIR))
                with py7zr.SevenZipFile(filepath, mode="r") as z:z.extractall(path=CTM_META_DIR)
                status_lable.set("Extraction completed")
            except Exception as e:   
                status_lable.set(f"faild to unzip {e}")
                return
        elif filepath.endswith(".zip"):
            try:
                QSTAFInstaller._extract_zip(filepath, Path(CTM_META_DIR))
                status_lable.set("Extraction completed")
            except Exception as e:   
                status_lable.set(f"faild to unzip {e}")
                return
                
        update_meta_in_config(META_PATH, META_MPSS_TXT)
        # if its from meta triger else just update the meta_mpss_txt
        #print(Pgname)
        status_lable.set(f"Unzipping Done")
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

def load_mpss_from_zip(filepath,Pgname,status_lable):
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
        status_lable.set(f"Pls wait,Unzipping Mpss to: {filepath}")

        if filepath.endswith(".7z"):
            try:
                print("Starting 7z extraction... This may take several minutes for large files")
                #QSTAFInstaller._extract_7z_with_cli(filepath, Path(CTM_MPSS_DIR))
                with py7zr.SevenZipFile(filepath, mode="r") as z:z.extractall(path=CTM_MPSS_DIR)
                status_lable.set("Extraction completed")
            except Exception as e:   
                status_lable.set(f"faild to unzip {e}")
                return
                
        elif filepath.endswith(".zip"):
            try:
                QSTAFInstaller._extract_zip(filepath, Path(CTM_MPSS_DIR))
                status_lable.set(f"Unzipping Done")
            except Exception as e:
                status_lable.set(f"faild to unzip {e}")
                return
                
        update_mpss_in_config(MPSS_PATH, META_MPSS_TXT)
        # if its from Mpss triger else just update the meta_mpss_txt
        if Pgname:
            trigger_prov_mpss(PROV_BASE)
            
def trigger_prov_mpss(PROV_BASE):
    os.chdir(PROV_BASE)
    remove_dir(os.path.join(PROV_BASE, 'MPSS'))
    project = get_project_name()
    adb_id = None
    try:
        adb_id = get_adb_id()
    except Exception as e:
        print(f'Exception during get_adb_id: {e}')
    if adb_id and project:
        remove_dir(os.path.join(PROV_BASE, adb_id)) # type: ignore

        command = [
            'python', 'End_to_End_device_configuration.py',
            "--project", project,
            "--option", "3",
            "--meta_option", "2",
            "--device_serial", "m"
        ]
        subprocess.run(command, shell=True)
        print("MPSS Upgrade launched in a new cmd prompt")
        check_MPSS_install_status(PROV_BASE)

def trigger_prov_meta(PROV_BASE):
    project = get_project_name()
    if project:
        os.chdir(PROV_BASE)
        command = [
            'python', 'End_to_End_device_configuration.py',
            "--project", project,
            "--option", "2",
            "--meta_option", "2",
            "--device_serial", "m"
        ]
        subprocess.run(command, shell=True)
        print("Meta Upgrade launched in a new cmd prompt")
        check_META_install_status(PROV_BASE,"Meta")


def load_qcn():
    project = get_project_name()
    PROV_BASE = get_provisioning_base()
    if PROV_BASE and project:
        os.chdir(PROV_BASE)
        command = [
            'python', 'End_to_End_device_configuration.py',
            "--project", project,
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
    project = get_project_name()
    PROV_BASE = get_provisioning_base()
    if PROV_BASE and project:
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
                    "--project", project,
                    "--option", "5",
                    "--meta_option", "2",
                    "--device_serial", "m"
                ]
                subprocess.run(command, shell=True)
                print("MBN Activation launched in a new cmd prompt")
    
def deactivate_mbn():
    pass
    
def write_nv():
    project = get_project_name()
    PROV_BASE = get_provisioning_base()
    if PROV_BASE and project:
        os.chdir(PROV_BASE)
        command = [
            'python', 'End_to_End_device_configuration.py',
            "--project", project,
            "--option", "6",
            "--meta_option", "2",
            "--device_serial", "m"
        ]
        subprocess.run(command, shell=True)
        print("NV Load launched in a new cmd prompt")

def load_efs():
    project = get_project_name()
    PROV_BASE = get_provisioning_base()
    if PROV_BASE and project:
        os.chdir(PROV_BASE)
        command = [
            'python', 'End_to_End_device_configuration.py',
            "--project", project,
            "--option", "7",
            "--meta_option", "2",
            "--device_serial", "m"
        ]
        subprocess.run(command, shell=True)
        print('Load_EFS launched in a new cmd prompt')

def full_provisioning(meta_selection=True, mpss_selection=True):
    project = get_project_name()
    PROV_BASE = get_provisioning_base()
    option = ""
    if meta_selection:
        option = "2,"
    if mpss_selection:
        option = f"{option}3,"
    option = f"{option}4,5,6"
    if PROV_BASE and project:
        os.chdir(PROV_BASE)
        command = [
            'python', 'End_to_End_device_configuration.py',
            "--project", project,
            "--option", option,
            "--meta_option", "2",
            "--device_serial", "m"
        ]
        subprocess.run(command, shell=True)
        print("Full Provisioning launched in a new cmd prompt")
        check_META_install_status(PROV_BASE,"Full")

       
        

def load_fota(filepath):
    # Push FOTA zip to device and trigger load in recovery mode
    print(f"FOTA Zip: {filepath}")
    project = get_project_name()
    PROV_BASE = get_provisioning_base()
    if PROV_BASE and project == '2':
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
    config = {}
    PROV_BASE = get_provisioning_base()
    if PROV_BASE:
        META_MPSS_TXT = os.path.join(PROV_BASE, 'META_MPSS.txt')
        try: 
            with open(META_MPSS_TXT, 'r') as file:
                for line in file:
                    line = line.strip()  # Remove whitespace
                    if '=' in line:  # Check if line contains '='
                        key, value = line.split('=', 1)  # Split at first '='
                        config[key.strip()] = value.strip()
        except Exception as e:
            print(f'No path selected for Provisioning : {e}')
    
    return config

def get_device_config_txt():
    config = {}
    adb_id = get_adb_id()
    PROV_BASE = get_provisioning_base()
    
    if PROV_BASE and adb_id:
        CONFIG_TXT = os.path.join(PROV_BASE, 'QCN', adb_id, 'config.txt')
        try:
            with open(CONFIG_TXT, 'r') as file:
                for line in file:
                    line = line.strip()  # Remove whitespace
                    if ':' in line:  # Check if line contains ':'
                        key, value = line.split(':', 1)  # Split at first ':'
                        key = key.strip()
                        value = value.strip()
                        
                        # Handle duplicate keys by storing values in a list
                        if key in config:
                            # Key already exists, append to list
                            if isinstance(config[key], list):
                                config[key].append(value)
                            else:
                                # Convert single value to list
                                config[key] = [config[key], value]
                        else:
                            # First occurrence of this key
                            config[key] = value
                            
        except Exception as e:
            print(f'No path selected for Provisioning : {e}')
    else:
        print(f'Valid PROV_BASE or adb_id not found')
    
    return config
  
  
  
  
def wrap_long_text(text, max_chars=90):
    """Wrap text to multiple lines if it exceeds max_chars"""
    if len(str(text)) > max_chars:
        return '\n'.join(textwrap.wrap(str(text), width=max_chars))
    return text
