import os
import QSTAFInstaller
from pathlib import Path
import re
import WifiController,StartTestCase
from Constants import CTM_DAPP_DIR


def InstallDapp(archive_path: str, DappInstallerType:str) -> None:
    device_type = None
    meta_build = WifiController.get_meta_build_info()
    if isinstance(meta_build, str) and 'kobuk' in meta_build.lower():
        device_type = 'kobuk'
    elif isinstance(meta_build, str) and 'pinnacles.le.2.2' in meta_build.lower():
        device_type = 'pinnacle_le_2_2'
    elif isinstance(meta_build, str) and 'pinnacles.le.1.2' in meta_build.lower():
        device_type = 'pinnacle'

    if device_type:
        TC_ondevice_path = None
        if DappInstallerType=="Zip":
            archivepath = Path(archive_path)
            print(archive_path)
            if not archivepath.exists() or archivepath.suffix.lower() not in (".zip", ".7z"):
                print(f"Invalid archive (expected .zip or .7z): {archive_path}")
            folder_path = Path(r"C:\CTM\DAPP")

            QSTAFInstaller._extract_archive(archivepath,folder_path ,None,"Dapp")
            folder_name = Path(archive_path).stem
            extracted_folder = folder_path.with_suffix('')
            if os.path.exists(os.path.join(extracted_folder, folder_name, device_type)):
                TC_ondevice_path = extracted_folder / folder_name / device_type / "testcase" / "TC_ondevice.txt"
                extracted_folder = os.path.join(extracted_folder, folder_name)
            else:
                print("DAPP selected is not compatible with the device")

        else:
            extracted_folder = Path(archive_path)
            print(extracted_folder)
            if os.path.exists(os.path.join(extracted_folder, device_type)):
                TC_ondevice_path = extracted_folder / device_type / "testcase" / "TC_ondevice.txt"
            else:
                print("DAPP selected is not compatible with the device")

        try:
            print(" folder:", extracted_folder)
            if TC_ondevice_path:
                print("TC_ondevice_path:", TC_ondevice_path)
                replace_ADB_TC_ondevice(TC_ondevice_path, extracted_folder, device_type)
        except Exception as e:
            print(f"Exception during replace_ADB_TC_ondevice: {e}")
    else:
        print('DAPP could not be installed, since device_type could not be determined')

def replace_ADB_TC_ondevice(TC_ondevice_path: Path, extracted_folder, device_type) -> None:
    if not TC_ondevice_path.exists():
        raise FileNotFoundError(f"Extracted folder not found: {TC_ondevice_path}")
    
    content = TC_ondevice_path.read_text()
    ADBId=WifiController.get_adb_id()
    if not ADBId:
        return 
    Replacment_sting = "QSTAF_MLO_"+ADBId
    updated_content = re.sub(r"QSTAF_MLO_\w+", Replacment_sting, content)
    TC_ondevice_path.write_text(updated_content)
    StartTestCase.start_tests(str(extracted_folder), f"{device_type}_install.bat", "Dapp_Installer")
    

if __name__ == "__main__":
    InstallDapp(r"D:\work\GUI\Kobuk_CPE_1.0_v1.0.5.7z","Zip")
    