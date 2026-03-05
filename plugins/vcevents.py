"""
╔══════════════════════════════════════════════════════════════╗
║  PLUGIN: VC EVENTS — video chat start/end auto-responder     ║
╚══════════════════════════════════════════════════════════════╝
Handles:
  - Video chat started in group → welcome message
  - Video chat ended   in group → farewell message
  - Bot added to group  → register & greet
  - ChatMemberUpdated (new member)
"""
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, ChatMemberUpdated
from pyrogram.enums import ChatMemberStatus

from strings import E, vc_started_msg, vc_ended_msg
from helpers.keyboards import help_main_kb
import database as db

logger = logging.getLogger("vcbot.vcevents")

engine = None


def register(app: Client, _engine):
    global engine
    engine = _engine

    # ── Video Chat Started ────────────────────────────────────────────────────
    @app.on_message(filters.group & filters.video_chat_started)
    async def on_vc_started(client: Client, message: Message):
        chat_title = message.chat.title or str(message.chat.id)
        logger.info("Video chat started in %s (%d)", chat_title, message.chat.id)
        await message.reply_text(
            vc_started_msg(chat_title),
            reply_markup=_quick_play_kb()
        )

    # ── Video Chat Ended ──────────────────────────────────────────────────────
    @app.on_message(filters.group & filters.video_chat_ended)
    async def on_vc_ended(client: Client, message: Message):
        chat_id = message.chat.id
        # Stop playback if active
        if engine.now_playing(chat_id) is not None:
            await engine.stop(chat_id)
        logger.info("Video chat ended in %d", chat_id)
        await message.reply_text(vc_ended_msg())

    # ── Video Chat Participants Invited (optional log) ────────────────────────
    @app.on_message(filters.group & filters.video_chat_members_invited)
    async def on_vc_invite(client: Client, message: Message):
        invited = message.video_chat_members_invited
        if invited:
            names = ", ".join(u.first_name for u in (invited.users or []) if u)
            if names:
                await message.reply_text(
                    f"{E['mic']} **{names}** joined the voice chat! 🎉"
                )

    # ── Bot added to new group ────────────────────────────────────────────────
    @app.on_message(filters.group & filters.new_chat_members)
    async def on_new_member(client: Client, message: Message):
        me = await client.get_me()
        for user in (message.new_chat_members or []):
            if user.id == me.id:
                # Bot was added to this group
                chat_id    = message.chat.id
                chat_title = message.chat.title or str(chat_id)
                logger.info("Bot added to group: %s (%d)", chat_title, chat_id)
                await db.register_chat(chat_id, chat_title)
                await message.reply_text(
                    f"{E['music']} **Thanks for adding me!**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{E['arrow']} Make me **admin** with these permissions:\n"
                    f"  • Manage Video Chats\n"
                    f"  • Send Messages\n"
                    f"\n{E['play']} Use `/play <song>` to start streaming!\n"
                    f"{E['star']} Use `/help` for all commands.",
                    reply_markup=help_main_kb()
                )

    # ── Bot kicked / left (cleanup) ───────────────────────────────────────────
    @app.on_message(filters.group & filters.left_chat_member)
    async def on_left_member(client: Client, message: Message):
        me = await client.get_me()
        if message.left_chat_member and message.left_chat_member.id == me.id:
            chat_id = message.chat.id
            await engine.stop(chat_id)
            await db.db_clear_queue(chat_id)
            logger.info("Bot left group %d — cleaned up", chat_id)


def _quick_play_kb():
    """Inline keyboard for quick actions shown on VC start."""
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"{E['play']} Play a song", switch_inline_query_current_chat="/play "),
        InlineKeyboardButton(f"{E['info']} Help",        callback_data="help_main"),
    ]])
