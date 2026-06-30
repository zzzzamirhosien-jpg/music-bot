import os
from dataclasses import dataclass, field


@dataclass
class BotConfig:
    bot_token: str = ""
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    owner_id: int = 0
    default_language: str = "en"
    cache_ttl_seconds: int = 3600
    daily_download_limit: int = 10

    def __post_init__(self):
        if not self.bot_token:
            raise ValueError("BOT_TOKEN is required")
        if not self.owner_id:
            raise ValueError("OWNER_ID is required")


def _safe_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def load_config() -> BotConfig:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    return BotConfig(
        bot_token=os.getenv("BOT_TOKEN", ""),
        spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
        spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", ""),
        owner_id=_safe_int(os.getenv("OWNER_ID", "0")),
        default_language=os.getenv("DEFAULT_LANGUAGE", "en"),
        cache_ttl_seconds=_safe_int(os.getenv("CACHE_TTL_SECONDS", "3600"), 3600),
        daily_download_limit=_safe_int(os.getenv("DAILY_DOWNLOAD_LIMIT", "10"), 10),
    )
