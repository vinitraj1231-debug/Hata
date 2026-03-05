"""
╔══════════════════════════════════════════════════════════════╗
║   PLUGIN: CALLBACKS — player controls, queue nav, search     ║
╚══════════════════════════════════════════════════════════════╝
"""
import math
import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from strings import (
    E, volume_msg, loop_msg, PAUSE_MSG, RESUME_MSG, skip_msg,
    STOP_MSG, queue_page_msg, now_playing_msg, progress_bar,
)
from helpers.keyboards import player_controls_kb, queue_nav_kb
from config import QUEUE_PAGE_SIZE
import database as db

logger = logging.getLogger("vcbot.callbacks")

engine = None
search_cache = {}   # shared with play.py


def register(app: Client, _engine):
    global engine
    engine = _engine

    # ── Player Control Callbacks ──────────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^ctrl_"))
    async def cb_player(client: Client, cb: CallbackQuery):
        data    = cb.data
        chat_id = cb.message.chat.id

        if data == "ctrl_pause":
            ok = await engine.pause(chat_id)
            await cb.answer(PAUSE_MSG if ok else "Could not pause.", show_alert=False)
            if ok:
                await _refresh_np_keyboard(cb, paused=True)

        elif data == "ctrl_resume":
            ok = await engine.resume(chat_id)
            await cb.answer(RESUME_MSG if ok else "Could not resume.", show_alert=False)
            if ok:
                await _refresh_np_keyboard(cb, paused=False)

        elif data == "ctrl_skip":
            t = engine.now_playing(chat_id)
            if not t:
                await cb.answer("Nothing is playing.", show_alert=True)
                return
            await engine.skip(chat_id)
            await cb.answer(f"{E['skip']} Skipped!", show_alert=False)
            try:
                await cb.message.delete()
            except Exception:
                pass

        elif data == "ctrl_stop":
            await engine.stop(chat_id)
            await cb.answer(f"{E['stop']} Stopped.", show_alert=False)
            try:
                await cb.message.delete()
            except Exception:
                pass

        elif data == "ctrl_replay":
            ok = await engine.replay(chat_id)
            await cb.answer(f"{E['prev']} Replaying!" if ok else "Nothing is playing.")

        elif data == "ctrl_volup":
            new_vol = min(200, engine.volume(chat_id) + 10)
            await engine.set_volume(chat_id, new_vol)
            await cb.answer(f"{E['vol']} Volume: {int(new_vol)}%")

        elif data == "ctrl_voldw":
            new_vol = max(0, engine.volume(chat_id) - 10)
            await engine.set_volume(chat_id, new_vol)
            await cb.answer(f"{E['vol']} Volume: {int(new_vol)}%")

        elif data == "ctrl_loop":
            modes  = ["none", "one", "all"]
            cur    = await db.get_repeat(chat_id)
            new_m  = modes[(modes.index(cur) + 1) % len(modes)]
            await db.set_repeat(chat_id, new_m)
            await cb.answer(loop_msg(new_m), show_alert=False)
            await _refresh_np_keyboard(cb)

        elif data == "ctrl_shuffle":
            await db.db_shuffle_queue(chat_id)
            await cb.answer(f"{E['shuffle']} Queue shuffled!")

        elif data == "ctrl_queue":
            tracks = await db.db_get_queue(chat_id)
            if not tracks:
                await cb.answer("Queue is empty!", show_alert=True)
                return
            total_pages = max(1, math.ceil(len(tracks) / QUEUE_PAGE_SIZE))
            np = engine.now_playing(chat_id)
            text = queue_page_msg(tracks[:QUEUE_PAGE_SIZE], 1, total_pages, np.title if np else None)
            kb   = queue_nav_kb(1, total_pages)
            await cb.message.reply_text(text, reply_markup=kb)
            await cb.answer()

    # ── Queue Pagination ──────────────────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^qpage_\d+$"))
    async def cb_qpage(client: Client, cb: CallbackQuery):
        page    = int(cb.data.split("_")[1])
        chat_id = cb.message.chat.id
        tracks  = await db.db_get_queue(chat_id)
        if not tracks:
            await cb.answer("Queue is now empty!", show_alert=True)
            return
        total_pages = max(1, math.ceil(len(tracks) / QUEUE_PAGE_SIZE))
        page  = max(1, min(page, total_pages))
        start = (page - 1) * QUEUE_PAGE_SIZE
        page_tracks = tracks[start:start + QUEUE_PAGE_SIZE]
        np  = engine.now_playing(chat_id)
        text = queue_page_msg(page_tracks, page, total_pages, np.title if np else None)
        kb   = queue_nav_kb(page, total_pages)
        try:
            await cb.message.edit_text(text, reply_markup=kb)
        except Exception:
            pass
        await cb.answer()

    # ── Search Result Picker ──────────────────────────────────────────────────
    @app.on_callback_query(filters.regex(r"^search_pick_\d+$"))
    async def cb_search_pick(client: Client, cb: CallbackQuery):
        idx = int(cb.data.split("_")[-1])
        key = f"{cb.message.chat.id}_{cb.from_user.id}"
        results = search_cache.get(key)
        if not results or idx >= len(results):
            await cb.answer("Selection expired. Search again.", show_alert=True)
            return

        chosen = results[idx]
        requester = cb.from_user.first_name
        chat_id   = cb.message.chat.id

        await cb.answer(f"{E['dl']} Downloading…", show_alert=False)
        try:
            from helpers.downloader import download_track
            track = await download_track(chosen["url"], requester)
        except Exception as e:
            await cb.message.reply_text(f"{E['cross']} Download failed: {e}")
            return

        pos = await db.db_enqueue(chat_id, track)
        np  = engine.now_playing(chat_id)
        if np is None:
            next_t = await db.db_pop_next(chat_id)
            if next_t:
                await engine.play(chat_id, next_t)
        else:
            from strings import queued_msg
            await cb.message.reply_text(queued_msg(track, pos))

        try:
            await cb.message.delete()
        except Exception:
            pass
        search_cache.pop(key, None)

    @app.on_callback_query(filters.regex("^search_cancel$"))
    async def cb_search_cancel(client: Client, cb: CallbackQuery):
        key = f"{cb.message.chat.id}_{cb.from_user.id}"
        search_cache.pop(key, None)
        await cb.answer("Cancelled.")
        try:
            await cb.message.delete()
        except Exception:
            pass


# ── Internal helpers ──────────────────────────────────────────────────────────
async def _refresh_np_keyboard(cb: CallbackQuery, paused: bool = None):
    chat_id = cb.message.chat.id
    loop    = await db.get_repeat(chat_id)
    is_p    = paused if paused is not None else engine.cm.is_paused(chat_id)
    kb      = player_controls_kb(paused=is_p, loop=loop)
    try:
        await cb.message.edit_reply_markup(kb)
    except Exception:
        pass
