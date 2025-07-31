import subprocess
import time
import WifiController 



if __name__ == "__main__":

#print(f"ADB ID: {adbid}")
    while True:
        adbid= WifiController.get_adb_id()
        time.sleep(1)
        if adbid == None:
            print("dev not found")
        else:
            print(f"ADB ID: {adbid}")
