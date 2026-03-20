import json
import os
import pytest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from src.state import load_state, save_state, is_fresh, has_changed


def test_load_state_missing_file(tmp_path):
    path = str(tmp_path / "nonexistent.json")
    state = load_state(path)
    assert state == {}


def test_load_state_existing_file(tmp_path):
    path = tmp_path / "state.json"
    data = {"x_asset_updated_at": "2024-01-01T00:00:00Z"}
    path.write_text(json.dumps(data))
    state = load_state(str(path))
    assert state == data


def test_save_state(tmp_path):
    path = str(tmp_path / "state.json")
    data = {"key": "value", "last_notified_at": "2024-01-01T00:00:00Z"}
    save_state(data, path)
    with open(path) as f:
        loaded = json.load(f)
    assert loaded == data


def test_is_fresh_recent():
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert is_fresh(recent, freshness_hours=4) is True


def test_is_fresh_too_old():
    now = datetime.now(timezone.utc)
    old = (now - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert is_fresh(old, freshness_hours=4) is False


def test_is_fresh_none():
    assert is_fresh(None, freshness_hours=4) is False


def test_has_changed_different():
    assert has_changed("2024-01-02T00:00:00Z", "2024-01-01T00:00:00Z") is True


def test_has_changed_same():
    assert has_changed("2024-01-01T00:00:00Z", "2024-01-01T00:00:00Z") is False


def test_has_changed_none_last():
    assert has_changed("2024-01-01T00:00:00Z", None) is True


def test_freshness_threshold_boundary():
    now = datetime.now(timezone.utc)
    # Slightly inside the boundary (3h59m ago) to avoid sub-second timing race
    boundary = (now - timedelta(hours=4) + timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Should be considered fresh (<=)
    assert is_fresh(boundary, freshness_hours=4) is True
