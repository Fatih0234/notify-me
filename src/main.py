import os
import sys
from datetime import datetime, timezone

from github_client import get_latest_release_asset, AssetNotFoundError
from db_loader import load_db, DatabaseValidationError
from x_queries import get_top_x_posts
from youtube_queries import get_top_youtube_videos
from formatter import build_message
from telegram_client import send_messages
from state import load_state, save_state, is_fresh, has_changed


def get_env(name, default=None, required=False):
    val = os.environ.get(name, default)
    if required and not val:
        print(f"ERROR: Required env var {name} is not set.")
        sys.exit(1)
    return val


def main():
    # Required env vars
    bot_token = get_env("TELEGRAM_BOT_TOKEN", required=True)
    chat_id = get_env("TELEGRAM_CHAT_ID", required=True)
    x_repo = get_env("X_REPO", default="Fatih0234/x-botty")
    yt_repo = get_env("YT_REPO", default="Fatih0234/youtube-competitor-tracker")
    x_asset_name = get_env("X_RELEASE_ASSET_NAME", default="twitter.db")
    yt_asset_name = get_env("YT_RELEASE_ASSET_NAME", default="youtube_competitor_tracker.db")
    github_token = get_env("GITHUB_TOKEN")
    freshness_hours = float(get_env("FRESHNESS_HOURS", default="4"))
    state_path = get_env("STATE_PATH", default="state.json")

    print("=== Telegram Notifier Bot ===")

    # Step 1: Download X asset
    print(f"\n[1/9] Downloading X asset from {x_repo}...")
    try:
        x_asset_info = get_latest_release_asset(x_repo, x_asset_name, token=github_token)
        print(f"  OK: {x_asset_name} ({x_asset_info['asset_size']} bytes), updated {x_asset_info['asset_updated_at']}")
    except AssetNotFoundError as e:
        print(f"  ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"  ERROR downloading X asset: {e}")
        sys.exit(1)

    # Step 2: Validate X DB
    print(f"\n[2/9] Validating X database...")
    try:
        x_conn = load_db(x_asset_info["local_path"])
        print("  OK: X database is valid")
    except DatabaseValidationError as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    # Step 3: Download YT asset
    print(f"\n[3/9] Downloading YT asset from {yt_repo}...")
    try:
        yt_asset_info = get_latest_release_asset(yt_repo, yt_asset_name, token=github_token)
        print(f"  OK: {yt_asset_name} ({yt_asset_info['asset_size']} bytes), updated {yt_asset_info['asset_updated_at']}")
    except AssetNotFoundError as e:
        print(f"  ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"  ERROR downloading YT asset: {e}")
        sys.exit(1)

    # Step 4: Validate YT DB
    print(f"\n[4/9] Validating YT database...")
    try:
        yt_conn = load_db(yt_asset_info["local_path"])
        print("  OK: YT database is valid")
    except DatabaseValidationError as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    # Step 5: Load state
    print(f"\n[5/9] Loading state from {state_path}...")
    state = load_state(state_path)
    print(f"  State: {state}")

    # Step 6: Freshness check
    print(f"\n[6/9] Freshness check (threshold: {freshness_hours}h)...")
    x_fresh = is_fresh(x_asset_info["asset_updated_at"], freshness_hours)
    yt_fresh = is_fresh(yt_asset_info["asset_updated_at"], freshness_hours)
    if not x_fresh and not yt_fresh:
        print(f"  SKIP: Both assets are older than {freshness_hours}h. No notification sent.")
        sys.exit(0)
    print(f"  X fresh: {x_fresh}, YT fresh: {yt_fresh}")

    # Step 7: Duplicate check
    print(f"\n[7/9] Duplicate check...")
    x_changed = has_changed(x_asset_info["asset_updated_at"], state.get("x_asset_updated_at"))
    yt_changed = has_changed(yt_asset_info["asset_updated_at"], state.get("yt_asset_updated_at"))
    if not x_changed and not yt_changed:
        print("  SKIP: Both assets unchanged since last run. No notification sent.")
        sys.exit(0)
    print(f"  X changed: {x_changed}, YT changed: {yt_changed}")

    # Step 8: Query DBs
    print(f"\n[8/9] Querying databases...")
    x_posts = get_top_x_posts(x_conn)
    yt_videos = get_top_youtube_videos(yt_conn)
    print(f"  X posts: {len(x_posts)}, YT videos: {len(yt_videos)}")

    # Step 9: Format and send
    print(f"\n[9/9] Formatting and sending Telegram message...")
    messages = build_message(x_posts, yt_videos, x_asset_info, yt_asset_info)
    print(f"  Messages to send: {len(messages)}")

    send_messages(bot_token, chat_id, messages)
    print("  OK: Message(s) sent successfully!")

    # Save state
    state["x_asset_updated_at"] = x_asset_info["asset_updated_at"]
    state["yt_asset_updated_at"] = yt_asset_info["asset_updated_at"]
    state["last_notified_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state, state_path)
    print(f"\nState saved to {state_path}")

    x_conn.close()
    yt_conn.close()


if __name__ == "__main__":
    main()
