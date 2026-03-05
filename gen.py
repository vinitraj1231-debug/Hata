"""
╔══════════════════════════════════════════╗
║   GEN.PY — Generate Pyrogram String      ║
║            Session for bot assistant     ║
╚══════════════════════════════════════════╝
Run:  python3 gen.py
Copy the printed session string into your .env as STRING_SESSION=...
"""
import asyncio
from pyrogram import Client
from config import API_ID, API_HASH

async def main():
    print("\n🔐  Pyrogram String Session Generator")
    print("━" * 42)
    print("You'll be asked to login with your Telegram account.")
    print("This account will join voice chats as the 'assistant'.\n")
    async with Client(":memory:", api_id=API_ID, api_hash=API_HASH) as app:
        session = await app.export_session_string()
        print("\n✅  Your STRING_SESSION:\n")
        print(session)
        print("\nCopy the above string to your .env file as:")
        print('STRING_SESSION="<paste here>"\n')

if __name__ == "__main__":
    asyncio.run(main())
