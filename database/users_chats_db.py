#  ──────────────────────────────────────────────────────────────
#  Database helpers  –  Tech VJ  (lazy‑init Mongo, single loop)
#  Keep credits  ♥  @VJ_Botz   @Tech_VJ   @KingVJ01
#  ──────────────────────────────────────────────────────────────

import os, datetime, asyncio, re, time
from typing import Tuple, List
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorClient

from info import (
    DATABASE_NAME, USER_DB_URI, OTHER_DB_URI,
    CUSTOM_FILE_CAPTION, IMDB, IMDB_TEMPLATE, MELCOW_NEW_USERS,
    BUTTON_MODE, SPELL_CHECK_REPLY, PROTECT_CONTENT, AUTO_DELETE,
    MAX_BTN, AUTO_FFILTER, SHORTLINK_API, SHORTLINK_URL,
    SHORTLINK_MODE, TUTORIAL, IS_TUTORIAL,
)

# ── static defaults ────────────────────────────────────────────
default_setgs = {
    "button": BUTTON_MODE,
    "file_secure": PROTECT_CONTENT,
    "imdb": IMDB,
    "spell_check": SPELL_CHECK_REPLY,
    "welcome": MELCOW_NEW_USERS,
    "auto_delete": AUTO_DELETE,
    "auto_ffilter": AUTO_FFILTER,
    "max_btn": MAX_BTN,
    "template": IMDB_TEMPLATE,
    "caption": CUSTOM_FILE_CAPTION,
    "shortlink": SHORTLINK_URL,
    "shortlink_api": SHORTLINK_API,
    "is_shortlink": SHORTLINK_MODE,
    "fsub": None,
    "tutorial": TUTORIAL,
    "is_tutorial": IS_TUTORIAL,
}

# ── simple referal helper (uses *blocking* PyMongo in separate DB) ──
from pymongo import MongoClient
_referal_client = MongoClient(OTHER_DB_URI)
_referal_db     = _referal_client["referal_user"]

async def referal_add_user(user_id: int, ref_user_id: int) -> bool:
    user_db = _referal_db[str(user_id)]
    try:
        user_db.insert_one({"_id": ref_user_id})
        return True
    except DuplicateKeyError:
        return False

async def get_referal_all_users(user_id: int):
    return _referal_db[str(user_id)].find()

async def get_referal_users_count(user_id: int) -> int:
    return _referal_db[str(user_id)].count_documents({})

async def delete_all_referal_users(user_id: int):
    _referal_db[str(user_id)].delete_many({})

# ╔═════════════════════════════════════════════════════════════╗
# ║           MAIN ASYNC DATABASE  (lazy Mongo client)          ║
# ╚═════════════════════════════════════════════════════════════╝

class _LazyDB:
    """Lazy‑initialised MongoDB wrapper that binds to the current loop."""

    def __init__(self, uri: str, db_name: str):
        self._uri        = uri
        self._db_name    = db_name
        self._client     = None
        self._db         = None
        self.col         = None
        self.grp         = None
        self.users       = None
        self.bot         = None

    # ── internal ───────────────────────────────────────────────
    async def _ensure_conn(self):
        if self._client is None:
            # Bind the client to *this* running loop
            self._client = AsyncIOMotorClient(
                self._uri,
                io_loop=asyncio.get_running_loop()
            )
            self._db   = self._client[self._db_name]
            self.col   = self._db.users
            self.grp   = self._db.groups
            self.users = self._db.uersz
            self.bot   = self._db.clone_bots

    # ───────────────────────────────────────────────────────────
    #   ↓↓↓  All public methods call _ensure_conn() first  ↓↓↓
    # ───────────────────────────────────────────────────────────
    def _new_user(self, uid, name):
        return dict(
            id=uid, name=name, file_id=None, caption=None,
            message_command=None, save=False,
            ban_status={"is_banned": False, "ban_reason": ""},
        )

    def _new_group(self, cid, title):
        return dict(
            id=cid, title=title,
            chat_status={"is_disabled": False, "reason": ""},
            settings=default_setgs
        )

    # ── USERS ──────────────────────────────────────────────────
    async def add_user(self, uid: int, name: str):
        await self._ensure_conn()
        await self.col.insert_one(self._new_user(uid, name))

    async def is_user_exist(self, uid: int) -> bool:
        await self._ensure_conn()
        return bool(await self.col.find_one({"id": uid}))

    async def total_users_count(self) -> int:
        await self._ensure_conn()
        return await self.col.count_documents({})

    #  …  (other user‑related functions unchanged)  …

    # ── BANS  (caused the crash) ───────────────────────────────
    async def get_banned(self) -> Tuple[List[int], List[int]]:
        await self._ensure_conn()
        users_cursor = self.col.find({"ban_status.is_banned": True})
        chats_cursor = self.grp.find({"chat_status.is_disabled": True})
        b_users = [doc["id"] async for doc in users_cursor]
        b_chats = [doc["id"] async for doc in chats_cursor]
        return b_users, b_chats

    async def ban_user(self, uid: int, reason="No Reason"):
        await self._ensure_conn()
        await self.col.update_one(
            {"id": uid},
            {"$set": {"ban_status": {"is_banned": True, "ban_reason": reason}}}
        )

    async def remove_ban(self, uid: int):
        await self._ensure_conn()
        await self.col.update_one(
            {"id": uid},
            {"$set": {"ban_status": {"is_banned": False, "ban_reason": ""}}}
        )

    async def get_ban_status(self, uid: int):
        await self._ensure_conn()
        user = await self.col.find_one({"id": uid}) or {}
        return user.get("ban_status", {"is_banned": False, "ban_reason": ""})

    # ── CHATS (only the methods used in plugins/banned.py) ─────
    async def disable_chat(self, cid: int, reason="No Reason"):
        await self._ensure_conn()
        await self.grp.update_one(
            {"id": cid},
            {"$set": {"chat_status": {"is_disabled": True, "reason": reason}}}
        )

    async def get_chat(self, cid: int):
        await self._ensure_conn()
        chat = await self.grp.find_one({"id": cid}) or {}
        return chat.get("chat_status")

# ── export single instance used everywhere ────────────────────
db = _LazyDB(USER_DB_URI, DATABASE_NAME)
