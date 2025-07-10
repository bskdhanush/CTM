import os
import requests
import CheckUpdates

# Replace with your target repository

GITHUB_USER   = "bskdhanush"
GITHUB_REPO   = "CTM"

# You should supply a valid PAT in your environment; do NOT hard-code in production.
GITHUB_PAT    = os.getenv("GITHUB_PAT") or "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"




def get_session():
    """
    Return a requests.Session that includes the GitHub PAT header.
    Raises EnvironmentError if the PAT is missing.
    """
    if not GITHUB_PAT:
        raise EnvironmentError("GITHUB_PAT not set. Cannot access private repository.")
    sess = requests.Session()
    sess.headers.update({
        "Authorization": f"Bearer {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json"
    })
    return sess

def fetch_latest_release_data():
    """
    Hits GitHub's /repos/:owner/:repo/releases/latest endpoint.
    Returns the JSON payload or raises HTTPError.
    """
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases"
    sess = get_session()
    r = sess.get(api_url, timeout=10)
   
    return r.json()

def getReleases():
    releases=fetch_latest_release_data()
    print(f"Found {len(releases)} releases.")

    for r in releases:
        print(r.get('tag_name', 'No tag'))
    


if __name__=="__main__":
    getReleases()
