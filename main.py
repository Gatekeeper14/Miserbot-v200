"""
╔══════════════════════════════════════════════════════════════╗
║         I.A.A.I.M.O — MASTER SYSTEM v15.000                 ║
║  Independent Artists Artificial Intelligence Music Ops       ║
║  Bot: Miserbot       Nation: Parish 14                       ║
║  Owner: BAZRAGOD                                            ║
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


BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BASE_URL = os.environ.get("BASE_URL")

OWNER_ID = int(os.environ.get("OWNER_ID", "8741545426"))
WEBHOOK_PATH = "/webhook"

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = Flask(__name__)
telegram_app = None

db_pool = None


def init_pool():
    global db_pool
    db_pool = SimpleConnectionPool(1, 10, dsn=DATABASE_URL)


def get_db():
    return db_pool.getconn()


def release_db(conn):
    db_pool.putconn(conn)


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
        "welcome_inside": "🛸 YOU ARE NOW INSIDE\n\nI.A.A.I.M.O — Parish 14 Nation.\nNo labels. No middlemen. Just the movement.\n\nYou are part of history.",
        "no_songs": "Catalog loading… check back soon.",
    }
}


def t(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )


DJS = {
    "aurora": {"name": "DJ Aurora", "emoji": "🌅", "hours": range(5, 12)},
    "colorred": {"name": "DJ Color Red", "emoji": "🔴", "hours": range(12, 18)},
    "maximus": {"name": "DJ Maximus", "emoji": "👑", "hours": range(18, 24)},
    "eclipse": {"name": "DJ Eclipse", "emoji": "🌑", "hours": range(0, 5)},
}


def get_current_dj():
    hour = datetime.utcnow().hour
    for dj in DJS.values():
        if hour in dj["hours"]:
            return dj
    return DJS["maximus"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌍 Choose Language", callback_data="choose_lang")]
    ]

    await update.message.reply_text(
        "🛸 Welcome to BAZRAGOD Radio",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []

    for code, label in SUPPORTED_LANGUAGES.items():
        keyboard.append([InlineKeyboardButton(label, callback_data=f"lang_{code}")])

    await update.callback_query.edit_message_text(
        text="🌍 Select your language:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = query.data.split("_")[1]

    await query.edit_message_text(text="✅ Language saved.")


async def show_main_menu(chat_id, context):
    keyboard = ReplyKeyboardMarkup(
        [
            ["📻 Radio", "🎵 Music"],
            ["🔥 Trending", "🏆 Leaderboard"],
            ["🛰 Fan Radar", "🎯 Missions"],
            ["👤 My Profile", "🛍 Merch"],
            ["💎 Vault", "💬 Lounge"],
            ["⚙ Settings", "❓ Help"],
        ],
        resize_keyboard=True,
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text="🚀 Enter the platform",
        reply_markup=keyboard,
    )


async def play_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📻 Radio starting...")


async def show_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Music catalog coming soon.")


async def fan_radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛰 Radar initializing...")


async def missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 Missions loading...")


async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👤 Profile loading...")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Help section.")


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


@app.route(WEBHOOK_PATH, methods=["POST"])
async def webhook():
    global telegram_app

    if telegram_app:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        await telegram_app.process_update(update)

    return "OK"


async def run():
    global telegram_app

    init_pool()

    telegram_app = build_app()

    await telegram_app.initialize()
    await telegram_app.start()

    # FIXED: await required
    await telegram_app.bot.set_webhook(
        url=f"{BASE_URL}{WEBHOOK_PATH}"
    )


if __name__ == "__main__":
    asyncio.run(run())
