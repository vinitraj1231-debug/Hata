"""
╔══════════════════════════════════════════════╗
║   STRINGS — All bot messages (styled)        ║
╚══════════════════════════════════════════════╝
"""

# ── Unicode font helpers ──────────────────────────────────────────────────────
def bold(t):    return f"**{t}**"
def mono(t):    return f"`{t}`"
def code(t):    return f"```{t}```"
def italic(t):  return f"__{t}__"
def strike(t):  return f"~~{t}~~"
def link(text, url): return f"[{text}]({url})"

# ── Decorative separators ─────────────────────────────────────────────────────
LINE        = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
THIN        = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
DOUBLE      = "══════════════════════════════"

# ── Emojis ────────────────────────────────────────────────────────────────────
E = {
    "music":    "🎵",
    "play":     "▶️",
    "pause":    "⏸",
    "skip":     "⏭",
    "stop":     "⏹",
    "loop":     "🔁",
    "shuffle":  "🔀",
    "vol":      "🔊",
    "mute":     "🔇",
    "queue":    "📜",
    "search":   "🔎",
    "dl":       "⬇️",
    "check":    "✅",
    "cross":    "❌",
    "warn":     "⚠️",
    "star":     "⭐",
    "fire":     "🔥",
    "admin":    "👑",
    "ban":      "🚫",
    "clock":    "⏱",
    "link":     "🔗",
    "note":     "📝",
    "chart":    "📊",
    "ping":     "🏓",
    "rocket":   "🚀",
    "mic":      "🎤",
    "heart":    "❤️",
    "vc":       "📻",
    "info":     "ℹ️",
    "lyric":    "📖",
    "next":     "⏩",
    "prev":     "⏮",
    "dot":      "•",
    "arrow":    "➤",
    "new":      "🆕",
    "live":     "🔴",
    "bright":   "✨",
}

# ─────────────────────────────────────────────────────────────────────────────
# START / WELCOME
# ─────────────────────────────────────────────────────────────────────────────
START_MSG = f"""
{E['music']} **𝗩𝗖 𝗠𝘂𝘀𝗶𝗰 𝗕𝗼𝘁** — _Premium Edition_
{LINE}

{E['bright']} Hello **{{name}}**! I am a **high-quality** group voice-chat music streamer.

{E['arrow']} Add me to your **group** and make me **admin**.
{E['arrow']} Use `/play` to start jamming instantly.
{E['arrow']} I'll **auto-join** the voice chat and start streaming!

{LINE}
{E['star']} `/help` — full command list
{E['vc']} Powered by **PyTgCalls** + **yt-dlp**
"""

# ─────────────────────────────────────────────────────────────────────────────
# HELP MENU
# ─────────────────────────────────────────────────────────────────────────────
HELP_MAIN = f"""
{E['music']} **𝗩𝗖 𝗠𝘂𝘀𝗶𝗰 𝗕𝗼𝘁 — 𝗛𝗲𝗹𝗽 𝗠𝗲𝗻𝘂**
{DOUBLE}

{E['arrow']} Choose a category below to see commands:

{E['play']}  **Playback** — play, pause, resume, skip  
{E['queue']} **Queue**    — view, shuffle, clear  
{E['vol']}   **Controls** — volume, speed, loop  
{E['admin']} **Admin**    — restrict, settings  
{E['info']}  **Info**     — now playing, stats, ping  
{E['lyric']} **Extras**   — lyrics, playlist  

{LINE}
_Tap a button to explore commands._
"""

HELP_PLAYBACK = f"""
{E['play']} **𝗣𝗹𝗮𝘆𝗯𝗮𝗰𝗸 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀**
{LINE}

`/play <song / URL>` — Search & stream a song
`/vplay <song / URL>` — Stream video (if supported)
`/pause` — Pause playback
`/resume` — Resume playback  
`/skip` — Skip current track
`/stop` — Stop & leave voice chat
`/seek <seconds>` — Seek to position
`/replay` — Restart current track
`/join` — Join voice chat manually
`/leave` — Leave voice chat

{THIN}
{E['info']} _Supports YouTube, SoundCloud, and direct URLs._
"""

HELP_QUEUE = f"""
{E['queue']} **𝗤𝘂𝗲𝘂𝗲 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀**
{LINE}

`/queue` — Show current queue (paginated)
`/np` — Now playing info
`/shuffle` — Shuffle the queue
`/clear` — Clear entire queue
`/remove <pos>` — Remove track at position
`/move <from> <to>` — Move track in queue
`/playlist <YT playlist URL>` — Import playlist

{THIN}
{E['info']} _Queue supports up to **500** tracks per chat._
"""

HELP_CONTROLS = f"""
{E['vol']} **𝗣𝗹𝗮𝘆𝗯𝗮𝗰𝗸 𝗖𝗼𝗻𝘁𝗿𝗼𝗹𝘀**
{LINE}

`/volume <0-200>` — Set volume
`/vol+` — Increase volume by 10
`/vol-` — Decrease volume by 10
`/mute` — Mute audio
`/unmute` — Unmute audio
`/loop <none|one|all>` — Set repeat mode
`/speed <0.5-2.0>` — Set playback speed

{THIN}
{E['info']} _Default volume: **100**. Max: **200**._
"""

HELP_ADMIN = f"""
{E['admin']} **𝗔𝗱𝗺𝗶𝗻 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀**
{LINE}

`/authusers` — List authorised users
`/auth <reply/id>` — Authorise a user to use bot
`/unauth <reply/id>` — Remove authorised user
`/ban <reply/id>` — Ban user from bot
`/unban <reply/id>` — Unban a user
`/broadcast <msg>` — Broadcast to all chats
`/gban <reply/id>` — Globally ban user
`/shutdown` — Shutdown bot (owner only)
`/restart` — Restart bot (owner only)
`/logs` — Get log file

{THIN}
{E['warn']} _Most admin commands require group admin._
"""

HELP_INFO = f"""
{E['info']} **𝗜𝗻𝗳𝗼 & 𝗦𝘁𝗮𝘁𝘀**
{LINE}

`/np` — Now playing track details
`/ping` — Bot latency
`/stats` — Bot statistics
`/id` — Get user/chat IDs
`/uptime` — Bot uptime

{THIN}
{E['chart']} _Real-time stats updated every session._
"""

HELP_EXTRAS = f"""
{E['lyric']} **𝗘𝘅𝘁𝗿𝗮𝘀 & 𝗙𝘂𝗻**
{LINE}

`/lyrics <song>` — Fetch song lyrics
`/playlist <url>` — Import YouTube playlist
`/search <query>` — Search & choose from results
`/suggest` — Get a music suggestion

{THIN}
{E['bright']} _More features coming soon!_
"""

# ─────────────────────────────────────────────────────────────────────────────
# PLAYBACK MESSAGES
# ─────────────────────────────────────────────────────────────────────────────
def now_playing_msg(track, volume, loop_mode, pos_bar=""):
    dur = _fmt_dur(track.duration)
    return f"""
{E['music']} **𝗡𝗼𝘄 𝗣𝗹𝗮𝘆𝗶𝗻𝗴**
{LINE}

{E['arrow']} **{track.title}**
{E['clock']} Duration : `{dur}`
{E['vol']}  Volume   : `{volume}%`
{E['loop']} Repeat   : `{loop_mode}`
{E['mic']}  By       : {track.requested_by}
{E['link']}  {link('Open on YouTube', track.url)}
{THIN}
{pos_bar}
"""

def queued_msg(track, pos):
    return f"""
{E['check']} **Added to Queue**
{LINE}

{E['arrow']} **{track.title}**
{E['clock']} Duration : `{_fmt_dur(track.duration)}`
{E['queue']} Position : `#{pos}`
{E['mic']}  By       : {track.requested_by}
"""

def searching_msg(query):
    return f"{E['search']} Searching for **{query}** …"

def downloading_msg(query):
    return f"{E['dl']} Downloading **{query}** …"

def skip_msg(title, next_title=None):
    s = f"{E['skip']} Skipped **{title}**"
    if next_title:
        s += f"\n{E['play']} Now playing: **{next_title}**"
    return s

def queue_empty_msg():
    return f"{E['cross']} Queue is empty. Use `/play` to add songs!"

def vc_join_msg(chat_title):
    return f"{E['vc']} Joined voice chat in **{chat_title}**!"

def vc_leave_msg():
    return f"{E['stop']} Left the voice chat. Bye! {E['heart']}"

def vc_started_msg(chat_title):
    return f"""
{E['live']} **Voice Chat Started!**
{THIN}
Chat: **{chat_title}**
{E['music']} Use `/play <song>` to start streaming!
"""

def vc_ended_msg():
    return f"""
{E['stop']} **Voice Chat Ended**
{THIN}
The voice chat was closed.
Start a new one and use `/play` to stream music again!
"""

def volume_msg(vol):
    bar = _make_bar(vol, 200)
    return f"{E['vol']} Volume set to `{vol}%`\n{bar}"

def loop_msg(mode):
    icons = {"none": E["stop"], "one": "🔂", "all": E["loop"]}
    return f"{icons.get(mode, E['loop'])} Repeat mode: **{mode}**"

PAUSE_MSG   = f"{E['pause']} Playback **paused**."
RESUME_MSG  = f"{E['play']}  Playback **resumed**."
STOP_MSG    = f"{E['stop']}  Playback **stopped** and queue cleared."
MUTE_MSG    = f"{E['mute']}  Audio **muted**."
UNMUTE_MSG  = f"{E['vol']}   Audio **unmuted**."

# ─────────────────────────────────────────────────────────────────────────────
# QUEUE
# ─────────────────────────────────────────────────────────────────────────────
def queue_page_msg(tracks, page, total_pages, now_title):
    lines = [f"{E['queue']} **Queue — Page {page}/{total_pages}**", LINE]
    if now_title:
        lines.append(f"{E['play']} **Now:** {now_title}")
        lines.append(THIN)
    for i, t in enumerate(tracks):
        lines.append(f"`{t['pos']:02d}.` {E['dot']} **{t['title']}** ({_fmt_dur(t['duration'])}) — {t['requested_by']}")
    lines.append(LINE)
    lines.append(f"_Page {page} of {total_pages} • Use buttons to navigate_")
    return "\n".join(lines)

# ─────────────────────────────────────────────────────────────────────────────
# ERRORS
# ─────────────────────────────────────────────────────────────────────────────
ERR_NO_VOICE    = f"{E['warn']} **No active voice chat!** Start a voice chat first, then use `/play`."
ERR_NO_PLAY     = f"{E['cross']} Nothing is currently playing."
ERR_NOT_ADMIN   = f"{E['ban']} You must be a **group admin** to use this command."
ERR_OWNER_ONLY  = f"{E['crown'] if 'crown' in E else E['admin']} This command is for the **bot owner** only."
ERR_QUEUE_FULL  = f"{E['warn']} Queue is full! Remove some tracks first."
ERR_DOWNLOAD    = f"{E['cross']} Download failed. Try a different link or search query."
ERR_PLAYBACK    = f"{E['cross']} Playback error. Skipping to next track…"
ERR_NO_RESULT   = f"{E['cross']} No results found. Try a different query."
ERR_INVALID_VOL = f"{E['warn']} Volume must be between **0** and **200**."

# ─────────────────────────────────────────────────────────────────────────────
# STATS / PING
# ─────────────────────────────────────────────────────────────────────────────
def ping_msg(ms):
    return f"{E['ping']} Pong! Latency: `{ms:.2f}ms`"

def stats_msg(d):
    return f"""
{E['chart']} **𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝘀**
{LINE}

{E['vc']}  Active VCs  : `{d['active_vcs']}`
{E['queue']} Queued      : `{d['total_queued']} tracks`
{E['music']} Played today: `{d['played_today']} tracks`
{E['clock']} Uptime      : `{d['uptime']}`
{E['rocket']} Version     : `v2.0 — Astra Edition`
{LINE}
"""

def uptime_msg(uptime_str):
    return f"{E['clock']} Uptime: `{uptime_str}`"

# ─────────────────────────────────────────────────────────────────────────────
# UTIL
# ─────────────────────────────────────────────────────────────────────────────
def _fmt_dur(secs: int) -> str:
    if not secs:
        return "live"
    h, r = divmod(int(secs), 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def _make_bar(val, max_val=100, width=18) -> str:
    pct = max(0, min(val / max_val, 1))
    filled = int(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"`[{bar}]` {int(pct*100)}%"

def progress_bar(elapsed, total, width=18) -> str:
    pct = max(0, min(elapsed / total, 1)) if total else 0
    filled = int(pct * width)
    bar = "▬" * filled + "─" * (width - filled)
    el = _fmt_dur(elapsed)
    tot = _fmt_dur(total)
    return f"`{el}` [{bar}] `{tot}`"
