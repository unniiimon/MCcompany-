# Don't Remove Credit  @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot  @Tech_VJ
# Ask Doubt on telegram @KingVJ01

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from utils import temp
from database.users_chats_db import db
from info import SUPPORT_CHAT

# ── custom filters ────────────────────────────────────────────
async def _is_banned_user(_, __, msg: Message):
    return (
        msg.from_user                       # user exists
        and msg.from_user.id in temp.BANNED_USERS
    )

async def _is_disabled_chat(_, __, msg: Message):
    return msg.chat.id in temp.BANNED_CHATS

banned_user   = filters.create(_is_banned_user)
disabled_chat = filters.create(_is_disabled_chat)

# ── handlers ──────────────────────────────────────────────────
@Client.on_message(filters.private & banned_user & filters.incoming)
async def ban_reply(_, msg: Message):
    ban = await db.get_ban_status(msg.from_user.id)
    await msg.reply_text(
        f"🚫 Sorry, you are banned.\nReason: <code>{ban['ban_reason']}</code>"
    )

@Client.on_message(filters.group & disabled_chat & filters.incoming)
async def grp_bd(bot: Client, msg: Message):
    buttons = [[InlineKeyboardButton("Support", url=f"https://t.me/{SUPPORT_CHAT}")]]
    chat_info = await db.get_chat(msg.chat.id) or {"reason": "No data"}
    txt = (
        "CHAT NOT ALLOWED 🐞\n\n"
        "My admins have restricted me from working here!\n"
        f"Reason: <code>{chat_info['reason']}</code>"
    )
    out = await msg.reply_text(txt, reply_markup=InlineKeyboardMarkup(buttons))
    try:
        await out.pin()
    except Exception:
        pass
    await bot.leave_chat(msg.chat.id)
