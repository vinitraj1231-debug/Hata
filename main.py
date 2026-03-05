"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ██╗   ██╗ ██████╗    ███╗   ███╗██╗   ██╗███████╗██╗ ██████╗  ║
║   ██║   ██║██╔════╝    ████╗ ████║██║   ██║██╔════╝██║██╔════╝  ║
║   ██║   ██║██║         ██╔████╔██║██║   ██║███████╗██║██║       ║
║   ╚██╗ ██╔╝██║         ██║╚██╔╝██║██║   ██║╚════██║██║██║       ║
║    ╚████╔╝ ╚██████╗    ██║ ╚═╝ ██║╚██████╔╝███████║██║╚██████╗  ║
║     ╚═══╝   ╚═════╝    ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝ ╚═════╝  ║
║                                                                  ║
║   VC Music Bot — Astra Edition  v2.0                             ║
║   Pyrogram v2 + PyTgCalls · yt-dlp · aiosqlite                   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

from pyrogram import Client, idle

from config import (
    API_ID, API_HASH, STRING_SESSION, BOT_TOKEN,
    LOG_LEVEL, DB_PATH, TMP_DIR,
)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("vcbot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("vcbot.main")

# ── Sanity checks ──────────────────────────────────────────────────────────────
if not API_ID or not API_HASH:
    sys.exit("❌  API_ID / API_HASH missing in .env")
if not STRING_SESSION:
    sys.exit("❌  STRING_SESSION missing in .env — run gen.py to create one")


# ── Pyrogram client (assistant / string session) ───────────────────────────────
assistant = Client(
    name           = "vcbot_assistant",
    api_id         = API_ID,
    api_hash       = API_HASH,
    session_string = STRING_SESSION,
)


async def main():
    # ── Database ───────────────────────────────────────────────────────────────
    from database import init_db
    await init_db()
    logger.info("✅ Database ready at %s", DB_PATH)

    # ── PyTgCalls ─────────────────────────────────────────────────────────────
    try:
        from pytgcalls import PyTgCalls
    except ImportError:
        sys.exit("❌  pytgcalls not installed. Run: pip install pytgcalls")

    raw_pytgcalls = PyTgCalls(assistant)

    # ── Wrappers ───────────────────────────────────────────────────────────────
    from helpers.call_manager import CallManager
    from helpers.engine import MusicEngine

    call_manager = CallManager(raw_pytgcalls)
    engine       = MusicEngine(assistant, call_manager)

    # Shared search cache dict passed to plugins
    import helpers
    helpers.search_cache = {}

    # ── Register plugins ───────────────────────────────────────────────────────
    from plugins import play, queue, controls, admin, help, vcevents, callbacks

    play.register(assistant, engine)
    queue.register(assistant, engine)
    controls.register(assistant, engine)
    admin.register(assistant, None)       # admin doesn't need engine
    help.register(assistant, engine)
    vcevents.register(assistant, engine)
    callbacks.register(assistant, engine)

    # Expose search_cache to play + callbacks
    import plugins.callbacks as cb_mod
    cb_mod.search_cache = helpers.search_cache

    logger.info("✅ All plugins registered")

    # ── Start ──────────────────────────────────────────────────────────────────
    await assistant.start()
    logger.info("✅ Pyrogram assistant started")

    await call_manager.start()
    logger.info("✅ PyTgCalls started")

    # ── Banner ────────────────────────────────────────────────────────────────
    me = await assistant.get_me()
    print(f"""
╔══════════════════════════════════════════╗
║   🎵 VC Music Bot — Astra Edition v2.0   ║
╠══════════════════════════════════════════╣
║  Account : {me.first_name:<30} ║
║  Username: @{(me.username or 'N/A'):<29} ║
║  ID      : {me.id:<30} ║
╠══════════════════════════════════════════╣
║  ✅  Bot is running and ready!           ║
║  📻  Add to group → /play <song>         ║
║  ❓  Help: /help                         ║
╚══════════════════════════════════════════╝
""")

    # ── Keep alive ────────────────────────────────────────────────────────────
    await idle()

    # ── Cleanup ───────────────────────────────────────────────────────────────
    logger.info("Shutting down…")
    await call_manager.stop()
    await assistant.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹  Stopped by user.")
