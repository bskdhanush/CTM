import paramiko
from dotenv import load_dotenv
import os

load_dotenv()

HOST = os.getenv("SFTP_HOST")
PORT = int(os.getenv("SFTP_PORT", 22))  # usually 21
USER = os.getenv('SFTP_USER')
PASS = os.getenv("SFTP_PASS")




def connect_fileZilla():
    if HOST is None:
        raise ValueError("SFTP_HOST environment variable is not set.")
    transport = paramiko.Transport((HOST, PORT))
    if USER is None or PASS is None:
        raise ValueError("SFTP_USER or SFTP_PASS environment variable is not set.")
    transport.connect(username=USER, password=PASS)

    sftp = paramiko.SFTPClient.from_transport(transport)
    if sftp is not None:
        print("Connected successfully to SFTP server.")

        for item in sftp.listdir('.'):
            print(item)

        sftp.close()
    else:
        print("Failed to establish SFTP connection.")
    transport.close()



if __name__ == "__main__":
    connect_fileZilla()