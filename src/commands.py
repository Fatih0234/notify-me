import os
import sys
import requests
from state import load_state, save_state

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
GITHUB_API = "https://api.github.com"

COMMANDS = {
    "/add-x":        ("x",  "add"),
    "/remove-x":     ("x",  "remove"),
    "/add-youtube":  ("yt", "add"),
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


def process_command(text, token, chat_id, gh_token, x_repo, yt_repo):
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
        trigger_workflow(
            x_repo, "manage-accounts.yml",
            {"action": action, "username": username},
            gh_token,
        )
        verb = "Adding" if action == "add" else "Removing"
        send(token, chat_id, f"{verb} @{username} on X... workflow triggered on {x_repo}")

    elif source == "yt":
        channel = handle if handle.startswith("@") else f"@{handle}"
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
    state_path = os.environ.get("STATE_PATH", "state.json")

    if not token or not chat_id:
        print("ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required.")
        sys.exit(1)
    if not gh_token:
        print("ERROR: GH_PAT is required to trigger workflows on other repos.")
        sys.exit(1)

    state = load_state(state_path)
    offset = state.get("last_command_update_id")
    if offset is not None:
        offset += 1  # mark previous batch as acknowledged

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
            process_command(text, token, chat_id, gh_token, x_repo, yt_repo)
            processed += 1
        except Exception as e:
            print(f"Error processing '{text}': {e}")
            send(token, chat_id, f"Error: {e}")

    save_state(state, state_path)
    print(f"Processed {processed} command(s) from {len(updates)} update(s).")


if __name__ == "__main__":
    main()
