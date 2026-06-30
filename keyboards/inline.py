from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.i18n import t


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇸 English", callback_data="lang:en")],
        [InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang:fa")],
    ])


def source_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📺 YouTube", callback_data="src:youtube"),
            InlineKeyboardButton("🎵 Spotify", callback_data="src:spotify"),
        ],
        [
            InlineKeyboardButton("☁️ SoundCloud", callback_data="src:soundcloud"),
        ],
    ])


def results_keyboard(results: list, page: int, per_page: int = 5, source: str = "youtube") -> InlineKeyboardMarkup:
    start = (page - 1) * per_page
    end = start + per_page
    page_results = results[start:end]
    total_pages = max(1, (len(results) + per_page - 1) // per_page)

    buttons = []
    for i, track in enumerate(page_results):
        idx = start + i + 1
        text = f"{idx}. {track.artist} - {track.title}"
        if len(text) > 50:
            text = text[:47] + "..."
        buttons.append([InlineKeyboardButton(text, callback_data=f"dl:{track.track_id}:{source}")])

    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("◀️", callback_data=f"pg:{source}:{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("▶️", callback_data=f"pg:{source}:{page + 1}"))
    buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("🔍 New Search", callback_data="action:search")])

    return InlineKeyboardMarkup(buttons)


def confirm_download_keyboard(track_id: str, source: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬇️ Download MP3", callback_data=f"dl:{track_id}:{source}")],
        [InlineKeyboardButton("🔙 Back to Results", callback_data="action:back")],
    ])


def join_channel_keyboard(channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        username = ch["channel_name"]
        buttons.append([InlineKeyboardButton(f"📢 Join @{username}", url=f"https://t.me/{username}")])
    buttons.append([InlineKeyboardButton("✅ I Joined", callback_data="check_join")])
    return InlineKeyboardMarkup(buttons)


def admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistics", callback_data="admin:stats")],
        [InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin:settings")],
        [InlineKeyboardButton("📢 Channels", callback_data="admin:channels")],
        [InlineKeyboardButton("👥 Users", callback_data="admin:users")],
        [InlineKeyboardButton("📝 Ads", callback_data="admin:ads")],
        [InlineKeyboardButton("📣 Broadcast", callback_data="admin:broadcast")],
        [InlineKeyboardButton("🔄 Clear Cache", callback_data="admin:cache")],
    ])


def admin_settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    bot_status = "✅ ON" if settings.get("bot_enabled", "1") == "1" else "❌ OFF"
    limit = settings.get("daily_limit", "10")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Bot: {bot_status}", callback_data="admin:toggle_bot")],
        [InlineKeyboardButton(f"Daily Limit: {limit}", callback_data="admin:set_limit")],
        [InlineKeyboardButton("📝 Welcome EN", callback_data="admin:set_welcome_en")],
        [InlineKeyboardButton("📝 Welcome FA", callback_data="admin:set_welcome_fa")],
        [InlineKeyboardButton("📝 Ad EN", callback_data="admin:set_ad_en")],
        [InlineKeyboardButton("📝 Ad FA", callback_data="admin:set_ad_fa")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin:main")],
    ])


def admin_channels_keyboard(channels: list) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        buttons.append([
            InlineKeyboardButton(f"📢 @{ch['channel_name']}", callback_data="noop"),
            InlineKeyboardButton("❌", callback_data=f"admin:rm_channel:{ch['channel_id']}"),
        ])
    buttons.append([InlineKeyboardButton("➕ Add Channel", callback_data="admin:add_channel")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="admin:main")])
    return InlineKeyboardMarkup(buttons)


def admin_users_keyboard(users: list, page: int = 1, per_page: int = 8) -> InlineKeyboardMarkup:
    start = (page - 1) * per_page
    end = start + per_page
    page_users = users[start:end]
    total_pages = max(1, (len(users) + per_page - 1) // per_page)

    buttons = []
    for u in page_users:
        status = "🚫" if u["is_banned"] else "✅"
        name = f"@{u['username']}" if u["username"] else u["full_name"]
        action = "unban" if u["is_banned"] else "ban"
        btn_text = f"{status} {name}"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"admin:{action}:{u['user_id']}")])

    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("◀️", callback_data=f"admin:users_page:{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("▶️", callback_data=f"admin:users_page:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="admin:main")])
    return InlineKeyboardMarkup(buttons)


def admin_broadcast_keyboard(count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ Send to {count} users", callback_data="admin:broadcast_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="admin:main")],
    ])


def back_button(callback: str = "admin:main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=callback)]])
