# Telegram Notifier Bot

Sends a Telegram digest of the top viral content from X and YouTube scrapers. Also accepts Telegram commands to manage which accounts/channels are tracked.

---

## How It Works

1. Downloads the latest SQLite release assets from the scraper repos
2. Queries top-5 X posts and top-5 YouTube videos ranked by their precomputed `viral_score`
3. Sends a formatted digest to Telegram
4. Skips if data is stale or unchanged since last run

**Viral scoring** is computed by the scrapers, not here:
- **X**: `freshness × (0.40×view_momentum + 0.25×reach + 0.20×quality + 0.15×engagement_momentum)`
- **YouTube**: `freshness × (0.45×view_momentum + 0.25×reach + 0.20×quality + 0.10×engagement_momentum)` — Shorts and long-form ranked separately

---

## Telegram Commands

Send these in the Telegram chat. The bot polls every 5 minutes and replies with a confirmation.

| Command | Description |
|---------|-------------|
| `/add-x @username` | Start tracking an X account |
| `/remove-x @username` | Stop tracking an X account |
| `/add-youtube @handle` | Start tracking a YouTube channel |
| `/remove-youtube @handle` | Stop tracking a YouTube channel |
| `/help` | Show available commands |

Commands trigger a `workflow_dispatch` on the respective scraper repo, which updates its `config.json` and commits the change.

---

## Setup

### 1. Secrets (GitHub Actions → Settings → Secrets)

| Secret | Description |
|--------|-------------|
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | Your personal/channel/group chat ID |
| `GH_PAT` | GitHub personal access token with `repo` scope (needed to trigger workflows on scraper repos) |

### 2. Variables (optional overrides)

| Variable | Default | Description |
|----------|---------|-------------|
| `X_REPO` | `Fatih0234/x-botty` | X scraper repo |
| `YT_REPO` | `Fatih0234/youtube-competitor-tracker` | YT scraper repo |
| `X_RELEASE_ASSET_NAME` | `twitter.db` | X database filename |
| `YT_RELEASE_ASSET_NAME` | `youtube_competitor_tracker.db` | YT database filename |
| `FRESHNESS_HOURS` | `4` | Skip notification if data is older than N hours |

---

## Schedules

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `notify.yml` | `25 */3 * * *` | Digest — runs after X scraper (`:00`) and YT scraper (`:10`) |
| `commands.yml` | `*/5 * * * *` | Command polling — checks Telegram for new commands |

---

## Running Locally

```bash
cp .env.example .env
# fill in TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GH_PAT
pip install -r requirements.txt
export $(cat .env | grep -v '^#' | xargs)
python src/main.py      # send digest
python src/commands.py  # process pending commands
```

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
