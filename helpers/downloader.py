"""
╔══════════════════════════════════════════╗
║       DOWNLOADER — yt-dlp wrapper        ║
╚══════════════════════════════════════════╝
"""
import asyncio
import uuid
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from yt_dlp import YoutubeDL
from config import YTDL_OPTS, TMP_DIR
from helpers.models import Track

logger = logging.getLogger("vcbot.dl")
POOL = ThreadPoolExecutor(max_workers=4)

# Base opts
_ytdl_opts = dict(YTDL_OPTS)
ytdl = YoutubeDL(_ytdl_opts)

# Flat opts for playlist metadata only
_flat_opts = dict(YTDL_OPTS, extract_flat=True, quiet=True)
ytdl_flat = YoutubeDL(_flat_opts)


def _run_sync(fn, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(POOL, lambda: fn(*args, **kwargs))


async def download_track(query: str, requested_by: str) -> Track:
    """
    Download (or extract) audio for a query/URL.
    Returns Track with local filepath.
    """
    is_url = query.startswith("http://") or query.startswith("https://")
    target = query if is_url else f"ytsearch1:{query}"

    # First pass — metadata only (no download)
    info = await _run_sync(ytdl.extract_info, target, False)
    if not info:
        raise RuntimeError("No results found.")
    if "entries" in info:
        info = info["entries"][0]
    if not info:
        raise RuntimeError("No playable results.")

    # Second pass — actual download
    info = await _run_sync(ytdl.extract_info, target, True)
    if "entries" in info:
        info = info["entries"][0]

    filepath = Path(ytdl.prepare_filename(info)).absolute()
    track_id = info.get("id") or str(uuid.uuid4())
    title    = info.get("title") or "Unknown"
    duration = int(info.get("duration") or 0)
    url      = info.get("webpage_url") or query
    thumb    = info.get("thumbnail") or ""

    return Track(
        id=track_id, title=title, filepath=str(filepath),
        duration=duration, url=url, requested_by=requested_by,
        thumbnail=thumb,
    )


async def fetch_playlist(url: str, limit: int = 15):
    """
    Fetch playlist entries (metadata only, no download).
    Returns list of dicts with title, url, duration.
    """
    info = await _run_sync(ytdl_flat.extract_info, url, False)
    if not info or "entries" not in info:
        return []
    entries = []
    for e in (info["entries"] or [])[:limit]:
        if not e:
            continue
        entries.append({
            "title":    e.get("title") or "Unknown",
            "url":      e.get("url") or e.get("webpage_url") or "",
            "duration": int(e.get("duration") or 0),
        })
    return entries


async def get_stream_url(url: str) -> str:
    """Get direct audio stream URL without downloading."""
    opts = {**_ytdl_opts, "skip_download": True, "quiet": True}
    def _extract():
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if "entries" in info:
                info = info["entries"][0]
            formats = info.get("formats") or []
            for f in reversed(formats):
                if f.get("acodec") != "none" and f.get("url"):
                    return f["url"]
            return info.get("url", "")
    return await _run_sync(_extract)


async def search_tracks(query: str, count: int = 5):
    """Return search results without downloading."""
    target = f"ytsearch{count}:{query}"
    def _search():
        with YoutubeDL({**_ytdl_opts, "quiet": True, "extract_flat": True}) as ydl:
            return ydl.extract_info(target, download=False)
    info = await _run_sync(_search)
    if not info or "entries" not in info:
        return []
    results = []
    for e in (info["entries"] or [])[:count]:
        if not e:
            continue
        results.append({
            "title":    e.get("title") or "Unknown",
            "url":      e.get("url") or e.get("webpage_url") or "",
            "duration": int(e.get("duration") or 0),
            "id":       e.get("id") or "",
        })
    return results
