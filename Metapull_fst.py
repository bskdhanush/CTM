import paramiko
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

HOST = os.getenv("SFTP_HOST")
PORT = int(os.getenv("SFTP_PORT", 22))  # usually 21
USER = os.getenv('SFTP_USER')
PASS = os.getenv("SFTP_PASS")


def check_lates_meta(items):
    pass



def get_files(sftp, transport):
    if sftp is not None:
        print("Connected successfully to SFTP server.")

        for item in sftp.listdir_attr('/Incoming'):
            filename = item.filename
            modified_time = item.st_mtime
            if modified_time is not None:
                date = datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d %H:%M:%S")
            else:
                date = "Unknown"
            if item.filename.startswith('BF-ENG') or item.filename.startswith('Kobuk') or item.filename.startswith('Pinnacle'):
                print(f"{filename} - {date}")


        sftp.close()
    else:
        print("Failed to establish SFTP connection.")
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