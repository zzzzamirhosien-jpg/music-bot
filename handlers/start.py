from telegram import Update
from telegram.ext import ContextTypes
from database import Database
from utils.i18n import t
from keyboards.inline import language_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db: Database = context.bot_data["db"]
    user = update.effective_user

    await db.add_user(user.id, user.username or "", user.full_name)
    await db.update_user(user.id, user.username or "", user.full_name)

    user_row = await db.get_user(user.id)
    lang = user_row["language"] if user_row else "en"

    await update.message.reply_text(
        t("welcome", lang),
        parse_mode="HTML",
        reply_markup=language_keyboard(),
    )


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split(":")[1]
    db: Database = context.bot_data["db"]

    await db.set_language(query.from_user.id, lang)
    await query.edit_message_text(
        t("lang_set", lang),
        parse_mode="HTML",
    )
    await query.message.reply_text(
        t("welcome", lang),
        parse_mode="HTML",
        reply_markup=language_keyboard(),
    )
