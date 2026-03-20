import requests


class TelegramError(Exception):
    pass


def send_message(bot_token, chat_id, text, parse_mode="MarkdownV2"):
    """Send a message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, json=payload, timeout=30)
    if not resp.ok:
        raise TelegramError(
            f"Telegram API error {resp.status_code}: {resp.text}"
        )
    return resp.json()


def send_messages(bot_token, chat_id, messages):
    """Send multiple messages sequentially."""
    results = []
    for msg in messages:
        result = send_message(bot_token, chat_id, msg)
        results.append(result)
    return results
