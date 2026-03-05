"""
╔══════════════════════════════════════════════════════════════╗
║   PLUGIN: PLAY — /play /pause /resume /skip /stop /join      ║
╚══════════════════════════════════════════════════════════════╝
"""
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from strings import (
    E, searching_msg, downloading_msg, queued_msg,
    ERR_NO_RESULT, ERR_DOWNLOAD, PAUSE_MSG, RESUME_MSG,
    STOP_MSG, skip_msg, vc_join_msg,
)
from helpers.downloader import download_track, search_tracks
from helpers.keyboards import search_results_kb
from config import MAX_QUEUE_LEN
import database as db

logger = logging.getLogger("vcbot.play")

# Engine + CM injected at runtime by main.py
engine = None


def register(app: Client, _engine):
    global engine
    engine = _engine

    @app.on_message(filters.command("play") & filters.group)
    async def cmd_play(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text(
                f"{E['music']} **Usage:** `/play <song name or YouTube URL>`\n"
                f"Example: `/play Shape of You`"
            )
            return

        query = " ".join(message.command[1:])
        requester = message.from_user.first_name if message.from_user else "Unknown"
        chat_id   = message.chat.id

        # Queue limit
        qlen = await db.db_queue_len(chat_id)
        if qlen >= MAX_QUEUE_LEN:
            await message.reply_text(f"{E['warn']} Queue is full! ({MAX_QUEUE_LEN} tracks max)")
            return

        msg = await message.reply_text(searching_msg(query))

        try:
            await msg.edit_text(downloading_msg(query))
            track = await download_track(query, requester)
        except Exception as e:
            logger.exception("Download failed")
            await msg.edit_text(f"{ERR_DOWNLOAD}\n`{e}`")
            return

        pos = await engine.enqueue(chat_id, track)

        # If nothing playing → start immediately
        np = engine.now_playing(chat_id)
        if np is None:
            # Pop the track we just queued and play it
            next_t = await db.db_pop_next(chat_id)
            if next_t:
                await msg.delete()
                await engine.play(chat_id, next_t)
            else:
                await msg.edit_text(f"{E['cross']} Internal error: could not start playback.")
        else:
            await msg.edit_text(queued_msg(track, pos))

    @app.on_message(filters.command("search") & filters.group)
    async def cmd_search(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text(f"{E['search']} **Usage:** `/search <song name>`")
            return
        query = " ".join(message.command[1:])
        msg = await message.reply_text(f"{E['search']} Searching for **{query}**…")
        results = await search_tracks(query, count=5)
        if not results:
            await msg.edit_text(ERR_NO_RESULT)
            return
        # Store search results in bot memory keyed by chat+user
        from helpers import search_cache
        key = f"{message.chat.id}_{message.from_user.id}"
        search_cache[key] = results
        text = f"{E['search']} **Search Results for** `{query}`\n\nTap to select:"
        await msg.edit_text(text, reply_markup=search_results_kb(results))

    @app.on_message(filters.command(["pause", "p"]) & filters.group)
    async def cmd_pause(client: Client, message: Message):
        chat_id = message.chat.id
        if engine.now_playing(chat_id) is None:
            await message.reply_text(f"{E['cross']} Nothing is playing.")
            return
        ok = await engine.pause(chat_id)
        await message.reply_text(PAUSE_MSG if ok else f"{E['warn']} Could not pause.")

    @app.on_message(filters.command(["resume", "r"]) & filters.group)
    async def cmd_resume(client: Client, message: Message):
        chat_id = message.chat.id
        ok = await engine.resume(chat_id)
        await message.reply_text(RESUME_MSG if ok else f"{E['warn']} Could not resume.")

    @app.on_message(filters.command(["skip", "s", "next"]) & filters.group)
    async def cmd_skip(client: Client, message: Message):
        chat_id = message.chat.id
        t = engine.now_playing(chat_id)
        if t is None:
            await message.reply_text(f"{E['cross']} Nothing is playing.")
            return
        await engine.skip(chat_id)
        next_t = engine.now_playing(chat_id)
        await message.reply_text(skip_msg(t.title, next_t.title if next_t else None))

    @app.on_message(filters.command("stop") & filters.group)
    async def cmd_stop(client: Client, message: Message):
        await engine.stop(message.chat.id)
        await message.reply_text(STOP_MSG)

    @app.on_message(filters.command("replay") & filters.group)
    async def cmd_replay(client: Client, message: Message):
        ok = await engine.replay(message.chat.id)
        if not ok:
            await message.reply_text(f"{E['cross']} Nothing is playing.")

    @app.on_message(filters.command("join") & filters.group)
    async def cmd_join(client: Client, message: Message):
        await engine.cm.start()
        await message.reply_text(vc_join_msg(message.chat.title or str(message.chat.id)))

    @app.on_message(filters.command("leave") & filters.group)
    async def cmd_leave(client: Client, message: Message):
        await engine.stop(message.chat.id)
        from strings import vc_leave_msg
        await message.reply_text(vc_leave_msg())
