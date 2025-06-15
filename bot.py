#  ──────────────────────────────────────────────────────────────
#  Tech VJ – Telegram Bot main entry‑point
#  Keep credits ♥  @VJ_Botz   @Tech_VJ   @KingVJ01
#  ──────────────────────────────────────────────────────────────
import os, sys, glob, importlib.util, logging.config, asyncio, pytz
from pathlib import Path
from datetime import datetime, date

from pyrogram import idle
from aiohttp import web

# ── Project‑local imports ──────────────────────────────────────
from database.users_chats_db import db
from info      import *              # API_ID, API_HASH, BOT_TOKEN, etc.
from utils     import temp
from Script    import script
from plugins   import web_server
from plugins.clone import restart_bots
from TechVJ.bot          import TechVJBot
from TechVJ.bot.clients  import initialize_clients
from TechVJ.util.keepalive import ping_server  # optional (Heroku)

# ── Optional faster event loop: install uvloop if available ────
try:
    import uvloop
    uvloop.install()
except ModuleNotFoundError:
    pass  # falls back to asyncio’s default loop

# ── Logging config ─────────────────────────────────────────────
logging.config.fileConfig("logging.conf")
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# ── Fresh, explicit event‑loop (avoids deprecation warning) ────
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ── Discover all plugin *.py files once at startup ─────────────
PLUGIN_PATHS = glob.glob("plugins/*.py")

# ╔═════════════════════════════════════════════════════════════╗
# ║                       MAIN STARTUP                          ║
# ╚═════════════════════════════════════════════════════════════╝
async def main() -> None:
    print("\n🔄 Initialising Tech‑VJ Bot …\n")

    # 1️⃣  Initialise any extra Pyrogram clients
    await initialize_clients()

    # 2️⃣  Dynamically load every plugin before the bot goes online
    for file_path in PLUGIN_PATHS:
        name = Path(file_path).stem
        spec = importlib.util.spec_from_file_location(f"plugins.{name}", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[f"plugins.{name}"] = module
        print(f"✅ Plugin loaded: {name}")

    # 3️⃣  Start the primary bot client
    await TechVJBot.start()
    me = await TechVJBot.get_me()
    temp.BOT, temp.ME = TechVJBot, me.id
    temp.U_NAME, temp.B_NAME = me.username, me.first_name

    # 4️⃣  Heroku ping task (ignored on Render/Koyeb)
    if ON_HEROKU:
        asyncio.create_task(ping_server())

    # 5️⃣  Sync banned lists
    temp.BANNED_USERS, temp.BANNED_CHATS = await db.get_banned()

    # 6️⃣  Send restart notifications
    tz      = pytz.timezone("Asia/Kolkata")
    now     = datetime.now(tz).strftime("%H:%M:%S %p")
    today   = date.today()
    restart = script.RESTART_TXT.format(today, now)

    async def safe_send(chat_id, text):
        try:
            m = await TechVJBot.send_message(chat_id, text)
            await m.delete()
        except Exception:
            print(f"⚠️  Couldn’t notify {chat_id} (admin rights?)")

    await safe_send(LOG_CHANNEL, restart)
    for ch in CHANNELS:
        await safe_send(ch, "**Bot Restarted**")
    await safe_send(AUTH_CHANNEL, "**Bot Restarted**")

    # 7️⃣  Restart clone bots if enabled
    if CLONE_MODE:
        print("♻️  Restarting clone bots …")
        await restart_bots()
        print("✅ Clone bots restarted.")

    # 8️⃣  Start a lightweight aiohttp keep‑alive server
    async def alive(_):
        return web.Response(text="I’m alive!", status=200)

    webapp = web.Application(); webapp.add_routes([web.get("/", alive)])
    runner = web.AppRunner(webapp)
    await runner.setup()

    BIND_PORT = int(os.environ.get("PORT", 8080))   # Render sets $PORT
    await web.TCPSite(runner, "0.0.0.0", BIND_PORT).start()

    print(f"🚀 Bot ready! Listening on port {BIND_PORT}")
    await idle()  # blocks here until Ctrl‑C / SIGTERM

# ── Entrypoint ─────────────────────────────────────────────────
# ── Entrypoint ─────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        asyncio.run(main())  # ✅ Use 'main' here
    except KeyboardInterrupt:
        logging.info("❌ Bot Stopped.")
