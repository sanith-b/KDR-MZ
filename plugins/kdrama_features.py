"""
My K-Drama 2.0 - User Features Plugin
Commands & Interactive Keyboards for:
  - /profile: Comprehensive user statistics, tier, points, referral link
  - /watchlist & inline [➕ Watchlist]: Personal drama watchlist management
  - /favorites & inline [⭐ Favorite]: Fast favorites library
  - /progress & inline [✅ Watched]: Episode viewing progress tracking
  - /recent: 1-tap replay of recently searched dramas
  - /notifications: In-app release alerts & request updates
  - FloodWait handling & user command rate limiting
"""
import time
import asyncio
from typing import Dict, Any, List, Optional
from pyrogram import Client, filters, enums
from pyrogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from pyrogram.errors import FloodWait, MessageNotModified, UserIsBlocked
from shared.database.repositories.users_repo import (
    users_repo, watchlists_repo, favorites_repo, watch_progress_repo
)
from shared.database.repositories.interactions_repo import (
    search_history_repo, notifications_repo
)
from shared.database.repositories.dramas_repo import dramas_repo
from shared.database.repositories.requests_repo import drama_requests_repo, request_votes_repo
from shared.services.tmdb import tmdb
from bot.kdrama_engine import kdrama_engine, check_user_rate_limit
from info import *
from logging_helper import LOGGER


async def safe_send_message(client: Client, chat_id: int, text: str, reply_markup=None) -> Optional[Message]:
    """Sends message with exponential backoff for Telegram FloodWait errors"""
    retries = 3
    for attempt in range(retries):
        try:
            return await client.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
        except FloodWait as e:
            LOGGER.warning(f"FloodWait encountered: sleeping {e.value}s")
            await asyncio.sleep(e.value + 1)
        except Exception as e:
            LOGGER.error(f"Error sending message to {chat_id}: {e}")
            break
    return None


# ===========================================================================
# 1. USER PROFILE COMMAND (/profile)
# ===========================================================================
@Client.on_message(filters.command(["profile", "myinfo"]) & filters.private)
async def user_profile_handler(client: Client, message: Message):
    if not check_user_rate_limit(message.from_user.id):
        return await message.reply_text("⚠️ You're sending commands too fast. Please slow down.")

    user_id = message.from_user.id
    user_doc = await users_repo.get_by_telegram_id(user_id)
    if not user_doc:
        user_doc = await users_repo.upsert_telegram_user(
            telegram_id=user_id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            username=message.from_user.username
        )

    # Gather library counts
    wl_count = await watchlists_repo.count({"user_id": str(user_id)})
    fav_count = await favorites_repo.count({"user_id": str(user_id)})
    prog_count = await watch_progress_repo.count({"user_id": str(user_id)})
    points = user_doc.get("points") or user_doc.get("referral_points", 0)
    role = user_doc.get("role", "user").capitalize()
    is_premium = user_doc.get("is_premium", False)

    bot_me = await client.get_me()
    referral_link = f"https://t.me/{bot_me.username}?start=refer_{user_id}"

    profile_text = (
        f"👤 <b>My K-Drama Profile</b>\n\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"🏷️ <b>Name:</b> {message.from_user.first_name}\n"
        f"👑 <b>Tier:</b> {'💎 VIP Premium' if is_premium else 'Free Member'} ({role})\n"
        f"⭐️ <b>Activity Points:</b> <code>{points}</code>\n\n"
        f"📚 <b>My Library:</b>\n"
        f"• 📋 Watchlist: <b>{wl_count}</b> dramas\n"
        f"• ⭐ Favorites: <b>{fav_count}</b> dramas\n"
        f"• 🎬 In Progress: <b>{prog_count}</b> episodes\n\n"
        f"🔗 <b>Your Referral Link:</b>\n"
        f"<code>{referral_link}</code>\n"
        f"<i>(Share to earn points and free VIP access!)</i>"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 Watchlist", callback_data="my_watchlist"),
            InlineKeyboardButton("⭐ Favorites", callback_data="my_favorites")
        ],
        [
            InlineKeyboardButton("🎬 Progress", callback_data="my_progress"),
            InlineKeyboardButton("🔔 Notifications", callback_data="my_notifications")
        ],
        [
            InlineKeyboardButton("💎 Upgrade VIP", callback_data="see_plans")
        ]
    ])

    await message.reply_text(profile_text, reply_markup=keyboard)


# ===========================================================================
# 2. WATCHLIST COMMAND & CALLBACKS (/watchlist)
# ===========================================================================
@Client.on_message(filters.command(["watchlist", "wl"]))
async def watchlist_handler(client: Client, message: Message):
    user_id = message.from_user.id
    res = await watchlists_repo.find_many({"user_id": str(user_id)})
    if not res.items:
        return await message.reply_text(
            "📋 <b>Your Watchlist is empty!</b>\n\n"
            "Search for any K-Drama and tap <b>[➕ Add to Watchlist]</b> to save it here."
        )

    text = "📋 <b>Your K-Drama Watchlist:</b>\n\n"
    buttons = []
    for item in res.items[:15]:
        d_id = item.get("drama_id")
        drama = await dramas_repo.get_by_slug_or_id(d_id)
        title = drama.get("title", d_id) if drama else d_id
        text += f"• <b>{title}</b> (<i>{item.get('status', 'plan_to_watch')}</i>)\n"
        buttons.append([
            InlineKeyboardButton(f"🔍 {title[:20]}", switch_inline_query_current_chat=title),
            InlineKeyboardButton("🗑️ Remove", callback_data=f"wl_del#{d_id}")
        ])

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex(r"^wl_add#"))
async def add_watchlist_callback(client: Client, query: CallbackQuery):
    _, drama_id = query.data.split("#", 1)
    user_id = query.from_user.id
    await watchlists_repo.update_one(
        {"user_id": str(user_id), "drama_id": drama_id},
        {"$set": {"user_id": str(user_id), "drama_id": drama_id, "status": "plan_to_watch"}},
        upsert=True
    )
    await query.answer("✅ Added to your Watchlist!", show_alert=True)


@Client.on_callback_query(filters.regex(r"^wl_del#"))
async def del_watchlist_callback(client: Client, query: CallbackQuery):
    _, drama_id = query.data.split("#", 1)
    user_id = query.from_user.id
    await watchlists_repo.collection.delete_one({"user_id": str(user_id), "drama_id": drama_id})
    await query.answer("🗑️ Removed from Watchlist!", show_alert=False)
    await query.message.edit_text("✅ Watchlist updated.")


# ===========================================================================
# 3. FAVORITES COMMAND & CALLBACKS (/favorites)
# ===========================================================================
@Client.on_message(filters.command(["favorites", "favs"]))
async def favorites_handler(client: Client, message: Message):
    user_id = message.from_user.id
    res = await favorites_repo.find_many({"user_id": str(user_id)})
    if not res.items:
        return await message.reply_text(
            "⭐ <b>You don't have any favorites yet!</b>\n\n"
            "Search for your all-time favorite K-Dramas and tap <b>[⭐ Favorite]</b>."
        )

    text = "⭐ <b>Your Favorite K-Dramas:</b>\n\n"
    buttons = []
    for item in res.items[:15]:
        d_id = item.get("drama_id")
        drama = await dramas_repo.get_by_slug_or_id(d_id)
        title = drama.get("title", d_id) if drama else d_id
        text += f"• ⭐️ <b>{title}</b>\n"
        buttons.append([
            InlineKeyboardButton(f"🎬 {title[:20]}", switch_inline_query_current_chat=title),
            InlineKeyboardButton("❌ Unfav", callback_data=f"fav_del#{d_id}")
        ])

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex(r"^fav_add#"))
async def add_favorite_callback(client: Client, query: CallbackQuery):
    _, drama_id = query.data.split("#", 1)
    user_id = query.from_user.id
    await favorites_repo.update_one(
        {"user_id": str(user_id), "drama_id": drama_id},
        {"$set": {"user_id": str(user_id), "drama_id": drama_id}},
        upsert=True
    )
    await query.answer("⭐ Added to Favorites!", show_alert=True)


@Client.on_callback_query(filters.regex(r"^fav_del#"))
async def del_favorite_callback(client: Client, query: CallbackQuery):
    _, drama_id = query.data.split("#", 1)
    user_id = query.from_user.id
    await favorites_repo.collection.delete_one({"user_id": str(user_id), "drama_id": drama_id})
    await query.answer("❌ Removed from Favorites!")
    await query.message.edit_text("✅ Favorites updated.")


# ===========================================================================
# 4. RECENT SEARCHES COMMAND (/recent)
# ===========================================================================
@Client.on_message(filters.command(["recent", "history"]))
async def recent_searches_handler(client: Client, message: Message):
    user_id = message.from_user.id
    recent = await search_history_repo.get_user_history(str(user_id), limit=8)
    if not recent:
        return await message.reply_text("🕒 <b>No recent searches found.</b>")

    text = "🕒 <b>Your Recently Searched K-Dramas:</b>\n<i>Tap any button to search again!</i>\n"
    buttons = []
    for entry in recent:
        q = entry.get("query")
        if q:
            buttons.append([InlineKeyboardButton(f"🔍 {q}", switch_inline_query_current_chat=q)])

    buttons.append([InlineKeyboardButton("🗑️ Clear History", callback_data="clear_my_history")])
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex(r"^clear_my_history$"))
async def clear_history_callback(client: Client, query: CallbackQuery):
    await search_history_repo.collection.delete_many({"user_id": str(query.from_user.id)})
    await query.answer("✅ Search history cleared!")
    await query.message.edit_text("🕒 Search history has been cleared.")


# ===========================================================================
# 5. WATCH PROGRESS COMMAND (/progress)
# ===========================================================================
@Client.on_message(filters.command(["progress", "watching"]))
async def progress_handler(client: Client, message: Message):
    user_id = message.from_user.id
    res = await watch_progress_repo.find_many({"user_id": str(user_id)})
    if not res.items:
        return await message.reply_text("🎬 <b>No watch progress recorded yet.</b>")

    text = "🎬 <b>Your Active Watch Progress:</b>\n\n"
    buttons = []
    for item in res.items[:10]:
        d_id = item.get("drama_id")
        ep_num = item.get("episode_number", 1)
        drama = await dramas_repo.get_by_slug_or_id(d_id)
        title = drama.get("title", d_id) if drama else d_id
        text += f"• <b>{title}</b> — Ep {ep_num} {'(Completed ✅)' if item.get('is_completed') else '(Watching ⏳)'}\n"
        buttons.append([InlineKeyboardButton(f"▶️ Continue: {title[:18]} (Ep {ep_num})", switch_inline_query_current_chat=f"{title} E{ep_num}")])

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# ===========================================================================
# 6. NOTIFICATIONS COMMAND (/notifications)
# ===========================================================================
@Client.on_message(filters.command(["notifications", "alerts"]))
async def notifications_handler(client: Client, message: Message):
    user_id = message.from_user.id
    res = await notifications_repo.find_many({"user_id": str(user_id)}, limit=10)
    if not res.items:
        return await message.reply_text("🔔 <b>No new notifications.</b> You're all caught up!")

    text = "🔔 <b>Your Recent Notifications:</b>\n\n"
    for notif in res.items:
        text += f"• <b>{notif.get('title', 'Alert')}</b>\n  {notif.get('message', '')}\n\n"

    await message.reply_text(text)
