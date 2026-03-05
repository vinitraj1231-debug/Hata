"""
╔══════════════════════════════════════════════════════════════╗
║  CALL MANAGER — PyTgCalls wrapper (multi-version compat)     ║
╚══════════════════════════════════════════════════════════════╝
"""
import asyncio
import logging
from typing import Any, Optional, Dict
from pathlib import Path

logger = logging.getLogger("vcbot.calls")

# ── Try to import AudioPiped from multiple known paths ───────────────────────
AudioPiped = None
AUDIO_PIPED_AVAILABLE = False

_audio_piped_paths = [
    ("pytgcalls.types.input_stream", "AudioPiped"),
    ("pytgcalls.types",              "AudioPiped"),
    ("pytgcalls",                    "AudioPiped"),
]
for _mod, _cls in _audio_piped_paths:
    try:
        import importlib
        _m = importlib.import_module(_mod)
        AudioPiped = getattr(_m, _cls, None)
        if AudioPiped is not None:
            AUDIO_PIPED_AVAILABLE = True
            logger.info("AudioPiped found at %s.%s", _mod, _cls)
            break
    except Exception:
        pass

if not AUDIO_PIPED_AVAILABLE:
    logger.warning("AudioPiped not found — will use file-path fallback.")


# ── Join call compatibility shim ─────────────────────────────────────────────
_JOIN_CANDIDATES = [
    ("join_group_call",  ("chat_id", "source")),
    ("join_call",        ("chat_id", "source")),
    ("start_group_call", ("chat_id", "source")),
    ("join",             ("chat_id", "source")),
    ("play",             ("chat_id", "source")),
    # reversed-arg versions (some older builds)
    ("join_group_call",  ("source", "chat_id")),
    ("join",             ("source", "chat_id")),
    ("play",             ("source", "chat_id")),
    ("start",            ("chat_id", "source")),
]

_LEAVE_CANDIDATES = ["leave_group_call", "leave_call", "leave", "end_call", "stop_call"]
_PAUSE_CANDIDATES = ["pause_stream", "pause", "pause_call"]
_RESUME_CANDIDATES = ["resume_stream", "resume", "resume_call"]
_CHANGE_VOLUME_CANDIDATES = ["change_volume_call", "set_volume", "volume"]


async def _try_candidates(obj: Any, candidates, *args) -> bool:
    """Try a list of method names with given args; return True if one succeeds."""
    for name in candidates:
        fn = getattr(obj, name, None)
        if not callable(fn):
            continue
        try:
            res = fn(*args)
            if asyncio.iscoroutine(res):
                await res
            return True
        except TypeError:
            continue
        except Exception:
            logger.exception("Method %s raised", name)
            raise
    return False


# ═══════════════════════════════════════════════════════════════════
# CALL MANAGER
# ═══════════════════════════════════════════════════════════════════
class CallManager:
    """
    Wraps PyTgCalls to provide a stable API regardless of installed version.
    Holds per-chat playback state (volume, paused, current source).
    """

    def __init__(self, pytgcalls_obj: Any):
        self.vc: Any = pytgcalls_obj
        self._started = False
        self._paused: Dict[int, bool] = {}
        self._volumes: Dict[int, float] = {}

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    async def start(self):
        if self._started:
            return
        try:
            res = self.vc.start()
            if asyncio.iscoroutine(res):
                await res
            self._started = True
            logger.info("PyTgCalls started.")
        except Exception as e:
            logger.warning("PyTgCalls.start() raised: %s (ignoring)", e)
            self._started = True  # assume already started

    async def stop(self):
        try:
            res = self.vc.stop()
            if asyncio.iscoroutine(res):
                await res
        except Exception:
            pass

    # ── Join / Play ───────────────────────────────────────────────────────────
    async def join_and_play(self, chat_id: int, filepath: str) -> None:
        """
        Join the voice chat and begin streaming `filepath`.
        Tries AudioPiped first, falls back to raw file path.
        """
        source = None
        if AUDIO_PIPED_AVAILABLE and AudioPiped is not None:
            try:
                source = AudioPiped(filepath)
            except Exception as e:
                logger.warning("AudioPiped(%s) failed: %s", filepath, e)

        if source is None:
            source = filepath   # raw path fallback

        last_exc = None
        for name, order in _JOIN_CANDIDATES:
            fn = getattr(self.vc, name, None)
            if not callable(fn):
                continue
            try:
                if order == ("chat_id", "source"):
                    res = fn(chat_id, source)
                else:
                    res = fn(source, chat_id)
                if asyncio.iscoroutine(res):
                    await res
                logger.info("Joined VC in %d via %s", chat_id, name)
                self._paused[chat_id] = False
                return
            except TypeError as e:
                last_exc = e
                continue
            except Exception as e:
                logger.exception("join_and_play failed with %s", name)
                raise RuntimeError(f"Playback failed: {e}") from e

        raise RuntimeError(
            f"No compatible join/play method found on PyTgCalls. Last err: {last_exc}"
        )

    # ── Leave ─────────────────────────────────────────────────────────────────
    async def leave(self, chat_id: int) -> bool:
        ok = await _try_candidates(self.vc, _LEAVE_CANDIDATES, chat_id)
        self._paused.pop(chat_id, None)
        self._volumes.pop(chat_id, None)
        return ok

    # ── Pause / Resume ────────────────────────────────────────────────────────
    async def pause(self, chat_id: int) -> bool:
        ok = await _try_candidates(self.vc, _PAUSE_CANDIDATES, chat_id)
        if ok:
            self._paused[chat_id] = True
        return ok

    async def resume(self, chat_id: int) -> bool:
        ok = await _try_candidates(self.vc, _RESUME_CANDIDATES, chat_id)
        if ok:
            self._paused[chat_id] = False
        return ok

    def is_paused(self, chat_id: int) -> bool:
        return self._paused.get(chat_id, False)

    # ── Volume ────────────────────────────────────────────────────────────────
    async def set_volume(self, chat_id: int, volume: float) -> bool:
        vol_int = int(volume)
        ok = await _try_candidates(self.vc, _CHANGE_VOLUME_CANDIDATES, chat_id, vol_int)
        if ok:
            self._volumes[chat_id] = volume
        return ok

    def get_volume(self, chat_id: int) -> float:
        return self._volumes.get(chat_id, 100.0)

    # ── Status ────────────────────────────────────────────────────────────────
    def is_active(self, chat_id: int) -> bool:
        """Check if we have an active call in this chat."""
        try:
            active = getattr(self.vc, "active_calls", None)
            if active is not None:
                return chat_id in active
        except Exception:
            pass
        return chat_id in self._paused   # best-effort via our own tracking
