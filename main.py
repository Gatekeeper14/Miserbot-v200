"""
╔══════════════════════════════════════════════════════════════╗
║         I.A.A.I.M.O — MASTER SYSTEM v15.000                 ║
║  Independent Artists Artificial Intelligence Music Ops       ║
║  Bot:     Miserbot       Nation:  Parish 14                  ║
║  Owner:   BAZRAGOD                                           ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import re
import time
import random
import asyncio
import threading
from datetime import datetime, date, timedelta
from io import BytesIO
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from flask import Flask, request

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from openai import OpenAI

BOT_TOKEN        = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL     = os.environ.get("DATABASE_URL")
OPENAI_API_KEY   = os.environ.get("OPENAI_API_KEY")
OWNER_ID         = int(os.environ.get("OWNER_ID", "8741545426"))
RADIO_CHANNEL_ID = os.environ.get("RADIO_CHANNEL_ID", "")
BOT_USERNAME     = "miserbot"
WEBHOOK_PATH     = "/webhook"

INTRO_FILE_ID = os.environ.get(
    "INTRO_FILE_ID",
    "CQACAgEAAxkBAAEdA9Jp2WRb5KP00P7uDWZQhizBRaY0nAACfwcAAmxuyUaMnHhvbPnphTsE",
)

BOOKING_EMAIL = "Miserbot.ai@gmail.com"
CASHAPP       = "https://cash.app/$BAZRAGOD"
PAYPAL        = "https://paypal.me/bazragod1"

SUPPORTER_PRICE   = 19.99
CHARITY_PRICE     = 1.00
CHARITY_THRESHOLD = 500

RADIO_SONG_DELAY     = 200
RADIO_BEAT_DELAY     = 120
RADIO_DROP_DELAY     = 35
RADIO_AD_DELAY       = 25
RADIO_ANNOUNCE_DELAY = 30

PLAYLIST_CACHE_TTL = 300

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
app = Flask(__name__)
SUPPORTED_LANGUAGES = {
    "en": "🇺🇸 English",
    "es": "🇪🇸 Español",
    "fr": "🇫🇷 Français",
    "pt": "🇧🇷 Português",
    "de": "🇩🇪 Deutsch",
    "jm": "🇯🇲 Patois",
}

TRANSLATIONS = {
    "en": {
        "select_lang": "🌍 Select your language to enter the platform.",
        "lang_saved": "✅ Language saved.",
        "welcome_inside": "🛸 YOU ARE NOW INSIDE\n\nI.A.A.I.M.O — Parish 14 Nation.\nNo labels. No middlemen. Just the movement.\n\nYou are part of history. 🔥",
        "no_songs": "Catalog loading… check back soon.",
        "location_saved": "📍 Location recorded!\n\nYour city is on the map 🌍\n\nBAZRAGOD sees where his army stands. 👑",
        "mission_done": "🎯 MISSION COMPLETE!\n\nCome back tomorrow. Parish 14 never stops. 👑",
    }
}

def t(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )
db_pool = None

def init_pool():
    global db_pool
    db_pool = SimpleConnectionPool(1, 10, dsn=DATABASE_URL)

def get_db():
    return db_pool.getconn()

def release_db(conn):
    db_pool.putconn(conn)
DJS = {
    "aurora": {
        "name": "DJ Aurora",
        "emoji": "🌅",
        "hours": range(5, 12),
        "db_key": "aurora",
    },
    "colorred": {
        "name": "DJ Color Red",
        "emoji": "🔴",
        "hours": range(12, 18),
        "db_key": "colorred",
    },
    "maximus": {
        "name": "DJ Maximus",
        "emoji": "👑",
        "hours": range(18, 24),
        "db_key": "maximus",
    },
    "eclipse": {
        "name": "DJ Eclipse",
        "emoji": "🌑",
        "hours": range(0, 5),
        "db_key": "eclipse",
    },
}
def get_current_dj():
    hour = datetime.utcnow().hour
    for dj in DJS.values():
        if hour in dj["hours"]:
            return dj
    return DJS["maximus"]


async def get_user_language(user_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT language FROM users WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    release_db(conn)

    if row:
        return row[0]
    return "en"


async def save_user_language(user_id: int, lang: str):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users (user_id, language)
        VALUES (%s,%s)
        ON CONFLICT (user_id)
        DO UPDATE SET language=EXCLUDED.language
        """,
        (user_id, lang),
    )

    conn.commit()
    release_db(conn)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    keyboard = [
        [InlineKeyboardButton("🌍 Choose Language", callback_data="choose_lang")]
    ]

    await context.bot.send_audio(
        chat_id=user.id,
        audio=INTRO_FILE_ID
    )

    await context.bot.send_message(
        chat_id=user.id,
        text="🛸 Welcome to BAZRAGOD Radio\n\nPress below to begin.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []

    for code, label in SUPPORTED_LANGUAGES.items():
        keyboard.append([InlineKeyboardButton(label, callback_data=f"lang_{code}")])

    await update.callback_query.edit_message_text(
        text="🌍 Select your language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = query.data.split("_")[1]

    user_id = query.from_user.id

    await save_user_language(user_id, lang)

    await query.edit_message_text(
        text="✅ Language saved."
    )

    await show_main_menu(user_id, context)
async def show_main_menu(user_id, context):
    keyboard = ReplyKeyboardMarkup(
        [
            ["📻 Radio", "🎵 Music"],
            ["🔥 Trending", "🏆 Leaderboard"],
            ["🛰 Fan Radar", "🎯 Missions"],
            ["👤 My Profile", "🛍 Merch"],
            ["💎 Vault", "💬 Lounge"],
            ["⚙ Settings", "❓ Help"]
        ],
        resize_keyboard=True
    )

    await context.bot.send_message(
        chat_id=user_id,
        text="🚀 Enter the platform",
        reply_markup=keyboard
    )
async def play_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT file_id,title,type
        FROM radio_queue
        ORDER BY id ASC
        LIMIT 1
        """
    )

    row = cur.fetchone()

    release_db(conn)

    if not row:
        await update.message.reply_text("Radio queue empty.")
        return

    file_id, title, mode = row

    await context.bot.send_audio(
        chat_id=chat_id,
        audio=file_id,
        caption=f"📻 Now playing\n\n{title}"
    )
async def show_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT title,file_id FROM music_catalog LIMIT 20")
    rows = cur.fetchall()

    release_db(conn)

    if not rows:
        await update.message.reply_text("Catalog loading…")
        return

    for title, file_id in rows:
        await context.bot.send_audio(
            chat_id=update.effective_chat.id,
            audio=file_id,
            caption=title
        )
async def fan_radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT city,country FROM fan_locations LIMIT 10"
    )

    rows = cur.fetchall()
    release_db(conn)

    if not rows:
        await update.message.reply_text("Radar initializing…")
        return

    text = "🛰 FAN RADAR\n\n"

    for city, country in rows:
        text += f"📍 {city}, {country}\n"

    await update.message.reply_text(text)
async def missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 DAILY MISSIONS\n\n"
        "1️⃣ Share the bot\n"
        "2️⃣ Invite a friend\n"
        "3️⃣ Play a track\n\n"
        "Earn fan points."
    )
async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT fan_points
        FROM users
        WHERE user_id=%s
        """,
        (user_id,)
    )

    row = cur.fetchone()
    release_db(conn)

    points = row[0] if row else 0

    await update.message.reply_text(
        f"👤 Your Profile\n\nFan Points: {points}"
    )
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ Help\n\n"
        "Use the menu buttons to navigate the platform.\n\n"
        "Radio — live broadcast\n"
        "Music — catalog\n"
        "Vault — exclusive tracks"
    )
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📻 Radio":
        await play_radio(update, context)

    elif text == "🎵 Music":
        await show_music(update, context)

    elif text == "🛰 Fan Radar":
        await fan_radar(update, context)

    elif text == "🎯 Missions":
        await missions(update, context)

    elif text == "👤 My Profile":
        await my_profile(update, context)

    elif text == "❓ Help":
        await help_command(update, context)
def build_app():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(choose_language, pattern="choose_lang"))
    application.add_handler(CallbackQueryHandler(set_language, pattern="lang_"))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return application
telegram_app = None

@app.route(WEBHOOK_PATH, methods=["POST"])
async def webhook():
    if telegram_app:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        await telegram_app.process_update(update)
    return "OK"
def run():
    global telegram_app

    init_pool()

    telegram_app = build_app()

    telegram_app.bot.set_webhook(
        url=f"https://worker-production-9d2b.up.railway.app{WEBHOOK_PATH}"
    )
if __name__ == "__main__":
    run()
