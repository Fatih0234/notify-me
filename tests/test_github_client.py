import pytest
from unittest.mock import patch, MagicMock
import io

from src.github_client import get_latest_release_asset, AssetNotFoundError


def make_release_response(assets):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "tag_name": "v1.0.0",
        "published_at": "2024-01-01T00:00:00Z",
        "assets": assets,
    }
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def make_download_response(content=b"SQLite format 3\x00" + b"\x00" * 100):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.raise_for_status = MagicMock()
    mock_resp.iter_content = MagicMock(return_value=[content])
    return mock_resp


@patch("src.github_client.requests.get")
def test_asset_found(mock_get, tmp_path):
    assets = [
        {
            "id": 42,
            "name": "twitter.db",
            "size": 12345,
            "updated_at": "2024-01-02T00:00:00Z",
            "browser_download_url": "https://example.com/twitter.db",
        }
    ]
    mock_get.side_effect = [
        make_release_response(assets),
        make_download_response(),
    ]

    result = get_latest_release_asset("owner/repo", "twitter.db")

    assert result["release_tag"] == "v1.0.0"
    assert result["asset_name"] == "twitter.db"
    assert result["asset_id"] == 42
    assert result["asset_size"] == 12345
    assert result["asset_updated_at"] == "2024-01-02T00:00:00Z"
    assert "local_path" in result


@patch("src.github_client.requests.get")
def test_asset_not_found_raises(mock_get):
    assets = [
        {
            "id": 1,
            "name": "other_file.zip",
            "size": 100,
            "updated_at": "2024-01-01T00:00:00Z",
            "browser_download_url": "https://example.com/other.zip",
        }
    ]
    mock_get.return_value = make_release_response(assets)

    with pytest.raises(AssetNotFoundError) as exc_info:
        get_latest_release_asset("owner/repo", "twitter.db")

    assert "twitter.db" in str(exc_info.value)
    assert "other_file.zip" in str(exc_info.value)


@patch("src.github_client.requests.get")
def test_auth_token_included_in_headers(mock_get):
    assets = [
        {
            "id": 1,
            "name": "twitter.db",
            "size": 100,
            "updated_at": "2024-01-01T00:00:00Z",
            "browser_download_url": "https://example.com/twitter.db",
        }
    ]
    mock_get.side_effect = [
        make_release_response(assets),
        make_download_response(),
    ]

    get_latest_release_asset("owner/repo", "twitter.db", token="mytoken")

    # Check that Authorization header was sent in the API call
    first_call_kwargs = mock_get.call_args_list[0]
    headers = first_call_kwargs[1]["headers"]
    assert headers.get("Authorization") == "Bearer mytoken"


@patch("src.github_client.requests.get")
def test_no_token_no_auth_header(mock_get):
    assets = [
        {
            "id": 1,
            "name": "twitter.db",
            "size": 100,
            "updated_at": "2024-01-01T00:00:00Z",
            "browser_download_url": "https://example.com/twitter.db",
        }
    ]
    mock_get.side_effect = [
        make_release_response(assets),
        make_download_response(),
    ]

    get_latest_release_asset("owner/repo", "twitter.db", token=None)

    first_call_kwargs = mock_get.call_args_list[0]
    headers = first_call_kwargs[1]["headers"]
    assert "Authorization" not in headers
