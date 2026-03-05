"""
╔════════════════════════════════════════════════════════════╗
║   MUSIC ENGINE — Core queue + playback orchestration       ║
╚════════════════════════════════════════════════════════════╝
"""
import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Optional

from pyrogram import Client

import database as db
from helpers.models import Track
from helpers.call_manager import CallManager
from helpers.downloader import download_track, get_stream_url
from config import IDLE_LEAVE_SEC, CACHE_MAX_FILES, TMP_DIR
from strings import E, progress_bar

logger = logging.getLogger("vcbot.engine")


class MusicEngine:
    """
    Central playback engine for all group voice chats.
    Holds one instance shared across all plugin modules.
    """

    def __init__(self, client: Client, call_manager: CallManager):
        self.client = client
        self.cm = call_manager

        self._now_playing: Dict[int, Optional[Track]] = {}
        self._started_at: Dict[int, float] = {}          # epoch when playback started
        self._play_tasks: Dict[int, asyncio.Task] = {}
        self._idle_tasks: Dict[int, asyncio.Task] = {}
        self._volumes: Dict[int, float] = {}
        self._cache_index: Dict[str, float] = {}

    # ─────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────

    def now_playing(self, chat_id: int) -> Optional[Track]:
        return self._now_playing.get(chat_id)

    def elapsed(self, chat_id: int) -> int:
        ts = self._started_at.get(chat_id)
        return int(time.time() - ts) if ts else 0

    def volume(self, chat_id: int) -> float:
        return self._volumes.get(chat_id, 100.0)

    async def play(self, chat_id: int, track: Track, notify_chat: bool = True):
        """
        Start playing `track` in `chat_id`. Called when queue-popped.
        """
        fp = Path(track.filepath)

        # If file missing — re-download
        if not fp.exists():
            logger.warning("File missing for %s — re-downloading", track.title)
            try:
                rt = await download_track(track.url, track.requested_by)
                track.filepath = rt.filepath
                fp = Path(rt.filepath)
            except Exception:
                logger.exception("Re-download failed for %s", track.title)
                await self._play_next(chat_id)
                return

        # Ensure CM started
        await self.cm.start()

        try:
            await self.cm.join_and_play(chat_id, str(fp))
        except Exception:
            logger.exception("join_and_play failed")
            await self._notify(chat_id, f"{E['cross']} Playback error — skipping…")
            await self._play_next(chat_id)
            return

        # Restore volume
        vol = await db.get_volume(chat_id)
        self._volumes[chat_id] = vol
        await self.cm.set_volume(chat_id, vol)

        # Update state
        self._now_playing[chat_id] = track
        self._started_at[chat_id] = time.time()
        self._cancel_idle(chat_id)
        self._track_cache(str(fp))

        # Log to stats
        await db.log_play(chat_id, track)

        # Schedule end monitor
        self._schedule_monitor(chat_id, track)

        if notify_chat:
            await self._send_np_card(chat_id, track)

    async def enqueue(self, chat_id: int, track: Track):
        """Add track to DB queue. Returns queue position."""
        pos = await db.db_enqueue(chat_id, track)
        return pos

    async def start_if_idle(self, chat_id: int):
        """If nothing is playing, pop next from queue and start."""
        if self._now_playing.get(chat_id) is not None:
            return
        await self._play_next(chat_id)

    async def skip(self, chat_id: int):
        self._cancel_monitor(chat_id)
        await self.cm.leave(chat_id)
        self._now_playing.pop(chat_id, None)
        await self._play_next(chat_id)

    async def stop(self, chat_id: int):
        self._cancel_monitor(chat_id)
        await self.cm.leave(chat_id)
        self._now_playing.pop(chat_id, None)
        await db.db_clear_queue(chat_id)

    async def pause(self, chat_id: int) -> bool:
        return await self.cm.pause(chat_id)

    async def resume(self, chat_id: int) -> bool:
        return await self.cm.resume(chat_id)

    async def set_volume(self, chat_id: int, vol: float) -> bool:
        self._volumes[chat_id] = vol
        await db.set_volume(chat_id, vol)
        return await self.cm.set_volume(chat_id, vol)

    async def replay(self, chat_id: int):
        t = self._now_playing.get(chat_id)
        if not t:
            return False
        self._cancel_monitor(chat_id)
        await self.cm.leave(chat_id)
        self._now_playing.pop(chat_id, None)
        await self.play(chat_id, t)
        return True

    # ─────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────

    async def _play_next(self, chat_id: int):
        repeat = await db.get_repeat(chat_id)
        current = self._now_playing.get(chat_id)

        if repeat == "one" and current:
            await self.play(chat_id, current)
            return

        next_track = await db.db_pop_next(chat_id)

        if not next_track and repeat == "all" and current:
            # Re-enqueue current and continue
            await db.db_enqueue(chat_id, current)
            next_track = await db.db_pop_next(chat_id)

        self._now_playing.pop(chat_id, None)
        self._started_at.pop(chat_id, None)

        if next_track:
            await self.play(chat_id, next_track)
        else:
            # Queue exhausted — schedule idle leave
            self._schedule_idle_leave(chat_id)

    def _schedule_monitor(self, chat_id: int, track: Track):
        self._cancel_monitor(chat_id)
        async def _monitor():
            try:
                wait = max(1, track.duration)
                await asyncio.sleep(wait + 2)
                await self._play_next(chat_id)
            except asyncio.CancelledError:
                pass
        self._play_tasks[chat_id] = asyncio.create_task(_monitor())

    def _cancel_monitor(self, chat_id: int):
        t = self._play_tasks.pop(chat_id, None)
        if t and not t.done():
            t.cancel()

    def _schedule_idle_leave(self, chat_id: int):
        self._cancel_idle(chat_id)
        async def _leave():
            await asyncio.sleep(IDLE_LEAVE_SEC)
            if self._now_playing.get(chat_id) is None:
                await self.cm.leave(chat_id)
                await self._notify(chat_id,
                    f"{E['stop']} Queue empty. Left voice chat after {IDLE_LEAVE_SEC}s idle. 💤")
        self._idle_tasks[chat_id] = asyncio.create_task(_leave())

    def _cancel_idle(self, chat_id: int):
        t = self._idle_tasks.pop(chat_id, None)
        if t and not t.done():
            t.cancel()

    def _track_cache(self, filepath: str):
        self._cache_index[filepath] = time.time()
        self._evict_cache()

    def _evict_cache(self):
        if len(self._cache_index) <= CACHE_MAX_FILES:
            return
        sorted_files = sorted(self._cache_index.items(), key=lambda x: x[1])
        remove = len(self._cache_index) - CACHE_MAX_FILES
        for p, _ in sorted_files[:remove]:
            try:
                Path(p).unlink(missing_ok=True)
                del self._cache_index[p]
                logger.debug("Evicted cache: %s", p)
            except Exception:
                pass

    async def _notify(self, chat_id: int, text: str):
        try:
            await self.client.send_message(chat_id, text)
        except Exception:
            pass

    async def _send_np_card(self, chat_id: int, track: Track):
        from strings import now_playing_msg, progress_bar as pb
        from helpers.keyboards import player_controls_kb
        loop = await db.get_repeat(chat_id)
        vol  = self._volumes.get(chat_id, 100.0)
        bar  = pb(0, track.duration)
        text = now_playing_msg(track, int(vol), loop, bar)
        kb   = player_controls_kb(paused=False, loop=loop)
        try:
            await self.client.send_message(chat_id, text, reply_markup=kb, disable_web_page_preview=True)
        except Exception as e:
            logger.warning("Could not send NP card: %s", e)
