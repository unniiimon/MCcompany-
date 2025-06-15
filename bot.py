# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import sys, glob, importlib, logging.config, pytz, asyncio
from pathlib import Path
from pyrogram import Client, idle
from aiohttp import web
from datetime import date, datetime

from database.users_chats_db import db
from info import *
from utils import temp
from Script import script
from plugins import web_server
from plugins.clone import restart_bots
from TechVJ.bot import TechVJBot
from TechVJ.util.keepalive import ping_server
from TechVJ.bot.clients import initialize_clients

# Optional: Comment out if it causes conflict
# from keep_alive import keep_alive
# keep_alive()

# Logging setup
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# Async event loop
loop = asyncio.get_event_loop()
ppath = "plugins/*.py"
files = glob.glob(ppath)

async def start():
    print("\n🔄 Initializing Your Bot...\n")

    # Initialize clients
    await initialize_clients()

    # Load all plugins
    for name in files:
        plugin_name = Path(name).stem
        spec = importlib.util.spec_from_file_location(f"plugins.{plugin_name}", name)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[f"plugins.{plugin_name}"] = module
        print(f"✅ Plugin Loaded: {plugin_name}")

    # Start bot
    await TechVJBot.start()
    bot_info = await TechVJBot.get_me()

    # Store bot info
    temp.BOT = TechVJBot
    temp.ME = bot_info.id
    temp.U_NAME = bot_info.username
    temp.B_NAME = bot_info.first_name

    # Ping server if hosted on Heroku
    if ON_HEROKU:
        asyncio.create_task(ping_server())

    # Load banned users/chats
    temp.BANNED_USERS, temp.BANNED_CHATS = await db.get_banned()

    # Notify log channels
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    today = date.today()
    time = now.strftime("%H:%M:%S %p")

    try:
        await TechVJBot.send_message(LOG_CHANNEL, script.RESTART_TXT.format(today, time))
    except Exception:
        print("⚠️ Make Bot Admin in LOG_CHANNEL")

    for ch in CHANNELS:
        try:
            msg = await TechVJBot.send_message(ch, "**Bot Restarted**")
            await msg.delete()
        except:
            print(f"⚠️ Make Bot Admin in {ch}")

    try:
        msg = await TechVJBot.send_message(AUTH_CHANNEL, "**Bot Restarted**")
        await msg.delete()
    except:
        print("⚠️ Make Bot Admin in AUTH_CHANNEL")

    if CLONE_MODE:
        print("♻️ Restarting All Clone Bots...")
        await restart_bots()
        print("✅ Clone Bots Restarted")

    # Start Web Server
    app = web.AppRunner(await web_server())
    await app.setup()
    await web.TCPSite(app, "0.0.0.0", PORT).start()

    print("🚀 Bot is fully up and running!")
    await idle()

# Entry point
if __name__ == "__main__":
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info("❌ Bot Stopped.")
