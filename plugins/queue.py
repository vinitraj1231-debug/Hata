"""
╔══════════════════════════════════════════════════════════════╗
║   PLUGIN: QUEUE — /queue /np /shuffle /clear /remove /move   ║
╚══════════════════════════════════════════════════════════════╝
"""
import logging
import math
from pyrogram import Client, filters
from pyrogram.types import Message

from strings import E, queue_empty_msg, queue_page_msg, now_playing_msg, progress_bar
from helpers.keyboards import queue_nav_kb, player_controls_kb
from config import QUEUE_PAGE_SIZE
import database as db

logger = logging.getLogger("vcbot.queue")

engine = None


def register(app: Client, _engine):
    global engine
    engine = _engine

    @app.on_message(filters.command(["queue", "q"]) & filters.group)
    async def cmd_queue(client: Client, message: Message):
        chat_id = message.chat.id
        tracks = await db.db_get_queue(chat_id)
        if not tracks:
            await message.reply_text(queue_empty_msg())
            return
        await _send_queue_page(client, message, tracks, page=1)

    @app.on_message(filters.command(["np", "nowplaying"]) & filters.group)
    async def cmd_np(client: Client, message: Message):
        chat_id = message.chat.id
        t = engine.now_playing(chat_id)
        if not t:
            await message.reply_text(f"{E['cross']} Nothing is currently playing.")
            return
        loop = await db.get_repeat(chat_id)
        vol  = engine.volume(chat_id)
        el   = engine.elapsed(chat_id)
        bar  = progress_bar(el, t.duration)
        text = now_playing_msg(t, int(vol), loop, bar)
        kb   = player_controls_kb(paused=engine.cm.is_paused(chat_id), loop=loop)
        await message.reply_text(text, reply_markup=kb, disable_web_page_preview=True)

    @app.on_message(filters.command("shuffle") & filters.group)
    async def cmd_shuffle(client: Client, message: Message):
        chat_id = message.chat.id
        qlen = await db.db_queue_len(chat_id)
        if qlen == 0:
            await message.reply_text(queue_empty_msg())
            return
        await db.db_shuffle_queue(chat_id)
        await message.reply_text(f"{E['shuffle']} Queue shuffled! ({qlen} tracks)")

    @app.on_message(filters.command("clear") & filters.group)
    async def cmd_clear(client: Client, message: Message):
        chat_id = message.chat.id
        await db.db_clear_queue(chat_id)
        await message.reply_text(f"{E['check']} Queue cleared.")

    @app.on_message(filters.command("remove") & filters.group)
    async def cmd_remove(client: Client, message: Message):
        chat_id = message.chat.id
        if len(message.command) < 2:
            await message.reply_text(f"{E['warn']} **Usage:** `/remove <position>`")
            return
        try:
            pos = int(message.command[1])
        except ValueError:
            await message.reply_text(f"{E['warn']} Position must be a number.")
            return
        ok = await db.db_remove_track(chat_id, pos)
        if ok:
            await message.reply_text(f"{E['check']} Removed track at position **{pos}**.")
        else:
            await message.reply_text(f"{E['cross']} No track at position **{pos}**.")

    @app.on_message(filters.command("move") & filters.group)
    async def cmd_move(client: Client, message: Message):
        chat_id = message.chat.id
        if len(message.command) < 3:
            await message.reply_text(f"{E['warn']} **Usage:** `/move <from> <to>`")
            return
        try:
            frm = int(message.command[1])
            to  = int(message.command[2])
        except ValueError:
            await message.reply_text(f"{E['warn']} Positions must be numbers.")
            return
        ok = await db.db_move_track(chat_id, frm, to)
        if ok:
            await message.reply_text(f"{E['check']} Moved track from position **{frm}** → **{to}**.")
        else:
            await message.reply_text(f"{E['cross']} Invalid positions.")


async def _send_queue_page(client, message, tracks, page: int):
    total_pages = max(1, math.ceil(len(tracks) / QUEUE_PAGE_SIZE))
    page = max(1, min(page, total_pages))
    start = (page - 1) * QUEUE_PAGE_SIZE
    page_tracks = tracks[start:start + QUEUE_PAGE_SIZE]
    chat_id = message.chat.id
    np = engine.now_playing(chat_id)
    np_title = np.title if np else None
    text = queue_page_msg(page_tracks, page, total_pages, np_title)
    kb   = queue_nav_kb(page, total_pages)
    await message.reply_text(text, reply_markup=kb)
