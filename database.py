import aiosqlite
import json
from datetime import datetime, date
from typing import Optional


class Database:
    def __init__(self, db_path: str = "data/bot.db"):
        self.db_path = db_path
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.init()

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def init(self):
        await self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                language TEXT DEFAULT 'en',
                is_banned INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                last_active TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS admin_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS search_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT NOT NULL,
                source TEXT NOT NULL,
                results TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                expires_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_cache_hash ON search_cache(query_hash, source);

            CREATE TABLE IF NOT EXISTS download_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                track_title TEXT,
                source TEXT,
                file_size INTEGER,
                download_date TEXT DEFAULT (date('now'))
            );

            CREATE TABLE IF NOT EXISTS channel_whitelist (
                channel_id INTEGER PRIMARY KEY,
                channel_name TEXT,
                is_active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                role TEXT DEFAULT 'admin'
            );

            INSERT OR IGNORE INTO admin_settings (key, value) VALUES
                ('bot_enabled', '1'),
                ('daily_limit', '10'),
                ('welcome_en', '🎵 Welcome to Music Bot!\n\nSend me a song name and I''ll find it for you.'),
                ('welcome_fa', '🎵 به ربات موزیک خوش آمدید!\n\nنام آهنگ را بفرستید تا برایتان پیدا کنم.'),
                ('ad_text_en', ''),
                ('ad_text_fa', '');
        """)
        await self.conn.commit()

    async def execute(self, query: str, params=()):
        cursor = await self.conn.execute(query, params)
        await self.conn.commit()
        return cursor

    async def fetch_one(self, query: str, params=()):
        cursor = await self.conn.execute(query, params)
        return await cursor.fetchone()

    async def fetch_all(self, query: str, params=()):
        cursor = await self.conn.execute(query, params)
        return await cursor.fetchall()

    # --- Users ---

    async def add_user(self, user_id: int, username: str, full_name: str, language: str = "en"):
        await self.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name, language) VALUES (?, ?, ?, ?)",
            (user_id, username, full_name, language),
        )

    async def update_user(self, user_id: int, username: str = None, full_name: str = None):
        if username is not None:
            await self.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        if full_name is not None:
            await self.execute("UPDATE users SET full_name = ? WHERE user_id = ?", (full_name, user_id))
        await self.execute("UPDATE users SET last_active = datetime('now') WHERE user_id = ?", (user_id,))

    async def get_user(self, user_id: int):
        return await self.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))

    async def set_language(self, user_id: int, language: str):
        await self.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))

    async def ban_user(self, user_id: int):
        await self.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))

    async def unban_user(self, user_id: int):
        await self.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))

    async def get_all_users(self):
        return await self.fetch_all("SELECT * FROM users ORDER BY last_active DESC")

    async def get_user_count(self):
        row = await self.fetch_one("SELECT COUNT(*) as cnt FROM users")
        return row["cnt"] if row else 0

    # --- Settings ---

    async def get_setting(self, key: str):
        row = await self.fetch_one("SELECT value FROM admin_settings WHERE key = ?", (key,))
        return row["value"] if row else None

    async def set_setting(self, key: str, value: str):
        await self.execute(
            "INSERT OR REPLACE INTO admin_settings (key, value) VALUES (?, ?)", (key, value)
        )

    async def get_all_settings(self):
        rows = await self.fetch_all("SELECT key, value FROM admin_settings")
        return {row["key"]: row["value"] for row in rows}

    # --- Cache ---

    async def cache_results(self, query_hash: str, source: str, results_json: str, ttl: int = 3600):
        await self.execute(
            "DELETE FROM search_cache WHERE query_hash = ? AND source = ?", (query_hash, source)
        )
        expires = datetime.utcnow().isoformat(timespec="seconds")
        await self.execute(
            "INSERT INTO search_cache (query_hash, source, results, expires_at) VALUES (?, ?, ?, datetime(?, '+' || ? || ' seconds'))",
            (query_hash, source, results_json, expires, ttl),
        )

    async def get_cached(self, query_hash: str, source: str):
        row = await self.fetch_one(
            "SELECT results FROM search_cache WHERE query_hash = ? AND source = ? AND expires_at > datetime('now')",
            (query_hash, source),
        )
        if row:
            return json.loads(row["results"])
        return None

    async def cleanup_expired_cache(self):
        await self.execute("DELETE FROM search_cache WHERE expires_at <= datetime('now')")

    async def get_cache_count(self):
        row = await self.fetch_one("SELECT COUNT(*) as cnt FROM search_cache")
        return row["cnt"] if row else 0

    async def clear_all_cache(self):
        await self.execute("DELETE FROM search_cache")

    # --- Downloads ---

    async def log_download(self, user_id: int, track_title: str, source: str, file_size: int = 0):
        await self.execute(
            "INSERT INTO download_log (user_id, track_title, source, file_size) VALUES (?, ?, ?, ?)",
            (user_id, track_title, source, file_size),
        )

    async def get_download_count(self, user_id: int, target_date: str = None):
        if target_date is None:
            target_date = date.today().isoformat()
        row = await self.fetch_one(
            "SELECT COUNT(*) as cnt FROM download_log WHERE user_id = ? AND download_date = ?",
            (user_id, target_date),
        )
        return row["cnt"] if row else 0

    async def get_total_downloads(self):
        row = await self.fetch_one("SELECT COUNT(*) as cnt FROM download_log")
        return row["cnt"] if row else 0

    # --- Admins ---

    async def add_admin(self, user_id: int, role: str = "admin"):
        await self.execute("INSERT OR REPLACE INTO admins (user_id, role) VALUES (?, ?)", (user_id, role))

    async def remove_admin(self, user_id: int):
        await self.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))

    async def is_admin(self, user_id: int):
        row = await self.fetch_one("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        return row is not None

    async def get_admins(self):
        return await self.fetch_all("SELECT * FROM admins")

    # --- Channels ---

    async def add_channel(self, channel_id: int, channel_name: str):
        await self.execute(
            "INSERT OR REPLACE INTO channel_whitelist (channel_id, channel_name, is_active) VALUES (?, ?, 1)",
            (channel_id, channel_name),
        )

    async def remove_channel(self, channel_id: int):
        await self.execute("DELETE FROM channel_whitelist WHERE channel_id = ?", (channel_id,))

    async def get_active_channels(self):
        return await self.fetch_all("SELECT * FROM channel_whitelist WHERE is_active = 1")
