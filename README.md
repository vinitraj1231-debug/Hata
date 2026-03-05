# 🎵 VC Music Bot — Astra Edition v2.0

> **Advanced Telegram Voice Chat Music Streamer**  
> Built with **Pyrogram v2** · **PyTgCalls** · **yt-dlp** · **aiosqlite**

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎵 **Stream Music** | YouTube, SoundCloud, direct URLs |
| 📜 **Queue System** | Persistent SQLite queue, up to 500 tracks |
| 🔀 **Shuffle / Move** | Full queue management |
| 🔁 **Loop Modes** | `none` · `one` · `all` |
| 🔊 **Volume Control** | 0–200%, inline buttons |
| 📺 **VC Auto-Response** | Greets on voice chat start/end |
| 🤖 **Auto-Join** | Auto joins VC when /play is used |
| 🔎 **Search & Pick** | Interactive search results |
| 📖 **Lyrics** | Via Genius API |
| 🎶 **Playlist Import** | YouTube playlists (up to 15 tracks) |
| 👑 **Admin System** | Auth users, global bans, broadcast |
| 📊 **Stats & Ping** | Live bot statistics |
| 💾 **Cache Management** | Auto-evicts old downloads |
| ⌨️ **Inline Controls** | Pause/Resume/Skip/Loop buttons on NP card |

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourname/vcmusicbot
cd vcmusicbot
pip install -r requirements.txt
```

### 2. Get Credentials

- **API_ID / API_HASH** → https://my.telegram.org/apps  
- **String Session** → Run `python3 gen.py` (login with the *assistant* account)
- **OWNER_ID** → Your Telegram user ID (use @userinfobot)

### 3. Configure `.env`

```bash
cp .env.example .env
nano .env          # fill in API_ID, API_HASH, STRING_SESSION, OWNER_ID
```

### 4. Run

```bash
python3 main.py
```

---

## 📋 Commands

### 🎵 Playback
| Command | Description |
|---|---|
| `/play <song/URL>` | Search & stream a track |
| `/pause` | Pause playback |
| `/resume` | Resume playback |
| `/skip` | Skip current track |
| `/stop` | Stop & clear queue |
| `/replay` | Restart current track |
| `/join` | Join voice chat |
| `/leave` | Leave voice chat |

### 📜 Queue
| Command | Description |
|---|---|
| `/queue` | View queue (paginated) |
| `/np` | Now playing info + controls |
| `/shuffle` | Shuffle queue |
| `/clear` | Clear queue |
| `/remove <pos>` | Remove a track |
| `/move <from> <to>` | Reorder queue |
| `/playlist <url>` | Import YouTube playlist |

### 🔊 Controls
| Command | Description |
|---|---|
| `/volume <0-200>` | Set volume |
| `/vol+` · `/vol-` | Adjust volume ±10 |
| `/mute` · `/unmute` | Mute/unmute |
| `/loop <none|one|all>` | Set repeat mode |

### 👑 Admin (owner / sudo)
| Command | Description |
|---|---|
| `/auth <reply/id>` | Authorise user |
| `/unauth <reply/id>` | Remove auth |
| `/gban <reply/id>` | Global ban |
| `/ungban <reply/id>` | Unban globally |
| `/broadcast <msg>` | Message all chats |
| `/logs` | Get log file |
| `/shutdown` | Stop bot |
| `/restart` | Restart bot |

### ℹ️ Info
| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/help` | Help menu |
| `/ping` | Latency check |
| `/stats` | Bot statistics |
| `/uptime` | Bot uptime |
| `/id` | Get user/chat IDs |
| `/lyrics <song>` | Fetch song lyrics |
| `/search <query>` | Interactive search |

---

## 🏗️ Project Structure

```
vcmusicbot/
├── main.py                  # Entry point
├── config.py                # All settings (loaded from .env)
├── database.py              # aiosqlite DB layer
├── strings.py               # All bot messages (styled with emoji)
├── gen.py                   # String session generator
├── requirements.txt
├── .env.example
├── helpers/
│   ├── __init__.py
│   ├── models.py            # Track dataclass
│   ├── downloader.py        # yt-dlp async wrapper
│   ├── call_manager.py      # PyTgCalls compat shim
│   ├── engine.py            # Core music engine
│   ├── decorators.py        # Auth decorators
│   └── keyboards.py         # InlineKeyboardMarkup builders
└── plugins/
    ├── __init__.py
    ├── play.py              # /play /pause /resume /skip /stop
    ├── queue.py             # /queue /np /shuffle /clear /remove
    ├── controls.py          # /volume /loop /mute /playlist
    ├── admin.py             # /auth /gban /broadcast /shutdown
    ├── help.py              # /start /help /ping /stats /lyrics
    ├── vcevents.py          # Video chat start/end handlers
    └── callbacks.py         # InlineKeyboard callback handlers
```

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `API_ID` | ✅ | — | Telegram API ID |
| `API_HASH` | ✅ | — | Telegram API Hash |
| `STRING_SESSION` | ✅ | — | Pyrogram string session |
| `OWNER_ID` | ✅ | — | Your Telegram user ID |
| `SUDO_USERS` | ❌ | — | Space-separated sudo IDs |
| `GENIUS_TOKEN` | ❌ | — | Genius API token for lyrics |
| `CACHE_MAX_FILES` | ❌ | 80 | Max cached audio files |
| `MAX_PLAYLIST` | ❌ | 15 | Max tracks per playlist import |
| `MAX_QUEUE_LEN` | ❌ | 500 | Max queue length per chat |
| `IDLE_LEAVE_SEC` | ❌ | 60 | Leave after N seconds idle |
| `DEFAULT_VOLUME` | ❌ | 100 | Default volume (0–200) |
| `ENABLE_LYRICS` | ❌ | true | Enable /lyrics command |
| `LOG_LEVEL` | ❌ | INFO | Logging level |

---

## 🛠️ Requirements

- Python **3.10+**
- **ffmpeg** installed (`apt install ffmpeg` / `brew install ffmpeg`)
- A Telegram account for the **assistant** (separate from your main)
- The assistant account must be in the group and have *"Manage Video Chats"* permission

---

## 📝 Notes

- The assistant (string session) **auto-joins the VC** when `/play` is used — no manual `/join` needed.  
- PyTgCalls compatibility layer supports versions **0.9.x – 3.x** automatically.  
- Downloads are cached and auto-evicted when `CACHE_MAX_FILES` is exceeded.

---

## 📄 License

MIT — free for personal and commercial use.
