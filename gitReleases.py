import os
import requests

# GitHub repo details
GITHUB_USER = "bskdhanush"
GITHUB_REPO = "CTM"
GITHUB_PAT = os.getenv("GITHUB_PAT") or "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"

def get_session():
    if not GITHUB_PAT:
        raise EnvironmentError("GITHUB_PAT not set. Cannot access private repository.")
    sess = requests.Session()
    sess.headers.update({
        "Authorization": f"Bearer {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    })
    return sess

def fetch_all_release():
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases"
    sess = get_session()
    r = sess.get(api_url, timeout=10)
    r.raise_for_status()
    return r.json()

def download_asset_by_tag(tag: str, dest_folder="."):
    releases = fetch_all_release()
    selected = next((r for r in releases if r.get("tag_name") == tag), None)

    if not selected:
        print(f"❌ Release with tag '{tag}' not found.")
        return

    assets = selected.get("assets", [])
    if not assets:
        print(f"❌ No assets found for release '{tag}'")
        return

    exe_asset = next((a for a in assets if a["name"].endswith(".exe")), None)
    if not exe_asset:
        print(f"❌ No .exe asset found in release '{tag}'. Available assets:")
        for a in assets:
            print(f"  - {a['name']}")
        return

    download_url = exe_asset["url"]  # 👈 Use API URL (not browser_download_url)
    filename = exe_asset["name"]
    dest_path = os.path.join(dest_folder, filename)

    print(f"⬇️ Downloading {filename} from release {tag}...")

    sess = get_session()
    headers = {
        "Accept": "application/octet-stream"  # 👈 needed for downloading assets via API
    }
    with sess.get(download_url, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"✅ Downloaded to: {dest_path}")

if __name__ == "__main__":
    selected_tag = "v1.2.5"
    download_asset_by_tag(selected_tag)
