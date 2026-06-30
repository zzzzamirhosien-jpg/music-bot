import os
import tempfile
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from utils.i18n import t
from utils.formatters import format_duration, progress_bar
from keyboards.inline import source_keyboard


async def download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db: Database = context.bot_data["db"]
    user_row = await db.get_user(query.from_user.id)
    lang = user_row["language"] if user_row else "en"

    parts = query.data.split(":")
    track_id = parts[1]
    source = parts[2] if len(parts) > 2 else "youtube"

    results = context.user_data.get("last_results", [])
    track = None
    for r in results:
        if r.track_id == track_id:
            track = r
            break

    if not track:
        await query.answer(t("error", lang), show_alert=True)
        return

    channels = await db.get_active_channels()
    if channels:
        bot = context.bot
        for ch in channels:
            try:
                member = await bot.get_chat_member(ch["channel_id"], query.from_user.id)
                if member.status not in ("member", "administrator", "creator"):
                    from keyboards.inline import join_channel_keyboard
                    await query.message.reply_text(
                        t("channel_required", lang, channel=ch["channel_name"]),
                        reply_markup=join_channel_keyboard(channels),
                    )
                    return
            except Exception:
                continue

    limit_setting = await db.get_setting("daily_limit") or "10"
    daily_limit = int(limit_setting)
    used = await db.get_download_count(query.from_user.id)
    if used >= daily_limit and query.from_user.id != context.bot_data["config"].owner_id:
        await query.answer(t("limit_reached", lang, used=used, limit=daily_limit), show_alert=True)
        return

    status_msg = await query.message.reply_text(
        t("downloading", lang, title=track.title, bar=progress_bar(0), percent=0),
        parse_mode="HTML",
    )

    engine = context.bot_data["engine"]
    tmpdir = tempfile.mkdtemp()

    try:
        filepath = await engine.download_track(track, tmpdir)

        if not filepath or not os.path.exists(filepath):
            await status_msg.edit_text(t("download_failed", lang), parse_mode="HTML")
            return

        file_size = os.path.getsize(filepath)
        if file_size > 50 * 1024 * 1024:
            await status_msg.edit_text(t("download_failed", lang), parse_mode="HTML")
            return

        await status_msg.edit_text(
            t("downloading", lang, title=track.title, bar=progress_bar(90), percent=90),
            parse_mode="HTML",
        )

        with open(filepath, "rb") as audio_file:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=audio_file,
                title=track.title,
                performer=track.artist,
                duration=track.duration,
                caption=f"🎵 {track.title}\n👤 {track.artist}\n⏱ {format_duration(track.duration)}",
            )

        await db.log_download(query.from_user.id, track.title, source, file_size)

        await status_msg.edit_text(
            t("download_complete", lang, title=track.title),
            parse_mode="HTML",
        )

        ad_lang = lang
        ad_text = await db.get_setting(f"ad_text_{ad_lang}")
        if ad_text:
            await query.message.reply_text(ad_text)

    except Exception as e:
        await status_msg.edit_text(t("download_failed", lang), parse_mode="HTML")
    finally:
        for f in os.listdir(tmpdir):
            os.remove(os.path.join(tmpdir, f))
        os.rmdir(tmpdir)


async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db: Database = context.bot_data["db"]
    user_row = await db.get_user(query.from_user.id)
    lang = user_row["language"] if user_row else "en"

    channels = await db.get_active_channels()
    if not channels:
        await query.answer("OK")
        return

    bot = context.bot
    all_joined = True
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch["channel_id"], query.from_user.id)
            if member.status not in ("member", "administrator", "creator"):
                all_joined = False
                break
        except Exception:
            continue

    if all_joined:
        await query.edit_message_text(
            t("welcome", lang),
            parse_mode="HTML",
            reply_markup=source_keyboard(),
        )
    else:
        await query.answer(t("channel_required", lang, channel=channels[0]["channel_name"]), show_alert=True)
