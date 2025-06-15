# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

from pyrogram import Client
from pyrogram import filters
from info import API_ID, API_HASH, BOT_TOKEN, PLUGIN_PATH, LOGGER
from database.users_chats_db import db
import logging
import asyncio

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
LOGGER = logging.getLogger(__name__)

# Bot Client
Bot = Client(
    "MyBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root=PLUGIN_PATH)
)

# Background startup tasks
async def startup_tasks():
    LOGGER.info("Getting banned users and chats...")
    banned_users, banned_chats = await db.get_banned()
    from utils.temp import BANNED_USERS, BANNED_CHATS
    BANNED_USERS.extend(banned_users)
    BANNED_CHATS.extend(banned_chats)
    LOGGER.info(f"Banned Users Loaded: {len(BANNED_USERS)}")
    LOGGER.info(f"Banned Groups Loaded: {len(BANNED_CHATS)}")

# Run the bot
async def main():
    await startup_tasks()
    await Bot.start()
    LOGGER.info("Bot started successfully.")
    await idle()
    await Bot.stop()
    LOGGER.info("Bot stopped.")

# Entry point
if __name__ == "__main__":
    from pyrogram.idle import idle
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Bot manually stopped.")
