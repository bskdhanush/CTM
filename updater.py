import os
import requests
from packaging.version import parse as parse_version

# Debug: module import
print("[DEBUG] GitHub updater module imported")

# Configuration from environment for security
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "bskdhanush")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "QC_stuff")
EXE_NAME = "QSTAF_Tool.exe"
GITHUB_PAT = os.getenv("GITHUB_PAT") or "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"
__version__ = os.getenv("APP_VERSION", "0.0.0")  # Current app version


def get_session():
    """
    Creates an authenticated session with GitHub API.
    Reads PAT from GITHUB_PAT env var and sets appropriate headers.
    """
    print("[DEBUG] Creating GitHub session...")
    token = GITHUB_PAT
    if not token:
        msg = "GITHUB_PAT not set. Cannot access private repository."
        print(f"[ERROR] {msg}")
        raise EnvironmentError(msg)
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    })
    print("[DEBUG] Session created with headers:", session.headers)
    return session


def get_latest_release_info():
    """
    Fetches the latest release info for the given repo.
    Raises HTTPError on failure.
    """
    print(f"[DEBUG] Fetching latest release for {GITHUB_USERNAME}/{GITHUB_REPOSITORY}")
    session = get_session()
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPOSITORY}/releases/latest"
    resp = session.get(api_url, timeout=10)
    resp.raise_for_status()
    print(f"[DEBUG] HTTP {resp.status_code} received for latest release info")
    return resp.json()


def find_asset_download_url(release_data, asset_name):
    """
    Locates the API URL for the named asset in the release data.
    Uses the asset's `url` (API endpoint) for authenticated download.
    """
    print(f"[DEBUG] Searching for asset '{asset_name}' in release data...")
    for asset in release_data.get("assets", []):
        if asset.get("name") == asset_name:
            api_url = asset.get("url")
            print(f"[DEBUG] Found asset API URL: {api_url}")
            return api_url
    msg = f"Asset '{asset_name}' not found in release."
    print(f"[ERROR] {msg}")
    raise ValueError(msg)


def download_file(asset_api_url, dest_folder, dest_name):
    """
    Downloads the GitHub release asset using the API URL with octet-stream accept header.
    Streams to disk safely with a temporary file.
    """
    print(f"[DEBUG] Preparing to download asset from {asset_api_url}")
    session = get_session()
    session.headers.update({"Accept": "application/octet-stream"})

    os.makedirs(dest_folder, exist_ok=True)
    temp_path = os.path.join(dest_folder, dest_name + ".tmp")
    final_path = os.path.join(dest_folder, dest_name)

    with session.get(asset_api_url, stream=True, timeout=60) as r:
        print(f"[DEBUG] HTTP {r.status_code} start streaming...")
        r.raise_for_status()
        with open(temp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                print(f"[DEBUG] Wrote chunk of size {len(chunk)}")

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


def main_update_check():
    """
    Main entry to check for updates and download new version if available.
    """
    print(f"[INFO] Starting update check — current version: {__version__}")
    try:
        release = get_latest_release_info()
    except Exception as e:
        print(f"[ERROR] Failed to fetch release info: {e}")
        return

    latest_tag = release.get("tag_name", "")
    print(f"[INFO] Latest tag on GitHub: {latest_tag}")

    if is_update_available(__version__, latest_tag):
        print(f"[INFO] New version available: {latest_tag}")
        try:
            asset_url = find_asset_download_url(release, EXE_NAME)
            download_dir = os.getenv('TEMP', '/tmp')
            downloaded = download_file(asset_url, download_dir, EXE_NAME)
            print(f"[INFO] Downloaded new version to: {downloaded}")
        except Exception as e:
            print(f"[ERROR] Update failed: {e}")
    else:
        print("[INFO] You already have the latest version.")


# Run on import for immediate feedback
print("[DEBUG] Invoking main_update_check()")
main_update_check()
