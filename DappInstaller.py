import os
import QSTAFInstaller
from pathlib import Path
import re
import WifiController,StartTestCase
from Constants import CTM_DAPP_DIR


def InstallDapp(archive_path: str, DappInstallerType:str) -> None:
    if DappInstallerType=="Zip":
        archivepath = Path(archive_path)
        print(archive_path)
        if not archivepath.exists() or archivepath.suffix.lower() not in (".zip", ".7z"):
            print(f"Invalid archive (expected .zip or .7z): {archive_path}")
        folder_path = Path(r"C:\CTM\DAPP")



        QSTAFInstaller._extract_archive(archivepath,folder_path ,None,"Dapp")
        folder_name = Path(archive_path).stem
        extracted_folder = folder_path.with_suffix('') 
        TC_ondevice_path = extracted_folder / folder_name / "kobuk" / "testcase" / "TC_ondevice.txt"
    else:
        #folder_path = Path(r"C:\CTM\DAPP")
        folder_name = Path(archive_path)
        extracted_folder = folder_name.with_suffix('') 
        print(archive_path)
        TC_ondevice_path =  folder_name / "kobuk" / "testcase" / "TC_ondevice.txt"


    try:
        print(" folder:", extracted_folder)
        print("TC_ondevice_path:", TC_ondevice_path)
        replace_ADB_TC_ondevice(TC_ondevice_path,extracted_folder)
        #print("Extracted to:", TC_ondevice_path)
    except Exception as e:
        print("Error:", str(e))

def replace_ADB_TC_ondevice(TC_ondevice_path: Path, extracted_folder) -> None:
    if not TC_ondevice_path.exists():
        raise FileNotFoundError(f"Extracted folder not found: {TC_ondevice_path}")
    
    content = TC_ondevice_path.read_text()
    ADBId=WifiController.get_adb_id()
    if not ADBId:
        return 
    Replacment_sting = "QSTAF_MLO_"+ADBId
    updated_content = re.sub(r"QSTAF_MLO_\w+", Replacment_sting, content)
    TC_ondevice_path.write_text(updated_content)
    StartTestCase.start_tests(str(extracted_folder), "kobuk_install.bat", "Dapp_Installer")
    

if __name__ == "__main__":
    InstallDapp(r"D:\work\GUI\Kobuk_CPE_1.0_v1.0.5.7z","Zip")
    