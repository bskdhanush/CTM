import QSTAFInstaller
import os
import re
import subprocess
import shutil

PROV_BASE = r'C:\Dropbox\BuildLoadProvisioning\CTM_Prov_Base'
META_MPSS_TXT = os.path.join(PROV_BASE, 'META_MPSS.txt')
MPSS_BASE = r'C:\temp\mpss'
META_BASE = r'C:\temp\meta'

def update_mpss_in_config(mpss_path, meta_mpss_txt):
    with open(meta_mpss_txt, 'r') as f:
        lines = f.readlines()
    with open(meta_mpss_txt, 'w') as f:
        for line in lines:
            m = re.search(r'(.*KOBUK_MPSS\s*=\s*)(.*)\n', line)
            if m:
                f.write(f'{m.group(1)}{mpss_path}')
            else:
                f.write(line)

def update_meta_in_config(meta_path, meta_mpss_txt):
    with open(meta_mpss_txt, 'r') as f:
        lines = f.readlines()
    with open(meta_mpss_txt, 'w') as f:
        for line in lines:
            m = re.search(r'(.*KOBUK_META\s*=\s*)(.*)\n', line)
            if m:
                f.write(f'{m.group(1)}{meta_path}')
            else:
                f.write(line)

def set_meta_file_path(filepath):
    # Extract MPSS zip, update META_MPSS.txt and trigger load
    print(f"Meta path to be set on End to end script: {filepath}")
    if filepath.endswith(".7z"):
        META_ID = os.path.basename(filepath).strip(".7z")
    if filepath.endswith(".zip"):
        META_ID = os.path.basename(filepath).strip(".zip")

    META_PATH = os.path.join(META_BASE, META_ID)
    if os.path.exists(META_PATH):
        shutil.rmtree(META_PATH)
    os.makedirs(META_PATH)

    QSTAFInstaller._extract_zip(filepath, META_PATH) # type: ignore
    update_meta_in_config(META_PATH, META_MPSS_TXT)
    trigger_prov_meta(PROV_BASE)


def set_mpss_file_path(filepath):
    # Extract MPSS zip, update META_MPSS.txt and trigger load
    print(f"Mpss path to be set on End to end script: {filepath}")
    if filepath.endswith(".7z"):
        MPSS_ID = os.path.basename(filepath).strip(".7z")
    if filepath.endswith(".zip"):
        MPSS_ID = os.path.basename(filepath).strip(".zip")

    MPSS_PATH = os.path.join(MPSS_BASE, MPSS_ID)
    if os.path.exists(MPSS_PATH):
        shutil.rmtree(MPSS_PATH)
    os.makedirs(MPSS_PATH)

    QSTAFInstaller._extract_zip(filepath, MPSS_PATH) # type: ignore
    update_mpss_in_config(MPSS_PATH, META_MPSS_TXT)
    trigger_prov_mpss(PROV_BASE)

def trigger_prov_mpss(PROV_BASE):
    os.chdir(PROV_BASE)
    command = [
        'python', 'End_to_End_device_configuration.py',
        "--project", "2",
        "--option", "3",
        "--meta_option", "2",
        "--device_serial", "m"
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    print(f'MPSS Upgrade Result: {result.stdout}')

def trigger_prov_meta(PROV_BASE):
    os.chdir(PROV_BASE)
    command = [
        'python', 'End_to_End_device_configuration.py',
        "--project", "2",
        "--option", "2",
        "--meta_option", "2",
        "--device_serial", "m"
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    print(f'Meta Upgrade Result: {result.stdout}')


def load_qcn():
    print("Load QCN triggered")
    pass
    
def activate_mbn(selected_mbn):
    print(f"Selected MBN to activate: {selected_mbn}")
    pass
    
def deactivate_mbn(selected_mbn):
    print(f"Selected MBN to deactivate: {selected_mbn}")
    pass
    
def write_nv():
    print("Write NV triggered")
    pass
    
def full_provisioning():
    print("Full Provisioning triggered")
    pass