import json
import os
from datetime import datetime, timezone


def load_state(path="state.json"):
    """Load state from JSON file. Returns empty dict if file doesn't exist."""
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_state(state, path="state.json"):
    """Save state to JSON file."""
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def is_fresh(asset_updated_at, freshness_hours):
    """Return True if asset_updated_at is within freshness_hours from now."""
    if not asset_updated_at:
        return False
    updated = datetime.fromisoformat(asset_updated_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    age_hours = (now - updated).total_seconds() / 3600
    return age_hours <= freshness_hours


def has_changed(asset_updated_at, last_updated_at):
    """Return True if asset has changed since last run."""
    return asset_updated_at != last_updated_at
