"""
╔══════════════════════════════════════════╗
║        DECORATORS & FILTERS              ║
╚══════════════════════════════════════════╝
"""
import logging
import functools
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

from config import OWNER_ID, SUDO_USERS
from strings import ERR_NOT_ADMIN, ERR_OWNER_ONLY, E

logger = logging.getLogger("vcbot.decorators")


def owner_only(func):
    """Allow only OWNER_ID."""
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        uid = message.from_user.id if message.from_user else 0
        if uid != OWNER_ID:
            await message.reply_text(ERR_OWNER_ONLY)
            return
        return await func(client, message, *args, **kwargs)
    return wrapper


def sudo_only(func):
    """Allow OWNER_ID + SUDO_USERS."""
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        uid = message.from_user.id if message.from_user else 0
        if uid not in [OWNER_ID] + SUDO_USERS:
            await message.reply_text(ERR_OWNER_ONLY)
            return
        return await func(client, message, *args, **kwargs)
    return wrapper


def admin_or_auth(func):
    """Allow group admins + authorised users + sudo."""
    @functools.wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        uid = message.from_user.id if message.from_user else 0
        if uid in [OWNER_ID] + SUDO_USERS:
            return await func(client, message, *args, **kwargs)

        # Check group admin status
        try:
            member = await client.get_chat_member(message.chat.id, uid)
            if member.status in (
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER,
            ):
                return await func(client, message, *args, **kwargs)
        except Exception:
            pass

        # Check per-chat auth list
        from database import get_auth_users
        auth = await get_auth_users(message.chat.id)
        if uid in auth:
            return await func(client, message, *args, **kwargs)

        await message.reply_text(ERR_NOT_ADMIN)
    return wrapper


async def resolve_target_user(client, message: Message):
    """Return user_id from reply or command argument."""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id, \
               message.reply_to_message.from_user.first_name
    if len(message.command) > 1:
        arg = message.command[1]
        try:
            uid = int(arg)
            return uid, str(uid)
        except ValueError:
            try:
                u = await client.get_users(arg)
                return u.id, u.first_name
            except Exception:
                pass
    return None, None


def fmt_seconds(s: int) -> str:
    h, r = divmod(int(s), 3600)
    m, sec = divmod(r, 60)
    if h:
        return f"{h}h {m}m {sec}s"
    elif m:
        return f"{m}m {sec}s"
    return f"{sec}s"
