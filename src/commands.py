import os
import sys
import base64
import json
import requests
from state import load_state, save_state

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
GITHUB_API = "https://api.github.com"
YOUTUBE_API = "https://www.googleapis.com/youtube/v3"

COMMANDS = {
    "/add-x":          ("x",  "add"),
    "/remove-x":       ("x",  "remove"),
    "/add-youtube":    ("yt", "add"),
    "/remove-youtube": ("yt", "remove"),
}

HELP_TEXT = (
    "Available commands:\n"
    "/add-x @username — track an X account\n"
    "/remove-x @username — stop tracking an X account\n"
    "/add-youtube @handle — track a YouTube channel\n"
    "/remove-youtube @handle — stop tracking a YouTube channel"
)


def tg(token, method, **kwargs):
    url = TELEGRAM_API.format(token=token, method=method)
    resp = requests.post(url, json=kwargs, timeout=15)
    resp.raise_for_status()
    return resp.json()


def send(token, chat_id, text):
    tg(token, "sendMessage", chat_id=chat_id, text=text)


def get_updates(token, offset=None):
    params = {"timeout": 0, "allowed_updates": ["message"]}
    if offset is not None:
        params["offset"] = offset
    url = TELEGRAM_API.format(token=token, method="getUpdates")
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("result", [])


def fetch_config(repo, gh_token):
    """Fetch and parse config.json from a GitHub repo."""
    url = f"{GITHUB_API}/repos/{repo}/contents/config.json"
    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    content = base64.b64decode(resp.json()["content"]).decode("utf-8")
    return json.loads(content)


def youtube_channel_exists(handle, yt_api_key):
    """Return True if a YouTube channel handle resolves to a real channel."""
    resp = requests.get(
        f"{YOUTUBE_API}/channels",
        params={"part": "id", "forHandle": handle.lstrip("@"), "key": yt_api_key},
        timeout=15,
    )
    resp.raise_for_status()
    return len(resp.json().get("items", [])) > 0


def trigger_workflow(repo, workflow_file, inputs, gh_token):
    url = f"{GITHUB_API}/repos/{repo}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.post(url, headers=headers, json={"ref": "main", "inputs": inputs}, timeout=15)
    if resp.status_code == 204:
        return True
    resp.raise_for_status()


def process_command(text, token, chat_id, gh_token, x_repo, yt_repo, yt_api_key):
    parts = text.strip().split(None, 1)
    cmd = parts[0].lower()

    if cmd == "/help":
        send(token, chat_id, HELP_TEXT)
        return

    if cmd not in COMMANDS:
        send(token, chat_id, f"Unknown command. {HELP_TEXT}")
        return

    if len(parts) < 2 or not parts[1].strip():
        send(token, chat_id, f"Usage: {cmd} @handle")
        return

    source, action = COMMANDS[cmd]
    handle = parts[1].strip()

    if source == "x":
        username = handle.lstrip("@")

        try:
            config = fetch_config(x_repo, gh_token)
            tracked = [a.lower() for a in config.get("accounts", [])]
            if action == "add" and username.lower() in tracked:
                send(token, chat_id, f"@{username} is already being tracked.")
                return
            if action == "remove" and username.lower() not in tracked:
                send(token, chat_id, f"@{username} is not in the tracking list.")
                return
        except Exception as e:
            print(f"Warning: could not fetch X config for validation: {e}")
            # Non-blocking — proceed with workflow trigger anyway

        trigger_workflow(
            x_repo, "manage-accounts.yml",
            {"action": action, "username": username},
            gh_token,
        )
        verb = "Adding" if action == "add" else "Removing"
        send(token, chat_id, f"{verb} @{username} on X... workflow triggered on {x_repo}")

    elif source == "yt":
        channel = handle if handle.startswith("@") else f"@{handle}"

        if action == "add" and yt_api_key:
            try:
                if not youtube_channel_exists(channel, yt_api_key):
                    send(token, chat_id, f"{channel} was not found on YouTube. Please check the handle and try again.")
                    return
            except Exception as e:
                print(f"Warning: could not validate YouTube channel existence: {e}")

        try:
            config = fetch_config(yt_repo, gh_token)
            tracked = [c.lstrip("@").lower() for c in config.get("channels", [])]
            channel_clean = channel.lstrip("@").lower()
            if action == "add" and channel_clean in tracked:
                send(token, chat_id, f"{channel} is already being tracked.")
                return
            if action == "remove" and channel_clean not in tracked:
                send(token, chat_id, f"{channel} is not in the tracking list.")
                return
        except Exception as e:
            print(f"Warning: could not fetch YT config for validation: {e}")

        trigger_workflow(
            yt_repo, "manage-channels.yml",
            {"action": action, "handle": channel},
            gh_token,
        )
        verb = "Adding" if action == "add" else "Removing"
        send(token, chat_id, f"{verb} {channel} on YouTube... workflow triggered on {yt_repo}")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    gh_token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN")
    x_repo = os.environ.get("X_REPO", "Fatih0234/x-botty")
    yt_repo = os.environ.get("YT_REPO", "Fatih0234/youtube-competitor-tracker")
    yt_api_key = os.environ.get("YOUTUBE_API_KEY")
    state_path = os.environ.get("STATE_PATH", "state.json")

    if not token or not chat_id:
        print("ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required.")
        sys.exit(1)
    if not gh_token:
        print("ERROR: GH_PAT is required to trigger workflows on other repos.")
        sys.exit(1)
    if not yt_api_key:
        print("WARNING: YOUTUBE_API_KEY not set — YouTube channel existence check disabled.")

    state = load_state(state_path)
    offset = state.get("last_command_update_id")
    if offset is not None:
        offset += 1

    updates = get_updates(token, offset)
    if not updates:
        print("No new updates.")
        return

    authorized_chat_id = str(chat_id)
    processed = 0

    for update in updates:
        update_id = update["update_id"]
        state["last_command_update_id"] = update_id

        message = update.get("message", {})
        msg_chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "").strip()

        if msg_chat_id != authorized_chat_id:
            print(f"Ignored message from unauthorized chat {msg_chat_id}")
            continue

        if not text or not text.startswith("/"):
            continue

        print(f"Processing command: {text!r}")
        try:
            process_command(text, token, chat_id, gh_token, x_repo, yt_repo, yt_api_key)
            processed += 1
        except Exception as e:
            print(f"Error processing '{text}': {e}")
            send(token, chat_id, f"Error: {e}")

    save_state(state, state_path)
    print(f"Processed {processed} command(s) from {len(updates)} update(s).")


if __name__ == "__main__":
    main()
