from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from utils.i18n import t
from keyboards.inline import admin_main_keyboard


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db: Database = context.bot_data["db"]
    user_id = update.effective_user.id
    owner_id = context.bot_data["config"].owner_id

    is_admin = await db.is_admin(user_id) or user_id == owner_id
    if not is_admin:
        user_row = await db.get_user(user_id)
        lang = user_row["language"] if user_row else "en"
        await update.message.reply_text(t("admin_no_access", lang))
        return

    await update.message.reply_text(
        t("admin_panel", "en"),
        parse_mode="HTML",
        reply_markup=admin_main_keyboard(),
    )


async def admin_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    db: Database = context.bot_data["db"]
    user_id = query.from_user.id
    owner_id = context.bot_data["config"].owner_id

    is_admin = await db.is_admin(user_id) or user_id == owner_id
    if not is_admin:
        await query.answer("Access denied", show_alert=True)
        return

    if data == "admin:main":
        from keyboards.inline import admin_main_keyboard
        await query.edit_message_text(
            t("admin_panel", "en"),
            parse_mode="HTML",
            reply_markup=admin_main_keyboard(),
        )
        return

    if data == "admin:stats":
        from keyboards.inline import back_button
        user_count = await db.get_user_count()
        download_count = await db.get_total_downloads()
        channels = await db.get_active_channels()
        text = t("admin_stats", "en",
                 users=user_count,
                 downloads=download_count,
                 searches="N/A",
                 channels=len(channels))
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_button())
        return

    if data == "admin:settings":
        from keyboards.inline import admin_settings_keyboard
        settings = await db.get_all_settings()
        await query.edit_message_text(
            t("admin_settings", "en"),
            parse_mode="HTML",
            reply_markup=admin_settings_keyboard(settings),
        )
        return

    if data == "admin:toggle_bot":
        current = await db.get_setting("bot_enabled")
        new_val = "0" if current == "1" else "1"
        await db.set_setting("bot_enabled", new_val)
        status = "ON" if new_val == "1" else "OFF"
        from keyboards.inline import admin_settings_keyboard
        settings = await db.get_all_settings()
        await query.edit_message_reply_markup(reply_markup=admin_settings_keyboard(settings))
        await query.answer(f"Bot {status}")
        return

    if data == "admin:set_limit":
        context.user_data["admin_action"] = "set_limit"
        await query.edit_message_text(t("limit_prompt", "en"))
        return

    if data == "admin:set_welcome_en":
        context.user_data["admin_action"] = "set_welcome_en"
        await query.edit_message_text("📝 Send the welcome message in English:")
        return

    if data == "admin:set_welcome_fa":
        context.user_data["admin_action"] = "set_welcome_fa"
        await query.edit_message_text("📝 Send the welcome message in Persian:")
        return

    if data == "admin:set_ad_en":
        context.user_data["admin_action"] = "set_ad_en"
        await query.edit_message_text(t("ad_prompt_en", "en"))
        return

    if data == "admin:set_ad_fa":
        context.user_data["admin_action"] = "set_ad_fa"
        await query.edit_message_text(t("ad_prompt_fa", "en"))
        return

    if data == "admin:channels":
        from keyboards.inline import admin_channels_keyboard
        channels = await db.get_active_channels()
        await query.edit_message_text(
            t("admin_channels", "en"),
            parse_mode="HTML",
            reply_markup=admin_channels_keyboard(channels),
        )
        return

    if data == "admin:add_channel":
        context.user_data["admin_action"] = "add_channel"
        await query.edit_message_text(t("add_channel_prompt", "en"))
        return

    if data.startswith("admin:rm_channel:"):
        channel_id = int(data.split(":")[2])
        await db.remove_channel(channel_id)
        from keyboards.inline import admin_channels_keyboard
        channels = await db.get_active_channels()
        await query.edit_message_reply_markup(reply_markup=admin_channels_keyboard(channels))
        await query.answer("Channel removed")
        return

    if data == "admin:users":
        from keyboards.inline import admin_users_keyboard
        users = await db.get_all_users()
        await query.edit_message_text(
            t("admin_users", "en"),
            parse_mode="HTML",
            reply_markup=admin_users_keyboard(users),
        )
        return

    if data.startswith("admin:users_page:"):
        page = int(data.split(":")[2])
        from keyboards.inline import admin_users_keyboard
        users = await db.get_all_users()
        await query.edit_message_reply_markup(reply_markup=admin_users_keyboard(users, page))
        return

    if data.startswith("admin:ban:"):
        uid = int(data.split(":")[2])
        await db.ban_user(uid)
        from keyboards.inline import admin_users_keyboard
        users = await db.get_all_users()
        await query.edit_message_reply_markup(reply_markup=admin_users_keyboard(users))
        await query.answer(f"User {uid} banned")

    if data.startswith("admin:unban:"):
        uid = int(data.split(":")[2])
        await db.unban_user(uid)
        from keyboards.inline import admin_users_keyboard
        users = await db.get_all_users()
        await query.edit_message_reply_markup(reply_markup=admin_users_keyboard(users))
        await query.answer(f"User {uid} unbanned")

    if data == "admin:ads":
        from keyboards.inline import back_button
        ad_en = await db.get_setting("ad_text_en") or "(not set)"
        ad_fa = await db.get_setting("ad_text_fa") or "(not set)"
        text = f"📝 <b>Ad Management</b>\n\nEN: {ad_en}\n\nFA: {ad_fa}"
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_button())
        context.user_data["admin_action"] = None
        return

    if data == "admin:broadcast":
        from keyboards.inline import back_button
        user_count = await db.get_user_count()
        context.user_data["admin_action"] = "broadcast"
        await query.edit_message_text(
            t("broadcast_prompt", "en") + f"\n\n({user_count} users)",
            parse_mode="HTML",
            reply_markup=back_button(),
        )
        return

    if data == "admin:broadcast_confirm":
        pending_msg = context.user_data.get("broadcast_message")
        if pending_msg:
            users = await db.get_all_users()
            sent = 0
            for u in users:
                try:
                    await context.bot.send_message(u["user_id"], pending_msg)
                    sent += 1
                except Exception:
                    pass
            await query.edit_message_text(t("broadcast_sent", "en", count=sent))
            context.user_data.pop("broadcast_message", None)
        context.user_data["admin_action"] = None
        return

    if data == "admin:cache":
        db_conn = db.conn
        cursor = await db_conn.execute("SELECT COUNT(*) as cnt FROM search_cache")
        row = await cursor.fetchone()
        count = row["cnt"] if row else 0
        await query.edit_message_text(
            f"🔄 Cache: {count} entries\n\nClear all cached search results?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 Clear All", callback_data="admin:cache_clear")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin:main")],
            ]),
        )
        return

    if data == "admin:cache_clear":
        await db.cleanup_expired_cache()
        db_conn = db.conn
        await db_conn.execute("DELETE FROM search_cache")
        await db_conn.commit()
        await query.edit_message_text(t("cache_cleared", "en"))
        return


async def admin_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db: Database = context.bot_data["db"]
    user_id = update.effective_user.id
    owner_id = context.bot_data["config"].owner_id

    is_admin = await db.is_admin(user_id) or user_id == owner_id
    if not is_admin:
        return

    action = context.user_data.get("admin_action")
    if not action:
        return

    text = update.message.text.strip()

    if action == "set_limit":
        if text.isdigit() and int(text) > 0:
            await db.set_setting("daily_limit", text)
            await update.message.reply_text(t("limit_set", "en", limit=text))
        else:
            await update.message.reply_text("❌ Send a positive number.")

    elif action == "set_welcome_en":
        await db.set_setting("welcome_en", text)
        await update.message.reply_text("✅ Welcome message (EN) updated.")
    elif action == "set_welcome_fa":
        await db.set_setting("welcome_fa", text)
        await update.message.reply_text("✅ Welcome message (FA) updated.")
    elif action == "set_ad_en":
        await db.set_setting("ad_text_en", text)
        await update.message.reply_text(t("ad_set", "en"))
    elif action == "set_ad_fa":
        await db.set_setting("ad_text_fa", text)
        await update.message.reply_text(t("ad_set", "en"))

    elif action == "add_channel":
        channel_name = text.lstrip("@")
        try:
            chat = await context.bot.get_chat(f"@{channel_name}")
            await db.add_channel(chat.id, channel_name)
            await update.message.reply_text(t("channel_added", "en", channel=channel_name))
        except Exception:
            try:
                chat = await context.bot.get_chat(int(text))
                await db.add_channel(chat.id, str(chat.id))
                await update.message.reply_text(t("channel_added", "en", channel=str(chat.id)))
            except Exception:
                await update.message.reply_text(t("channel_not_found", "en"))

    elif action == "broadcast":
        context.user_data["broadcast_message"] = text
        users = await db.get_all_users()
        from keyboards.inline import admin_broadcast_keyboard
        await update.message.reply_text(
            t("broadcast_confirm", "en", count=len(users)),
            reply_markup=admin_broadcast_keyboard(len(users)),
        )

    context.user_data["admin_action"] = None
