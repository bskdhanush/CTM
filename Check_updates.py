from datetime import datetime
import os
from tkinter import messagebox    
import requests
from packaging.version import parse as parse_version


print("[DEBUG] GitHub updater module imported")

# Configuration from environment for security
GITHUB_USERNAME   = os.getenv("GITHUB_USERNAME", "bskdhanush")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "QC_stuff")
GITHUB_PAT        = os.getenv("GITHUB_PAT") or "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"
__version__       = os.getenv("APP_VERSION", "1.2.1")  # Current app version
DOWNLOAD_DIR      = r"C:\QSTAF" 

def get_session():
    """
    Creates an authenticated session with GitHub API.
    Raises EnvironmentError if PAT is missing.
    """
    print("[DEBUG] Creating GitHub session...")
    if not GITHUB_PAT:
        raise EnvironmentError("GITHUB_PAT not set. Cannot access private repository.")
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    })
    return s

def fetch_latest_release_data():
    """
    Fetches the full JSON for the latest release.
    Raises HTTPError on failure.
    """
    print(f"[DEBUG] Fetching latest release for {GITHUB_USERNAME}/{GITHUB_REPOSITORY}")
    session = get_session()
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/releases/latest"
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    print(f"[DEBUG] HTTP {resp.status_code} received for latest release JSON")
    return resp.json()

def get_latest_release_version():
    """
    Returns only the version string (tag_name or name) of the latest release.
    """
    data = fetch_latest_release_data()
    version = data.get("tag_name") or data.get("name")
    if not version:
        msg = "Latest release has no tag_name or name."
        print(f"[ERROR] {msg}")
        raise ValueError(msg)

    print(f"[DEBUG] Parsed latest release version: {version}")
    return version

def find_latest_exe_download_url(release_data):
    """
    From a release JSON, finds the newest .exe asset by created_at
    and returns a tuple (asset_api_url, asset_filename).
    Raises ValueError if none found.
    """
    print("[DEBUG] Searching for .exe assets in release data…")
    assets = release_data.get("assets", [])
    exe_assets = [a for a in assets if a.get("name", "").lower().endswith(".exe")]

    if not exe_assets:
        msg = "No .exe asset found in latest release."
        print(f"[ERROR] {msg}")
        raise ValueError(msg)

    # Helper to parse GitHub's ISO timestamp
    def _parse_iso(ts: str) -> datetime:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")

    # Sort descending by creation time
    exe_assets.sort(key=lambda a: _parse_iso(a.get("created_at", "")), reverse=True)
    chosen = exe_assets[0]

    api_url  = chosen.get("url")
    filename = chosen.get("name")
    print(f"[DEBUG] Selected .exe '{filename}' → {api_url}")
    return api_url, filename

def download_file(asset_api_url, dest_folder, dest_name):
    """
    Downloads the GitHub release asset using the API URL with octet-stream accept header.
    Streams to disk safely with a temporary file.
    """
    print(f"[DEBUG] Preparing to download asset from {asset_api_url}")
    session = get_session()
    session.headers.update({"Accept": "application/octet-stream"})

    os.makedirs(dest_folder, exist_ok=True)
    temp_path  = os.path.join(dest_folder, dest_name + ".tmp")
    final_path = os.path.join(dest_folder, dest_name)

    with session.get(asset_api_url, stream=True, timeout=60) as r:
        print(f"[DEBUG] HTTP {r.status_code} start streaming.")
        r.raise_for_status()
        with open(temp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    os.replace(temp_path, final_path)
    print(f"[DEBUG] Downloaded and saved to {final_path}")
    return final_path

def is_update_available(current_ver, latest_tag):
    """
    Compares current app version against latest Git tag using packaging.version.
    """
    print(f"[DEBUG] Comparing versions: current={current_ver}, latest={latest_tag}")
    result = parse_version(latest_tag.lstrip('v')) > parse_version(current_ver.lstrip('v'))
    print(f"[DEBUG] Update available: {result}")
    return result

def asset_already_present(dest_folder: str, filename: str) -> bool:
    """
    Returns True if the exact asset file is already present on disk.
    """
    return os.path.isfile(os.path.join(dest_folder, filename))

def main_update_check():
    print(f"[INFO] Starting update check — current version: {__version__}")

    try:
        release = fetch_latest_release_data()
    except Exception as e:
        print(f"[ERROR] Failed to fetch release info: {e}")
        return

    latest_tag = release.get("tag_name", "")
    print(f"[INFO] Latest tag on GitHub: {latest_tag}")

    if not is_update_available(__version__, latest_tag):
        print("[INFO] You already have the latest version running.")
        return

    print(f"[INFO] New version available: {latest_tag}")

    try:
        api_url, asset_name = find_latest_exe_download_url(release)
        if asset_already_present(DOWNLOAD_DIR, asset_name):
            print(f"[INFO] '{asset_name}' is already present in {DOWNLOAD_DIR}. Skipping download.")
            return

        downloaded_path = download_file(api_url, DOWNLOAD_DIR, asset_name)
        #print(f"[INFO] Downloaded new version to: {downloaded_path}")
        messagebox.showinfo("Update available",f"Downloaded new version at '{downloaded_path}'")

    except Exception as e:
        print(f"[ERROR] Update failed: {e}")

# Uncomment to run automatically on import
# print("[DEBUG] Invoking main_update_check()")
# main_update_check()