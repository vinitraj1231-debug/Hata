"""
╔══════════════════════════════════════════╗
║      KEYBOARDS — InlineKeyboardMarkup    ║
╚══════════════════════════════════════════╝
"""
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from strings import E


def player_controls_kb(paused: bool = False, loop: str = "none") -> InlineKeyboardMarkup:
    loop_icons = {"none": f"{E['stop']} Off", "one": "🔂 One", "all": f"{E['loop']} All"}
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{E['prev']} Replay",  callback_data="ctrl_replay"),
            InlineKeyboardButton(f"{E['pause']} Pause" if not paused else f"{E['play']} Resume",
                                 callback_data="ctrl_pause" if not paused else "ctrl_resume"),
            InlineKeyboardButton(f"{E['skip']} Skip",    callback_data="ctrl_skip"),
        ],
        [
            InlineKeyboardButton(f"{E['vol']} Vol–",     callback_data="ctrl_voldw"),
            InlineKeyboardButton(f"{E['stop']} Stop",    callback_data="ctrl_stop"),
            InlineKeyboardButton(f"{E['vol']} Vol+",     callback_data="ctrl_volup"),
        ],
        [
            InlineKeyboardButton(f"{loop_icons[loop]}",  callback_data="ctrl_loop"),
            InlineKeyboardButton(f"{E['queue']} Queue",  callback_data="ctrl_queue"),
            InlineKeyboardButton(f"{E['shuffle']} Shuffle", callback_data="ctrl_shuffle"),
        ],
    ])


def help_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{E['play']} Playback",  callback_data="help_playback"),
            InlineKeyboardButton(f"{E['queue']} Queue",    callback_data="help_queue"),
        ],
        [
            InlineKeyboardButton(f"{E['vol']} Controls",   callback_data="help_controls"),
            InlineKeyboardButton(f"{E['admin']} Admin",    callback_data="help_admin"),
        ],
        [
            InlineKeyboardButton(f"{E['info']} Info",      callback_data="help_info"),
            InlineKeyboardButton(f"{E['lyric']} Extras",   callback_data="help_extras"),
        ],
    ])


def back_kb(data: str = "help_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"◀️ Back", callback_data=data)
    ]])


def queue_nav_kb(page: int, total_pages: int) -> InlineKeyboardMarkup:
    btns = []
    if page > 1:
        btns.append(InlineKeyboardButton("◀️ Prev", callback_data=f"qpage_{page - 1}"))
    btns.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        btns.append(InlineKeyboardButton("Next ▶️", callback_data=f"qpage_{page + 1}"))
    return InlineKeyboardMarkup([btns])


def search_results_kb(results: list) -> InlineKeyboardMarkup:
    rows = []
    for i, r in enumerate(results[:5]):
        title = r["title"][:38] + "…" if len(r["title"]) > 38 else r["title"]
        rows.append([InlineKeyboardButton(
            f"{i + 1}. {title}",
            callback_data=f"search_pick_{i}"
        )])
    rows.append([InlineKeyboardButton(f"{E['cross']} Cancel", callback_data="search_cancel")])
    return InlineKeyboardMarkup(rows)


def confirm_kb(yes_data: str, no_data: str = "confirm_no") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"{E['check']} Yes", callback_data=yes_data),
        InlineKeyboardButton(f"{E['cross']} No",  callback_data=no_data),
    ]])


def close_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"{E['cross']} Close", callback_data="close_msg")
    ]])
