import paramiko
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

HOST = os.getenv("SFTP_HOST")
PORT = int(os.getenv("SFTP_PORT", 22))  # usually 21
USER = os.getenv('SFTP_USER')
PASS = os.getenv("SFTP_PASS")

remote_path="/CPE-Markets/LV/"
local_path="D:/work/GUI/Quts_tool"



def get_lates_meta(items):
    pass



def get_files(sftp, transport):
    if sftp is not None:
        print("Connected successfully to SFTP server.")

        for item in sftp.listdir_attr(remote_path):
            filename = item.filename
            modified_time = item.st_mtime
            if modified_time is not None:
                date = datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d %H:%M:%S")
            else:
                date = "Unknown"
            if item.filename.startswith('v') or item.filename.startswith('Kobuk') or item.filename.startswith('Pinnacle'):
                print(f"{filename} - {date}")
            
            remote_file_path = os.path.join(remote_path, "v4.7.2.7z")
        download_file(sftp,transport, remote_file_path,local_path)



import os

def download_file(sftp, transport, remote_file_path, local_path):
    try:
        filename = os.path.basename(remote_file_path)  # Extract filename
        full_local_path = os.path.join(local_path, filename)  # Full local path
        sftp.get(remote_file_path, full_local_path)
        print(f"Downloaded: {remote_file_path} to {full_local_path}")
    except Exception as e:
        print(f"Failed to download {remote_file_path}. Error: {e}")
    finally:
        sftp.close()
        transport.close()

        



def connect_Server():
    if HOST is None:
        raise ValueError("SFTP_HOST environment variable is not set.")
    transport = paramiko.Transport((HOST, PORT))
    if USER is None or PASS is None:
        raise ValueError("SFTP_USER or SFTP_PASS environment variable is not set.")
    transport.connect(username=USER, password=PASS)

    sftp = paramiko.SFTPClient.from_transport(transport)
    get_files(sftp, transport)

    



if __name__ == "__main__":
    connect_Server()