# Telegram Notifier Bot

A standalone bot that sends Telegram digests of the top viral content from X (Twitter) and YouTube scrapers.

## How It Works

1. Downloads the latest SQLite release assets from the scraper repos
2. Queries the top-5 X posts by engagement score and top-5 YouTube videos by viral score
3. Sends a formatted Telegram digest message
4. Tracks state to avoid duplicate notifications

## Setup

### Secrets (GitHub Actions)
- `TELEGRAM_BOT_TOKEN` — your Telegram bot token
- `TELEGRAM_CHAT_ID` — the chat/channel ID to send messages to

### Variables (GitHub Actions, optional)
| Variable | Default | Description |
|----------|---------|-------------|
| `X_REPO` | `Fatih0234/x-botty` | X scraper repo |
| `YT_REPO` | `Fatih0234/youtube-competitor-tracker` | YT scraper repo |
| `X_RELEASE_ASSET_NAME` | `twitter.db` | X database filename |
| `YT_RELEASE_ASSET_NAME` | `youtube_competitor_tracker.db` | YT database filename |
| `FRESHNESS_HOURS` | `4` | Skip if data older than N hours |

## Running Locally

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_CHAT_ID=your_chat_id
python src/main.py
```

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Schedule

The workflow runs at `25 */3 * * *` UTC — 25 minutes past every 3rd hour, after the X scraper (`:00`) and YT scraper (`:10`) have completed.
