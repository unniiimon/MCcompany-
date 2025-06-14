# bot.py  (trimmed to essentials)

import asyncio, logging, importlib.util
from pathlib import Path
from aiohttp import web
import pytz
from datetime import datetime, date
from pyrogram import Client, idle

from database.users_chats_db import db
from info import *
from Script import script
from TechVJ.bot import TechVJBot
from TechVJ.bot.clients import initialize_clients
from plugins.clone import restart_bots

# --------------------------------------------------------------------------- #
# 1.  Health‑check HTTP server (aiohttp only)
# --------------------------------------------------------------------------- #

async def health(request):
    return web.Response(text="OK", status=200)

async def build_web_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", health)      # UptimeRobot will hit this
    return app

# --------------------------------------------------------------------------- #
# 2.  Main startup coroutine
# --------------------------------------------------------------------------- #

async def start():
    print("\nInitialising bot…")
    await initialize_clients()

    # dynamic plugin loader
    for file in Path("plugins").glob("*.py"):
        name = file.stem
        spec  = importlib.util.spec_from_file_location(f"plugins.{name}", file)
        mod   = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print(f"Tech VJ Imported => {name}")

    # start Pyrogram
    await TechVJBot.start()

    # keep banned lists up to date
    banned_users, banned_chats = await db.get_banned()
    temp.BANNED_USERS, temp.BANNED_CHATS = banned_users, banned_chats
    me = await TechVJBot.get_me()
    temp.BOT, temp.ME, temp.U_NAME, temp.B_NAME = TechVJBot, me.id, me.username, me.first_name
    logging.info(script.LOGO)

    # notify restart
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz).strftime("%H:%M:%S %p")
    today = date.today()

    try:
        await TechVJBot.send_message(LOG_CHANNEL, script.RESTART_TXT.format(today, now))
    except Exception as e:
        logging.warning("Cannot send restart log: %s", e)

    if CLONE_MODE:
        print("Restarting clone bots…")
        await restart_bots()

    # spin up aiohttp for health probe
    app = await build_web_app()
    runner = web.AppRunner(app)
    await runner.setup()
    bind_port = int(os.getenv("PORT", 8080))
    await web.TCPSite(runner, "0.0.0.0", bind_port).start()

    # block forever
    await idle()

# --------------------------------------------------------------------------- #
# 3.  Entrypoint – single, modern event‑loop
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import uvloop
    uvloop.install()            # 15‑20 % faster I/O, optional
    try:
        asyncio.run(start())    # no deprecated get_event_loop()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped, bye 👋")
