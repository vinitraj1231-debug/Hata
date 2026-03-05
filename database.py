"""
╔══════════════════════════════════════════╗
║         DATABASE — aiosqlite layer       ║
╚══════════════════════════════════════════╝
"""
import time
import logging
import aiosqlite
from config import DB_PATH

logger = logging.getLogger("vcbot.db")


# ═══════════════════════════════════════════════════════════════════
# INIT
# ═══════════════════════════════════════════════════════════════════
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS queue (
                track_id     TEXT,
                chat_id      INTEGER,
                position     INTEGER,
                title        TEXT,
                filepath     TEXT,
                duration     INTEGER DEFAULT 0,
                url          TEXT,
                requested_by TEXT,
                added_at     REAL,
                PRIMARY KEY (track_id, chat_id)
            );

            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id      INTEGER PRIMARY KEY,
                repeat_mode  TEXT    DEFAULT 'none',
                volume       REAL    DEFAULT 100,
                is_muted     INTEGER DEFAULT 0,
                auth_users   TEXT    DEFAULT '',
                banned_users TEXT    DEFAULT '',
                lang         TEXT    DEFAULT 'en'
            );

            CREATE TABLE IF NOT EXISTS play_stats (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id      INTEGER,
                track_id     TEXT,
                title        TEXT,
                played_at    REAL
            );

            CREATE TABLE IF NOT EXISTS global_bans (
                user_id      INTEGER PRIMARY KEY,
                reason       TEXT,
                banned_at    REAL
            );

            CREATE TABLE IF NOT EXISTS bot_chats (
                chat_id      INTEGER PRIMARY KEY,
                chat_title   TEXT,
                joined_at    REAL
            );
        """)
        await db.commit()
    logger.info("Database initialised at %s", DB_PATH)


# ═══════════════════════════════════════════════════════════════════
# QUEUE
# ═══════════════════════════════════════════════════════════════════
async def db_enqueue(chat_id: int, track) -> int:
    """Returns new queue position."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT IFNULL(MAX(position), 0) FROM queue WHERE chat_id = ?", (chat_id,)
        )
        row = await cur.fetchone()
        pos = (row[0] or 0) + 1
        await db.execute(
            """INSERT OR REPLACE INTO queue
               (track_id, chat_id, position, title, filepath, duration, url, requested_by, added_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (track.id, chat_id, pos, track.title, track.filepath,
             track.duration, track.url, track.requested_by, time.time()),
        )
        await db.commit()
    return pos


async def db_pop_next(chat_id: int):
    """Pop and return the next track (lowest position)."""
    from helpers.models import Track
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """SELECT track_id, title, filepath, duration, url, requested_by
               FROM queue WHERE chat_id = ? ORDER BY position ASC LIMIT 1""",
            (chat_id,)
        )
        row = await cur.fetchone()
        if not row:
            return None
        tid, title, fp, dur, url, rb = row
        await db.execute(
            "DELETE FROM queue WHERE track_id = ? AND chat_id = ?", (tid, chat_id)
        )
        await db.commit()
    return Track(id=tid, title=title, filepath=fp, duration=int(dur or 0),
                 url=url, requested_by=rb)


async def db_get_queue(chat_id: int, limit: int = 500):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """SELECT track_id, title, filepath, duration, url, requested_by, position
               FROM queue WHERE chat_id = ? ORDER BY position ASC LIMIT ?""",
            (chat_id, limit),
        )
        rows = await cur.fetchall()
    return [
        {"id": r[0], "title": r[1], "filepath": r[2], "duration": int(r[3] or 0),
         "url": r[4], "requested_by": r[5], "pos": r[6]}
        for r in rows
    ]


async def db_clear_queue(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM queue WHERE chat_id = ?", (chat_id,))
        await db.commit()


async def db_remove_track(chat_id: int, position: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT track_id FROM queue WHERE chat_id = ? AND position = ?",
            (chat_id, position)
        )
        row = await cur.fetchone()
        if not row:
            return False
        await db.execute(
            "DELETE FROM queue WHERE track_id = ? AND chat_id = ?",
            (row[0], chat_id)
        )
        await db.commit()
    return True


async def db_shuffle_queue(chat_id: int):
    import random
    rows = await db_get_queue(chat_id)
    random.shuffle(rows)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM queue WHERE chat_id = ?", (chat_id,))
        for pos, t in enumerate(rows, start=1):
            await db.execute(
                """INSERT INTO queue
                   (track_id, chat_id, position, title, filepath, duration, url, requested_by, added_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (t["id"], chat_id, pos, t["title"], t["filepath"],
                 t["duration"], t["url"], t["requested_by"], time.time()),
            )
        await db.commit()


async def db_move_track(chat_id: int, from_pos: int, to_pos: int) -> bool:
    rows = await db_get_queue(chat_id)
    if from_pos < 1 or from_pos > len(rows) or to_pos < 1 or to_pos > len(rows):
        return False
    item = rows.pop(from_pos - 1)
    rows.insert(to_pos - 1, item)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM queue WHERE chat_id = ?", (chat_id,))
        for pos, t in enumerate(rows, start=1):
            await db.execute(
                """INSERT INTO queue
                   (track_id, chat_id, position, title, filepath, duration, url, requested_by, added_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (t["id"], chat_id, pos, t["title"], t["filepath"],
                 t["duration"], t["url"], t["requested_by"], time.time()),
            )
        await db.commit()
    return True


async def db_queue_len(chat_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM queue WHERE chat_id = ?", (chat_id,)
        )
        row = await cur.fetchone()
    return row[0] if row else 0


# ═══════════════════════════════════════════════════════════════════
# CHAT SETTINGS
# ═══════════════════════════════════════════════════════════════════
async def _ensure_settings(db, chat_id: int):
    await db.execute(
        "INSERT OR IGNORE INTO chat_settings(chat_id) VALUES(?)", (chat_id,)
    )


async def get_setting(chat_id: int, key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            f"SELECT {key} FROM chat_settings WHERE chat_id = ?", (chat_id,)
        )
        row = await cur.fetchone()
    return row[0] if row else None


async def set_setting(chat_id: int, key: str, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_settings(db, chat_id)
        await db.execute(
            f"UPDATE chat_settings SET {key} = ? WHERE chat_id = ?", (value, chat_id)
        )
        await db.commit()


async def get_volume(chat_id: int) -> float:
    v = await get_setting(chat_id, "volume")
    return float(v) if v is not None else 100.0


async def set_volume(chat_id: int, vol: float):
    await set_setting(chat_id, "volume", vol)


async def get_repeat(chat_id: int) -> str:
    v = await get_setting(chat_id, "repeat_mode")
    return v or "none"


async def set_repeat(chat_id: int, mode: str):
    await set_setting(chat_id, "repeat_mode", mode)


async def get_muted(chat_id: int) -> bool:
    v = await get_setting(chat_id, "is_muted")
    return bool(v)


async def set_muted(chat_id: int, muted: bool):
    await set_setting(chat_id, "is_muted", int(muted))


# ═══════════════════════════════════════════════════════════════════
# AUTH USERS (per-chat)
# ═══════════════════════════════════════════════════════════════════
async def _get_user_list(chat_id: int, col: str):
    v = await get_setting(chat_id, col)
    if not v:
        return []
    return [int(x) for x in v.split(",") if x.strip()]


async def _set_user_list(chat_id: int, col: str, lst):
    await set_setting(chat_id, col, ",".join(str(x) for x in lst))


async def auth_user(chat_id: int, user_id: int):
    lst = await _get_user_list(chat_id, "auth_users")
    if user_id not in lst:
        lst.append(user_id)
    await _set_user_list(chat_id, "auth_users", lst)


async def unauth_user(chat_id: int, user_id: int):
    lst = await _get_user_list(chat_id, "auth_users")
    lst = [x for x in lst if x != user_id]
    await _set_user_list(chat_id, "auth_users", lst)


async def get_auth_users(chat_id: int):
    return await _get_user_list(chat_id, "auth_users")


# ═══════════════════════════════════════════════════════════════════
# GLOBAL BANS
# ═══════════════════════════════════════════════════════════════════
async def gban_user(user_id: int, reason: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO global_bans(user_id, reason, banned_at) VALUES(?,?,?)",
            (user_id, reason, time.time())
        )
        await db.commit()


async def ungban_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM global_bans WHERE user_id = ?", (user_id,))
        await db.commit()


async def is_gbanned(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM global_bans WHERE user_id = ?", (user_id,)
        )
        row = await cur.fetchone()
    return row is not None


# ═══════════════════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════════════════
async def log_play(chat_id: int, track):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO play_stats(chat_id, track_id, title, played_at) VALUES(?,?,?,?)",
            (chat_id, track.id, track.title, time.time())
        )
        await db.commit()


async def get_played_today(chat_id: int = None) -> int:
    day_start = time.time() - 86400
    async with aiosqlite.connect(DB_PATH) as db:
        if chat_id:
            cur = await db.execute(
                "SELECT COUNT(*) FROM play_stats WHERE chat_id = ? AND played_at > ?",
                (chat_id, day_start)
            )
        else:
            cur = await db.execute(
                "SELECT COUNT(*) FROM play_stats WHERE played_at > ?", (day_start,)
            )
        row = await cur.fetchone()
    return row[0] if row else 0


# ═══════════════════════════════════════════════════════════════════
# BOT CHATS REGISTRY
# ═══════════════════════════════════════════════════════════════════
async def register_chat(chat_id: int, title: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO bot_chats(chat_id, chat_title, joined_at) VALUES(?,?,?)",
            (chat_id, title, time.time())
        )
        await db.commit()


async def get_all_chats():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT chat_id, chat_title FROM bot_chats")
        return await cur.fetchall()
