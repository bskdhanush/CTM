#!/usr/bin/env python3
"""
Fast SFTP downloader using ssh2-python (libssh2).
Install: pip install ssh2-python python-dotenv
"""

import os
import socket
import time
from datetime import datetime
from dotenv import load_dotenv

from ssh2.session import Session
from ssh2.sftp import (
    LIBSSH2_FXF_READ,
    LIBSSH2_SFTP_S_IRUSR,
)

load_dotenv()

HOST = os.getenv("SFTP_HOST")
PORT = int(os.getenv("SFTP_PORT", 22))
USER = os.getenv("SFTP_USER")
PASS = os.getenv("SFTP_PASS")
REMOTE_PATH = "Incoming/"


def connect_sftp(connect_timeout=10):
    if not HOST or not USER or PASS is None:
        raise ValueError("SFTP connection details (SFTP_HOST, SFTP_USER, SFTP_PASS) required in .env")

    sock = socket.create_connection((HOST, PORT), timeout=connect_timeout)
    sess = Session()
    sess.handshake(sock)
    sess.userauth_password(USER, PASS)
    sftp = sess.sftp_init()
    return sess, sftp, sock


def list_files(device_filter="", pageName=""):
    """
    Return a list of dicts: [{'name': <str>, 'size': <int|None>, 'mtime': <int|None>}...]
    Uses sftp.opendir() and handle.readdir()
    """
    keywords = []
    if pageName == "Meta":
        filter = device_filter.strip('"')
        filter = filter.split('.')[0]
        keywords= [filter]
    
    elif pageName == "Mpss":
        keywords= ["BF","MPSS"]



    #print(f"Listing files for device filter: '{filter}'")
    sess, sftp, sock = connect_sftp()
    try:
        files = []
        # Use opendir to get a handle; iterate handle.readdir()
        with sftp.opendir(REMOTE_PATH) as dh:
            for entry in dh.readdir():  # yields tuples (name_len, name_bytes, attrs) in many builds
                # Some versions yield (size, buf, attrs) or (name_len, name_buf, attrs)
                # Normalize extraction:
                print(f"printing entry : {entry[1]}")
                if len(entry) == 3:
                    _, name_buf, attrs = entry
                else:
                    # fallback: try to unpack first two as name bytes and attrs
                    name_buf = entry[1] if len(entry) > 1 else entry[0]
                    attrs = entry[-1] if len(entry) > 1 else None

                name = name_buf.decode() if isinstance(name_buf, (bytes, bytearray)) else str(name_buf)
                if keywords and not any(k in name for k in keywords):
                    continue

                filesize = getattr(attrs, "filesize", None) if attrs is not None else None
                mtime = getattr(attrs, "mtime", None) if attrs is not None else None

                files.append({"name": name, "size": filesize, "mtime": mtime})
        return files
    finally:
        try:
            sess.disconnect()
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass


def download_file(remote_filename, local_dir, chunk_size=1024 * 1024, progress_interval=0.5):
    """
    Download a remote file via libssh2 with large chunk reads.
    """
    sess, sftp, sock = connect_sftp()
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

            print(f"Downloading: {remote_filename}  size={file_size}")

            transferred = 0
            start = time.time()
            last_time = start
            last_transferred = 0

            with open(local_path, "wb") as lf:
                while True:
                    to_read = chunk_size if transferred + chunk_size <= file_size else int(file_size - transferred)
                    # fh.read returns (rc, data) in some bindings; in others it returns data directly.
                    chunk = fh.read(to_read)
                    # normalize:
                    if isinstance(chunk, tuple) and len(chunk) == 2:
                        rc, data = chunk
                        if rc <= 0 or not data:
                            break
                    else:
                        # chunk is bytes or None
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


if __name__ == "__main__":
    # Basic example: list and download first matching file
    device = "Kobuk"
    files = list_files(device)
    if not files:
        print("No matching files found.")
    else:
        print("Found files:")
        for f in files:
            mtime = datetime.fromtimestamp(f["mtime"]).strftime("%Y-%m-%d %H:%M:%S") if f["mtime"] else "Unknown"
            print(f" - {f['name']}  size={f['size']}  mtime={mtime}")

        # Download the first file
        target = files[0]["name"]
        print(f"Downloading first file: {target}")
        #download_file(target, "./downloads")