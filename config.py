"""
╔══════════════════════════════════════════╗
║        CONFIGURATION — VCMUSICBOT        ║
╚══════════════════════════════════════════╝
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Core Telegram credentials ───────────────────────────────────────────────
API_ID          = int(os.getenv("API_ID", 0))
API_HASH        = os.getenv("API_HASH", "")
BOT_TOKEN       = os.getenv("BOT_TOKEN", "")          # optional bot for commands
STRING_SESSION  = os.getenv("STRING_SESSION", "")     # Pyrogram string session (assistant)

# ── Owner / Sudo ─────────────────────────────────────────────────────────────
OWNER_ID        = int(os.getenv("OWNER_ID", 0))
SUDO_USERS      = list(map(int, os.getenv("SUDO_USERS", "").split() if os.getenv("SUDO_USERS") else []))

# ── Paths ─────────────────────────────────────────────────────────────────────
TMP_DIR         = Path(os.getenv("TMP_DIR", "./downloads"))
DB_PATH         = Path(os.getenv("DB_PATH", "./vcbot.db"))
TMP_DIR.mkdir(parents=True, exist_ok=True)

# ── Cache / Limits ───────────────────────────────────────────────────────────
CACHE_MAX_FILES = int(os.getenv("CACHE_MAX_FILES", "80"))
MAX_PLAYLIST    = int(os.getenv("MAX_PLAYLIST", "15"))   # max songs per /playlist import
MAX_QUEUE_LEN   = int(os.getenv("MAX_QUEUE_LEN", "500"))
QUEUE_PAGE_SIZE = 10                                      # tracks per queue page

# ── Playback defaults ─────────────────────────────────────────────────────────
DEFAULT_VOLUME  = float(os.getenv("DEFAULT_VOLUME", "100"))   # 0–200
IDLE_LEAVE_SEC  = int(os.getenv("IDLE_LEAVE_SEC", "60"))

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL       = os.getenv("LOG_LEVEL", "INFO").upper()

# ── ytdl options ──────────────────────────────────────────────────────────────
YTDL_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": str(TMP_DIR / "%(id)s.%(ext)s"),
    "quiet": True,
    "no_warnings": True,
    "noplaylist": False,
    "ignoreerrors": True,
    "extract_flat": False,
}

# ── Feature flags ─────────────────────────────────────────────────────────────
ENABLE_LYRICS   = os.getenv("ENABLE_LYRICS", "true").lower() == "true"
ENABLE_SPOTIFY  = os.getenv("ENABLE_SPOTIFY", "false").lower() == "true"
GENIUS_TOKEN    = os.getenv("GENIUS_TOKEN", "")
