import os
import QSTAFInstaller
from pathlib import Path
import re
import WifiController,StartTestCase

def InstallDapp(archive_path: str) -> None:
    apath = Path(archive_path)
    if not apath.exists() or apath.suffix.lower() not in (".zip", ".7z"):
        print(f"Invalid archive (expected .zip or .7z): {archive_path}")

    folder_path = Path(os.path.dirname(archive_path))

    QSTAFInstaller._extract_archive(apath,folder_path ,None,"Dapp")

    try:
        extracted_folder = apath.with_suffix('') 
        TC_ondevice_path = extracted_folder / "kobuk" / "testcase" / "TC_ondevice.txt"
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
    InstallDapp(r"D:\work\GUI\Kobuk_CPE_1.0_v1.0.5.7z")
    