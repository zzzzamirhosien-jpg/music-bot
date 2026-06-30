# Telegram Music Bot

A Python Telegram bot that searches and downloads music from YouTube, Spotify, SoundCloud using free APIs (yt-dlp).

## Features

- Search songs from YouTube, YouTube Music, Spotify, SoundCloud
- Download and send MP3 directly in Telegram
- Admin panel inside Telegram (`/admin`)
- Bilingual: English + Persian (Farsi)
- Forced channel join for monetization
- Configurable daily download limits
- Ad system between downloads
- SQLite database (no external DB needed)
- Search result caching (1hr TTL)

## Requirements

- Python 3.11+
- FFmpeg (required for audio conversion)
- Telegram Bot Token (from @BotFather)
- Spotify API credentials (optional, for Spotify search)

## Setup

### 1. Get Bot Token

1. Open Telegram, search for @BotFather
2. Send `/newbot` and follow instructions
3. Copy the bot token

### 2. Get Spotify Credentials (Optional)

1. Go to https://developer.spotify.com/dashboard
2. Create an app
3. Copy Client ID and Client Secret

### 3. Install & Run

```bash
# Clone the repo
git clone <your-repo>
cd telegram-music-bot

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your tokens

# Make sure FFmpeg is installed
# Ubuntu/Debian: sudo apt install ffmpeg
# macOS: brew install ffmpeg

# Run the bot
python bot.py
```

### 4. Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create project
railway init

# Set environment variables
railway variables set BOT_TOKEN="your_token"
railway variables set OWNER_ID="your_telegram_id"
railway variables set SPOTIFY_CLIENT_ID="your_id"
railway variables set SPOTIFY_CLIENT_SECRET="your_secret"

# Add FFmpeg
railway variables set NIXPACKS_PKGS="ffmpeg"

# Deploy
railway up
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram bot token from @BotFather |
| `OWNER_ID` | Yes | Your Telegram user ID (for admin access) |
| `SPOTIFY_CLIENT_ID` | No | Spotify API client ID |
| `SPOTIFY_CLIENT_SECRET` | No | Spotify API client secret |
| `DEFAULT_LANGUAGE` | No | Default language: `en` or `fa` (default: `en`) |
| `CACHE_TTL_SECONDS` | No | Search cache TTL (default: 3600) |
| `DAILY_DOWNLOAD_LIMIT` | No | Max downloads per user per day (default: 10) |

## Bot Commands

| Command | Who | Description |
|---------|-----|-------------|
| `/start` | Everyone | Start the bot, select language |
| `/admin` | Admin only | Open admin panel |

## How It Works

1. User sends a song name
2. Bot searches YouTube via yt-dlp (or Spotify → YouTube)
3. Shows top 5 results as inline buttons
4. User taps a result
5. yt-dlp downloads the best audio quality
6. FFmpeg converts to MP3 320kbps
7. Bot sends the audio file via Telegram
8. Temp file is deleted

## Admin Panel

Send `/admin` to your bot to access:

- **Statistics** — user count, downloads, channels
- **Settings** — toggle bot, set daily limit, edit messages
- **Channels** — add/remove forced-join channels
- **Users** — ban/unban users
- **Ads** — set ad text shown after downloads
- **Broadcast** — send message to all users
- **Cache** — clear search cache

## Project Structure

```
telegram-music-bot/
├── bot.py                  # Entry point
├── config.py               # Configuration
├── database.py             # SQLite database
├── handlers/
│   ├── start.py            # /start handler
│   ├── search.py           # Search + results
│   ├── download.py         # Download + send audio
│   └── admin.py            # Admin panel
├── services/
│   ├── music_engine.py     # yt-dlp search/download
│   ├── spotify_api.py      # Spotify search
│   ├── cache.py            # Search cache
│   └── monetization.py     # Channel join, limits
├── utils/
│   ├── i18n.py             # EN + FA translations
│   └── formatters.py       # Progress bar, etc.
├── keyboards/
│   └── inline.py           # All inline keyboards
├── requirements.txt
├── Procfile                # Railway
├── railway.json
└── runtime.txt
```

## Notes

- **FFmpeg is required** for MP3 conversion
- Files larger than 50MB are skipped (Telegram limit)
- Downloads are deleted immediately after sending
- Search results are cached for 1 hour
- Owner (OWNER_ID) is never rate-limited
