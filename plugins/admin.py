"""
╔══════════════════════════════════════════════════════════════╗
║   PLUGIN: ADMIN — auth, ban, broadcast, gban, shutdown       ║
╚══════════════════════════════════════════════════════════════╝
"""
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from config import OWNER_ID, SUDO_USERS
from strings import E, ERR_OWNER_ONLY, ERR_NOT_ADMIN
from helpers.decorators import owner_only, sudo_only, admin_or_auth, resolve_target_user
import database as db

logger = logging.getLogger("vcbot.admin")


def register(app: Client, _engine):

    # ── Auth management ───────────────────────────────────────────────────────
    @app.on_message(filters.command("authusers") & filters.group)
    async def cmd_authusers(client: Client, message: Message):
        auth = await db.get_auth_users(message.chat.id)
        if not auth:
            await message.reply_text(f"{E['info']} No authorised users in this chat.")
            return
        ids_text = "\n".join(f"• `{uid}`" for uid in auth)
        await message.reply_text(f"{E['check']} **Authorised Users:**\n{ids_text}")

    @app.on_message(filters.command("auth") & filters.group)
    async def cmd_auth(client: Client, message: Message):
        uid = message.from_user.id if message.from_user else 0
        if uid not in [OWNER_ID] + SUDO_USERS:
            await message.reply_text(ERR_NOT_ADMIN)
            return
        target_id, name = await resolve_target_user(client, message)
        if not target_id:
            await message.reply_text(f"{E['warn']} Reply to a user or provide user ID.")
            return
        await db.auth_user(message.chat.id, target_id)
        await message.reply_text(f"{E['check']} **{name}** (`{target_id}`) authorised to use bot in this chat.")

    @app.on_message(filters.command("unauth") & filters.group)
    async def cmd_unauth(client: Client, message: Message):
        uid = message.from_user.id if message.from_user else 0
        if uid not in [OWNER_ID] + SUDO_USERS:
            await message.reply_text(ERR_NOT_ADMIN)
            return
        target_id, name = await resolve_target_user(client, message)
        if not target_id:
            await message.reply_text(f"{E['warn']} Reply to a user or provide user ID.")
            return
        await db.unauth_user(message.chat.id, target_id)
        await message.reply_text(f"{E['cross']} **{name}** (`{target_id}`) removed from authorised users.")

    # ── Global ban ────────────────────────────────────────────────────────────
    @app.on_message(filters.command("gban"))
    @sudo_only
    async def cmd_gban(client: Client, message: Message):
        target_id, name = await resolve_target_user(client, message)
        if not target_id:
            await message.reply_text(f"{E['warn']} Reply to a user or provide user ID.")
            return
        reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason"
        await db.gban_user(target_id, reason)
        await message.reply_text(
            f"{E['ban']} **Globally banned:** {name} (`{target_id}`)\n"
            f"{E['note']} Reason: {reason}"
        )

    @app.on_message(filters.command("ungban"))
    @sudo_only
    async def cmd_ungban(client: Client, message: Message):
        target_id, name = await resolve_target_user(client, message)
        if not target_id:
            await message.reply_text(f"{E['warn']} Reply to a user or provide user ID.")
            return
        await db.ungban_user(target_id)
        await message.reply_text(f"{E['check']} **Unbanned:** {name} (`{target_id}`)")

    # ── Broadcast ─────────────────────────────────────────────────────────────
    @app.on_message(filters.command("broadcast"))
    @sudo_only
    async def cmd_broadcast(client: Client, message: Message):
        if len(message.command) < 2 and not message.reply_to_message:
            await message.reply_text(f"{E['warn']} Provide a message or reply to one.")
            return
        text = (
            message.reply_to_message.text
            if message.reply_to_message
            else " ".join(message.command[1:])
        )
        chats = await db.get_all_chats()
        sent, failed = 0, 0
        status_msg = await message.reply_text(f"{E['rocket']} Broadcasting to {len(chats)} chats…")
        for chat_id, _ in chats:
            try:
                await client.send_message(chat_id, text)
                sent += 1
            except Exception:
                failed += 1
        await status_msg.edit_text(
            f"{E['check']} Broadcast complete!\n"
            f"Sent: `{sent}` | Failed: `{failed}`"
        )

    # ── Stats / Logs ──────────────────────────────────────────────────────────
    @app.on_message(filters.command("logs"))
    @sudo_only
    async def cmd_logs(client: Client, message: Message):
        try:
            await client.send_document(
                message.chat.id,
                document="vcbot.log",
                caption=f"{E['note']} Bot log file"
            )
        except Exception:
            await message.reply_text(f"{E['cross']} Log file not found.")

    # ── Shutdown / Restart ────────────────────────────────────────────────────
    @app.on_message(filters.command("shutdown"))
    @owner_only
    async def cmd_shutdown(client: Client, message: Message):
        await message.reply_text(f"{E['stop']} Shutting down… Goodbye! {E['heart']}")
        os._exit(0)

    @app.on_message(filters.command("restart"))
    @owner_only
    async def cmd_restart(client: Client, message: Message):
        await message.reply_text(f"{E['rocket']} Restarting bot…")
        os.execv(__import__("sys").executable, [__import__("sys").executable] + __import__("sys").argv)

    # ── ID helper ─────────────────────────────────────────────────────────────
    @app.on_message(filters.command("id"))
    async def cmd_id(client: Client, message: Message):
        uid  = message.from_user.id if message.from_user else "N/A"
        cid  = message.chat.id
        name = message.from_user.first_name if message.from_user else "N/A"
        text = (
            f"{E['info']} **ID Info**\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👤 **Your ID:** `{uid}`\n"
            f"👤 **Name:** {name}\n"
            f"💬 **Chat ID:** `{cid}`"
        )
        if message.reply_to_message and message.reply_to_message.from_user:
            ru = message.reply_to_message.from_user
            text += f"\n↩️ **Replied User:** {ru.first_name} — `{ru.id}`"
        await message.reply_text(text)
