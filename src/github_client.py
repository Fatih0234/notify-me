import os
import tempfile
import requests


class AssetNotFoundError(Exception):
    pass


def get_latest_release_asset(repo, asset_name, token=None):
    """Fetch latest release, find asset by name, download to /tmp.

    Returns dict with keys:
      release_tag, published_at, asset_id, asset_name, asset_size,
      asset_updated_at, local_path
    """
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/repos/{repo}/releases/latest"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    release = resp.json()

    assets = release.get("assets", [])
    found = None
    for a in assets:
        if a["name"] == asset_name:
            found = a
            break

    if found is None:
        names = [a["name"] for a in assets]
        print(f"Asset '{asset_name}' not found. Available assets: {names}")
        raise AssetNotFoundError(
            f"Asset '{asset_name}' not found in latest release of {repo}. "
            f"Found: {names}"
        )

    # Download the asset
    download_url = found["browser_download_url"]
    dl_headers = {}
    if token:
        dl_headers["Authorization"] = f"Bearer {token}"
    dl_headers["Accept"] = "application/octet-stream"

    dl_resp = requests.get(download_url, headers=dl_headers, timeout=120, stream=True)
    dl_resp.raise_for_status()

    tmp_dir = tempfile.mkdtemp()
    local_path = os.path.join(tmp_dir, asset_name)
    with open(local_path, "wb") as f:
        for chunk in dl_resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return {
        "release_tag": release["tag_name"],
        "published_at": release["published_at"],
        "asset_id": found["id"],
        "asset_name": found["name"],
        "asset_size": found["size"],
        "asset_updated_at": found["updated_at"],
        "local_path": local_path,
    }
