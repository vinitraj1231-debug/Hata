"""
╔══════════════════════════════════════════════════════════════╗
║   PLUGIN: HELP — /start /help /ping /stats /uptime /lyrics   ║
╚══════════════════════════════════════════════════════════════╝
"""
import time
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from strings import (
    E, START_MSG, HELP_MAIN, HELP_PLAYBACK, HELP_QUEUE,
    HELP_CONTROLS, HELP_ADMIN, HELP_INFO, HELP_EXTRAS,
    ping_msg, stats_msg, uptime_msg,
)
from helpers.keyboards import help_main_kb, back_kb, close_kb
from config import ENABLE_LYRICS, GENIUS_TOKEN
import database as db

logger = logging.getLogger("vcbot.help")

BOT_START_TIME = time.time()
engine = None


def register(app: Client, _engine):
    global engine
    engine = _engine

    # ── /start ────────────────────────────────────────────────────────────────
    @app.on_message(filters.command("start"))
    async def cmd_start(client: Client, message: Message):
        name = message.from_user.first_name if message.from_user else "User"
        # Register chat
        await db.register_chat(message.chat.id, getattr(message.chat, "title", "PM"))
        await message.reply_text(
            START_MSG.format(name=name),
            reply_markup=help_main_kb(),
            disable_web_page_preview=True
        )

    # ── /help ─────────────────────────────────────────────────────────────────
    @app.on_message(filters.command("help"))
    async def cmd_help(client: Client, message: Message):
        await message.reply_text(HELP_MAIN, reply_markup=help_main_kb())

    # ── Help callbacks ────────────────────────────────────────────────────────
    _help_map = {
        "help_playback": HELP_PLAYBACK,
        "help_queue":    HELP_QUEUE,
        "help_controls": HELP_CONTROLS,
        "help_admin":    HELP_ADMIN,
        "help_info":     HELP_INFO,
        "help_extras":   HELP_EXTRAS,
    }

    @app.on_callback_query(filters.regex(r"^help_"))
    async def cb_help(client: Client, cb: CallbackQuery):
        data = cb.data
        if data == "help_main":
            await cb.message.edit_text(HELP_MAIN, reply_markup=help_main_kb())
        elif data in _help_map:
            await cb.message.edit_text(
                _help_map[data],
                reply_markup=back_kb("help_main")
            )
        await cb.answer()

    # ── /ping ─────────────────────────────────────────────────────────────────
    @app.on_message(filters.command("ping"))
    async def cmd_ping(client: Client, message: Message):
        t0 = time.time()
        m  = await message.reply_text(f"{E['ping']} Pinging…")
        ms = (time.time() - t0) * 1000
        await m.edit_text(ping_msg(ms))

    # ── /uptime ───────────────────────────────────────────────────────────────
    @app.on_message(filters.command("uptime"))
    async def cmd_uptime(client: Client, message: Message):
        from helpers.decorators import fmt_seconds
        elapsed = int(time.time() - BOT_START_TIME)
        await message.reply_text(uptime_msg(fmt_seconds(elapsed)))

    # ── /stats ────────────────────────────────────────────────────────────────
    @app.on_message(filters.command("stats"))
    async def cmd_stats(client: Client, message: Message):
        from helpers.decorators import fmt_seconds
        chat_id = message.chat.id
        qlen    = await db.db_queue_len(chat_id)
        played  = await db.get_played_today()
        elapsed = int(time.time() - BOT_START_TIME)

        # Count active VCs (rough heuristic)
        try:
            active_vcs = len(getattr(engine.cm.vc, "active_calls", {}) or {})
        except Exception:
            active_vcs = "N/A"

        d = {
            "active_vcs":    active_vcs,
            "total_queued":  qlen,
            "played_today":  played,
            "uptime":        fmt_seconds(elapsed),
        }
        await message.reply_text(stats_msg(d))

    # ── /lyrics ───────────────────────────────────────────────────────────────
    @app.on_message(filters.command("lyrics"))
    async def cmd_lyrics(client: Client, message: Message):
        if not ENABLE_LYRICS:
            await message.reply_text(f"{E['cross']} Lyrics feature is disabled.")
            return

        # Get query: command arg or current track
        if len(message.command) > 1:
            query = " ".join(message.command[1:])
        else:
            t = engine.now_playing(message.chat.id)
            if not t:
                await message.reply_text(f"{E['warn']} Provide a song name: `/lyrics <song>`")
                return
            query = t.title

        msg = await message.reply_text(f"{E['lyric']} Fetching lyrics for **{query}**…")
        lyrics = await _fetch_lyrics(query)
        if not lyrics:
            await msg.edit_text(f"{E['cross']} Lyrics not found for **{query}**.")
            return

        # Split if too long
        chunks = [lyrics[i:i+4000] for i in range(0, len(lyrics), 4000)]
        await msg.edit_text(
            f"{E['lyric']} **Lyrics — {query}**\n"
            f"{'━'*28}\n\n{chunks[0]}",
            reply_markup=close_kb()
        )
        for chunk in chunks[1:]:
            await message.reply_text(chunk)

    # ── Callback: close message ───────────────────────────────────────────────
    @app.on_callback_query(filters.regex("^close_msg$"))
    async def cb_close(client: Client, cb: CallbackQuery):
        try:
            await cb.message.delete()
        except Exception:
            await cb.answer("Cannot delete.")

    @app.on_callback_query(filters.regex("^noop$"))
    async def cb_noop(client: Client, cb: CallbackQuery):
        await cb.answer()


async def _fetch_lyrics(query: str) -> str:
    """Fetch lyrics via Genius API or simple scrape."""
    if not GENIUS_TOKEN:
        return await _scrape_lyrics(query)
    try:
        import aiohttp
        headers = {"Authorization": f"Bearer {GENIUS_TOKEN}"}
        url = f"https://api.genius.com/search?q={query}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                data = await r.json()
        hits = data.get("response", {}).get("hits", [])
        if not hits:
            return ""
        # Fetch lyrics page
        song_url = hits[0]["result"]["url"]
        async with aiohttp.ClientSession() as session:
            async with session.get(song_url) as r:
                html = await r.text()
        # Simple extraction
        import re
        matches = re.findall(r'<div[^>]*data-lyrics-container[^>]*>(.*?)</div>', html, re.DOTALL)
        if not matches:
            return ""
        raw = " ".join(matches)
        text = re.sub(r'<br\s*/?>', '\n', raw)
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()
    except Exception as e:
        logger.warning("Genius API error: %s", e)
        return ""


async def _scrape_lyrics(query: str) -> str:
    """Fallback lyrics scrape."""
    return f"_(Genius API token not set. Add `GENIUS_TOKEN` to .env to enable lyrics.)_"
