#!/usr/bin/env python3

"""
Fast SFTP downloader using ssh2-python (libssh2).
Install: pip install ssh2-python python-dotenv
"""

import os
import socket
import time
from datetime import datetime
import datetime
from dotenv import load_dotenv
from ssh2.session import Session
from ssh2.sftp import (
    LIBSSH2_FXF_READ,
    LIBSSH2_SFTP_S_IRUSR,
    LIBSSH2_FXF_WRITE,
    LIBSSH2_FXF_CREAT,
    LIBSSH2_FXF_TRUNC,
    LIBSSH2_SFTP_S_IRUSR,
    LIBSSH2_SFTP_S_IWUSR
)

load_dotenv()
HOST = os.getenv("SFTP_HOST")
PORT = int(os.getenv("SFTP_PORT", 22))
USER = os.getenv("SFTP_USER")
PASS = os.getenv("SFTP_PASS")
REMOTE_PATH = "Incoming/"

def connect_sftp(connect_timeout=20):
    if not HOST or not USER or PASS is None:
        raise ValueError("SFTP connection details (SFTP_HOST, SFTP_USER, SFTP_PASS) required in .env")
    sess = sftp = sock = None
    try:
        sock = socket.create_connection((HOST, PORT), timeout=connect_timeout)
        sess = Session()
        sess.handshake(sock)
        sess.userauth_password(USER, PASS)
        sftp = sess.sftp_init()
    except socket.timeout:
        print("Connection timed out.")
    except socket.error as e:
        print(f"Socket error: {e}")
    return sess, sftp, sock

def list_files(device_filter="", pageName="",sub_sting=""):
    """
    Return a list of dicts: [{'name': , 'size': , 'mtime': }...]
    Uses sftp.opendir() and handle.readdir()
    """
    files = []
    keywords = []
    if sub_sting=="":
        if pageName == "Meta":
            filter = device_filter.strip('"')
            filter = filter.split('.')[0]
            keywords= [filter]
        elif pageName == "Mpss":
            keywords= ["BF","MPSS"]
    elif sub_sting:
        sub_sting=sub_sting.upper()
        keywords= ["BF","MPSS"]

    try:
        sess, sftp, sock = connect_sftp()
    except Exception as e:
        print(f'Exception during connect_sftp : {e}')
        sess = sftp = sock = None
    if sess and sftp and sock:
        try:
            # Use opendir to get a handle; iterate handle.readdir()
            with sftp.opendir(REMOTE_PATH) as dh:
                for entry in dh.readdir():
                    print(f"printing entry : {entry[1]}")
                    if len(entry) == 3:
                        _, name_buf, attrs = entry
                    else:
                        name_buf = entry[1] if len(entry) > 1 else entry[0]
                        attrs = entry[-1] if len(entry) > 1 else None

                    name = name_buf.decode() if isinstance(name_buf, (bytes, bytearray)) else str(name_buf)
                    print(pageName)
                    if pageName=="Meta":
                        if keywords and not any(k in name for k in keywords):
                            continue
                    else:
                        if keywords and not (sub_sting in name and any(k in name for k in keywords)):
                            continue  # Skip if BOTH conditions are not met

                    filesize = getattr(attrs, "filesize", None) if attrs is not None else None
                    mtime = getattr(attrs, "mtime", None) if attrs is not None else None
                    dt = datetime.datetime.fromtimestamp(mtime) # type: ignore
                    files.append({"name": name, "size": filesize, "mtime": dt.strftime("%Y-%m-%d %H:%M:%S")})
        finally:
            try:
                sess.disconnect()
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass
    else:
        print(f'Failed to establish FTP connection to {HOST}')
    return files

def download_file(remote_filename, local_dir, chunk_size=1024 * 1024, progress_interval=0.5):
    """
    Download a remote file via libssh2 with large chunk reads.
    """
    try:
        sess, sftp, sock = connect_sftp()
    except Exception as e:
        print(f'Exception during connect_sftp : {e}')
        sess = sftp = sock = None
    if sess and sftp and sock:
        try:
            remote_path = REMOTE_PATH.rstrip("/") + "/" + remote_filename
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, remote_filename)

            # Open remote file for reading
            fh = sftp.open(remote_path, LIBSSH2_FXF_READ, LIBSSH2_SFTP_S_IRUSR)
            try:
                fstat = fh.fstat()
                file_size = getattr(fstat, "filesize", None)
                if file_size is None:
                    print("Could not determine remote file size; proceeding anyway.")
                    file_size = float("inf")

                print(f"Downloading: {remote_filename} size={file_size}")
                transferred = 0
                start = time.time()
                last_time = start
                last_transferred = 0

                with open(local_path, "wb") as lf:
                    while True:
                        to_read = chunk_size if transferred + chunk_size <= file_size else int(file_size - transferred)
                        chunk = fh.read(to_read)

                        # normalize:
                        if isinstance(chunk, tuple) and len(chunk) == 2:
                            rc, data = chunk
                            if rc <= 0 or not data:
                                break
                        else:
                            data = chunk
                            if not data:
                                break

                        if not isinstance(data, (bytes, bytearray)):
                            raise TypeError("Expected bytes from fh.read(), got: {}".format(type(data)))

                        lf.write(data)
                        transferred += len(data)

                        now = time.time()
                        if now - last_time >= progress_interval or transferred == file_size:
                            delta = transferred - last_transferred
                            dt = now - last_time if now - last_time > 0 else 1e-6
                            speed_bps = delta / dt
                            speed_mbps = speed_bps * 8 / (1024 * 1024)
                            pct = (transferred / file_size * 100) if file_size and file_size != float("inf") else 0
                            print(f"\r{transferred}/{file_size if file_size!=float('inf') else 'unknown'} bytes ({pct:.1f}%) - {speed_mbps:.2f} Mbps", end="", flush=True)
                            last_time = now
                            last_transferred = transferred

                total_time = time.time() - start
                avg_mbps = (transferred * 8 / (1024 * 1024)) / total_time if total_time > 0 else 0
                print(f"\nCompleted: {transferred} bytes in {total_time:.1f}s — avg {avg_mbps:.2f} Mbps")
            finally:
                try:
                    fh.close()
                except Exception:
                    pass
        finally:
            try:
                sess.disconnect()
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass
    else:
        print(f'Failed to establish FTP connection to {HOST}')
        

def file_upload(filepath, server_upload_path, chunk_size=1024 * 1024, progress_interval=0.5):
    """
    Upload a local file to the remote SFTP server via libssh2 with large chunk writes.
    
    Args:
        filepath: Local file path to upload
        server_upload_path: Remote destination path (including filename)
        chunk_size: Size of chunks to read/write (default 1MB)
        progress_interval: How often to print progress updates in seconds
    """
    from CrashHandler import remove_crash_entry
    try:
        sess, sftp, sock = connect_sftp()
    except Exception as e:
        print(f'Exception during connect_sftp : {e}')
        sess = sftp = sock = None
    if sess and sftp and sock:
        try:
            # Ensure local file exists
            if not os.path.isfile(filepath):
                raise FileNotFoundError(f"Local file not found: {filepath}")

            # Get local file size
            file_size = os.path.getsize(filepath)

            # Prepare remote path
            remote_path = server_upload_path if "/" in server_upload_path else (REMOTE_PATH.rstrip("/") + "/" + server_upload_path)

            print(f"Uploading: {os.path.basename(filepath)} ({file_size} bytes) to {remote_path}")

            # Use standard permissions: 0644 (rw-r--r--)
            mode = LIBSSH2_SFTP_S_IRUSR | LIBSSH2_SFTP_S_IWUSR | LIBSSH2_SFTP_S_IRUSR | LIBSSH2_SFTP_S_IRUSR

            # Open remote file for writing
            try:
                fh = sftp.open(
                    remote_path,
                    LIBSSH2_FXF_WRITE | LIBSSH2_FXF_CREAT | LIBSSH2_FXF_TRUNC,
                    mode
                )
            except Exception as e:
                print(f"Failed to open remote file. Error: {e}")
                print(f"Ensure the remote directory exists and you have write permissions.")
                raise

            try:
                transferred = 0
                start = time.time()
                last_time = start
                last_transferred = 0

                with open(filepath, "rb") as lf:
                    while True:
                        # Read chunk from local file
                        data = lf.read(chunk_size)
                        if not data:
                            break

                        # Write chunk to remote file - returns (error_code, bytes_written) tuple
                        result = fh.write(data)

                        # Handle tuple return value
                        if isinstance(result, tuple):
                            error_code, bytes_written = result
                            if error_code < 0:
                                raise IOError(f"Upload failed with error code: {error_code}")
                        else:
                            # Fallback if not tuple (shouldn't happen in normal operation)
                            bytes_written = result if result else len(data)

                        transferred += bytes_written

                        # Progress reporting
                        now = time.time()
                        if now - last_time >= progress_interval or transferred == file_size:
                            delta = transferred - last_transferred
                            dt = now - last_time if now - last_time > 0 else 1e-6
                            speed_bps = delta / dt
                            speed_mbps = speed_bps * 8 / (1024 * 1024)
                            pct = (transferred / file_size * 100) if file_size > 0 else 0
                            print(f"\r{transferred}/{file_size} bytes ({pct:.1f}%) - {speed_mbps:.2f} Mbps", end="", flush=True)
                            last_time = now
                            last_transferred = transferred

                total_time = time.time() - start
                avg_mbps = (transferred * 8 / (1024 * 1024)) / total_time if total_time > 0 else 0
                print(f"\nCompleted: {transferred} bytes in {total_time:.1f}s — avg {avg_mbps:.2f} Mbps")
                remove_crash_entry(filepath)

            finally:
                try:
                    fh.close()
                except Exception:
                    pass
        finally:
            try:
                sess.disconnect()
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass
    else:
        print(f'Failed to establish FTP connection to {HOST}')

if __name__ == "__main__":
    # Basic example: list and download first matching file
    device = "Kobuk"
    files = list_files(device)
    if not files:
        print("No matching files found.")
        target = files[0]["name"]
        print(f"Downloading first file: {target}")
        #download_file(target, "./downloads")
        
        # Example upload usage:
        # file_upload("./local_file.bin", "uploaded_file.bin")
