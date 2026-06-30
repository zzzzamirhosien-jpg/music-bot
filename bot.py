import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from config import load_config
from database import Database
from services.music_engine import MusicEngine
from services.spotify_api import SpotifyService

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application):
    config = application.bot_data["config"]
    db = application.bot_data["db"]

    await db.connect()

    if config.owner_id:
        await db.add_admin(config.owner_id, "owner")

    logger.info("Bot started. DB connected, owner registered.")


async def post_shutdown(application):
    db = application.bot_data["db"]
    await db.close()
    logger.info("Bot stopped. DB closed.")


async def cache_cleanup_job(context):
    db = context.bot_data["db"]
    await db.cleanup_expired_cache()
    logger.info("Cache cleanup done.")


def main():
    config = load_config()
    db = Database()

    spotify = SpotifyService(config.spotify_client_id, config.spotify_client_secret)
    engine = MusicEngine(spotify_service=spotify)

    app = ApplicationBuilder().token(config.bot_token).build()

    app.bot_data["config"] = config
    app.bot_data["db"] = db
    app.bot_data["engine"] = engine

    app.post_init = post_init
    app.post_shutdown = post_shutdown

    from handlers.start import start, set_language
    from handlers.search import search_handler
    from handlers.search import callback_router
    from handlers.admin import admin_command, admin_callback_router, admin_text_handler

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))

    app.add_handler(CallbackQueryHandler(set_language, pattern=r"^lang:"))
    app.add_handler(CallbackQueryHandler(callback_router, pattern=r"^(src:|action:|dl:|pg:|noop)"))
    app.add_handler(CallbackQueryHandler(admin_callback_router, pattern=r"^admin:"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_text_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))

    app.job_queue.run_repeating(cache_cleanup_job, interval=3600, first=300)

    logger.info("Starting bot polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
