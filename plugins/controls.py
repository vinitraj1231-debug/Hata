"""
╔══════════════════════════════════════════════════════════════╗
║   PLUGIN: CONTROLS — /volume /loop /mute /unmute /playlist   ║
╚══════════════════════════════════════════════════════════════╝
"""
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from strings import E, volume_msg, loop_msg, MUTE_MSG, UNMUTE_MSG
from helpers.downloader import fetch_playlist, download_track
from config import MAX_PLAYLIST, MAX_QUEUE_LEN
import database as db

logger = logging.getLogger("vcbot.controls")

engine = None


def register(app: Client, _engine):
    global engine
    engine = _engine

    @app.on_message(filters.command(["volume", "vol"]) & filters.group)
    async def cmd_volume(client: Client, message: Message):
        chat_id = message.chat.id
        if len(message.command) < 2:
            vol = engine.volume(chat_id)
            await message.reply_text(volume_msg(int(vol)))
            return
        try:
            vol = float(message.command[1])
        except ValueError:
            await message.reply_text(f"{E['warn']} Usage: `/volume <0-200>`")
            return
        if not (0 <= vol <= 200):
            from strings import ERR_INVALID_VOL
            await message.reply_text(ERR_INVALID_VOL)
            return
        await engine.set_volume(chat_id, vol)
        await message.reply_text(volume_msg(int(vol)))

    @app.on_message(filters.command("vol+") & filters.group)
    async def cmd_vol_up(client: Client, message: Message):
        chat_id = message.chat.id
        new_vol = min(200, engine.volume(chat_id) + 10)
        await engine.set_volume(chat_id, new_vol)
        await message.reply_text(volume_msg(int(new_vol)))

    @app.on_message(filters.command("vol-") & filters.group)
    async def cmd_vol_down(client: Client, message: Message):
        chat_id = message.chat.id
        new_vol = max(0, engine.volume(chat_id) - 10)
        await engine.set_volume(chat_id, new_vol)
        await message.reply_text(volume_msg(int(new_vol)))

    @app.on_message(filters.command("mute") & filters.group)
    async def cmd_mute(client: Client, message: Message):
        chat_id = message.chat.id
        await engine.set_volume(chat_id, 0)
        await db.set_muted(chat_id, True)
        await message.reply_text(MUTE_MSG)

    @app.on_message(filters.command("unmute") & filters.group)
    async def cmd_unmute(client: Client, message: Message):
        chat_id = message.chat.id
        vol = await db.get_volume(chat_id) or 100
        await engine.set_volume(chat_id, vol)
        await db.set_muted(chat_id, False)
        await message.reply_text(UNMUTE_MSG)

    @app.on_message(filters.command("loop") & filters.group)
    async def cmd_loop(client: Client, message: Message):
        chat_id = message.chat.id
        if len(message.command) < 2:
            mode = await db.get_repeat(chat_id)
            await message.reply_text(loop_msg(mode))
            return
        mode = message.command[1].lower()
        if mode not in ("none", "one", "all"):
            await message.reply_text(f"{E['warn']} Usage: `/loop <none|one|all>`")
            return
        await db.set_repeat(chat_id, mode)
        await message.reply_text(loop_msg(mode))

    @app.on_message(filters.command("playlist") & filters.group)
    async def cmd_playlist(client: Client, message: Message):
        chat_id = message.chat.id
        if len(message.command) < 2:
            await message.reply_text(f"{E['warn']} **Usage:** `/playlist <YouTube playlist URL>`")
            return
        url = message.command[1]
        if "youtube.com/playlist" not in url and "youtu.be" not in url:
            await message.reply_text(f"{E['warn']} Please provide a valid **YouTube playlist URL**.")
            return

        msg = await message.reply_text(f"{E['dl']} Fetching playlist… (max {MAX_PLAYLIST} tracks)")
        entries = await fetch_playlist(url, limit=MAX_PLAYLIST)
        if not entries:
            await msg.edit_text(f"{E['cross']} No tracks found in playlist.")
            return

        requester = message.from_user.first_name if message.from_user else "Unknown"
        added = 0
        qlen  = await db.db_queue_len(chat_id)
        await msg.edit_text(f"{E['dl']} Queuing **{len(entries)}** tracks…")

        for entry in entries:
            if qlen + added >= MAX_QUEUE_LEN:
                break
            try:
                t = await download_track(entry["url"], requester)
                await db.db_enqueue(chat_id, t)
                added += 1
            except Exception:
                pass

        np = engine.now_playing(chat_id)
        if np is None and added > 0:
            next_t = await db.db_pop_next(chat_id)
            if next_t:
                await engine.play(chat_id, next_t)

        await msg.edit_text(
            f"{E['check']} Added **{added}** tracks from playlist to queue!\n"
            f"{E['queue']} Total in queue: `{qlen + added}`"
        )
