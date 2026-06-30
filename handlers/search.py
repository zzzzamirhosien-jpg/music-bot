import json
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from utils.i18n import t
from utils.formatters import format_duration
from keyboards.inline import (
    language_keyboard,
    source_keyboard,
    results_keyboard,
    back_button,
    join_channel_keyboard,
    admin_main_keyboard,
    admin_settings_keyboard,
    admin_channels_keyboard,
    admin_users_keyboard,
    admin_broadcast_keyboard,
)
from services.cache import get_or_search


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    db: Database = context.bot_data["db"]
    user_row = await db.get_user(query.from_user.id)
    lang = user_row["language"] if user_row else "en"

    if data.startswith("lang:"):
        from handlers.start import set_language
        await set_language(update, context)
        return

    if data.startswith("src:"):
        source = data.split(":")[1]
        context.user_data["source"] = source
        await query.edit_message_text(
            t("search_placeholder", lang, query="..."),
            parse_mode="HTML",
        )
        return

    if data == "action:search":
        await query.edit_message_text(
            t("search_placeholder", lang, query=""),
            parse_mode="HTML",
        )
        return

    if data == "action:back":
        await query.edit_message_text(
            t("welcome", lang),
            parse_mode="HTML",
            reply_markup=source_keyboard(),
        )
        return

    if data == "noop":
        await query.answer("OK")
        return

    if data.startswith("pg:"):
        parts = data.split(":")
        source = parts[1]
        page = int(parts[2])
        cached_results = context.user_data.get("last_results", [])
        if cached_results:
            await query.edit_message_reply_markup(
                reply_markup=results_keyboard(cached_results, page, source=source)
            )
        return

    if data.startswith("dl:"):
        from handlers.download import download_callback
        await download_callback(update, context)
        return

    if data == "check_join":
        from handlers.download import check_join_callback
        await check_join_callback(update, context)
        return

    if data.startswith("admin:"):
        from handlers.admin import admin_callback_router
        await admin_callback_router(update, context)
        return


async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db: Database = context.bot_data["db"]
    user_row = await db.get_user(update.effective_user.id)
    lang = user_row["language"] if user_row else "en"

    bot_enabled = await db.get_setting("bot_enabled")
    if bot_enabled == "0":
        await update.message.reply_text(t("bot_disabled", lang))
        return

    channels = await db.get_active_channels()
    if channels:
        bot = context.bot
        all_joined = True
        unjoined = None
        for ch in channels:
            try:
                member = await bot.get_chat_member(ch["channel_id"], update.effective_user.id)
                if member.status not in ("member", "administrator", "creator"):
                    all_joined = False
                    unjoined = ch
                    break
            except Exception:
                continue
        if not all_joined and unjoined:
            await update.message.reply_text(
                t("channel_required", lang, channel=unjoined["channel_name"]),
                reply_markup=join_channel_keyboard(channels),
            )
            return

    source = context.user_data.get("source", "youtube")
    query_text = update.message.text.strip()
    if not query_text:
        return

    searching_msg = await update.message.reply_text(
        t("search_placeholder", lang, query=query_text),
        parse_mode="HTML",
    )

    engine = context.bot_data["engine"]
    cache_ttl = context.bot_data["config"].cache_ttl_seconds
    results = await get_or_search(engine, db, query_text, source, ttl=cache_ttl)

    context.user_data["last_results"] = results
    context.user_data["last_query"] = query_text

    if not results:
        await searching_msg.edit_text(
            t("no_results", lang, query=query_text),
            parse_mode="HTML",
        )
        return

    header = t("results_header", lang, query=query_text, count=len(results))
    await searching_msg.edit_text(
        header,
        parse_mode="HTML",
        reply_markup=results_keyboard(results, 1, source=source),
    )
