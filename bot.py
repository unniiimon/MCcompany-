import os
import sys
import glob
import asyncio
import logging
import importlib.util
from pathlib import Path
from aiohttp import web
from pyrogram import Client, idle
from database.users_chats_db import db
from utils import temp
from Script import script

# ✅ Use environment variables securely (no info.py needed)
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPPORT_CHAT = os.environ.get("SUPPORT_CHAT", "YourSupportGroup")
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", 0))
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
PORT = int(os.environ.get("PORT", 8080))  # Render uses dynamic port
APP_NAME = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost")

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Bot client
app = Client(
    "MovieProviderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins={"root": "plugins"},
    workers=100,
    sleep_threshold=10
)

# ✅ Load banned users/chats from DB
async def load_bans():
    logger.info("Loading banned users & chats from DB...")
    b_users, b_chats = await db.get_banned()
    temp.BANNED_USERS = list(set(b_users))
    temp.BANNED_CHATS = list(set(b_chats))
    logger.info(f"Banned users: {len(temp.BANNED_USERS)}, Banned chats: {len(temp.BANNED_CHATS)}")

# ✅ Auto-load plugins from 'plugins' folder
def load_plugins():
    plugin_path = Path(__file__).parent / "plugins"
    for file in glob.glob(f"{plugin_path}/**/*.py", recursive=True):
        module_name = Path(file).stem
        rel_path = Path(file).relative_to(plugin_path.parent)
        spec = importlib.util.spec_from_file_location(str(rel_path), file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    logger.info("All plugins loaded.")

# ✅ Optional keep-alive server for Render (Flask-style aiohttp server)
async def keep_alive():
    async def handler(request):
        return web.Response(text="Bot is Alive!", content_type="text/plain")

    app = web.Application()
    app.router.add_get("/", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Keep-alive server running on port {PORT}")

# ✅ Main function
async def main():
    await load_bans()
    await app.start()
    logger.info(f"{script.BOT_NAME} Started Successfully!")
    await keep_alive()
    await idle()
    await app.stop()
    logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.warning("Bot shutdown requested... Exiting.")
