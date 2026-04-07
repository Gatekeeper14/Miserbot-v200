# I.A.A.I.M.O MISERBOT SYSTEM
# PART 1

import os
import random
import asyncio
import threading
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from io import BytesIO
from datetime import datetime, date
from openai import OpenAI
from flask import Flask, request

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

ADMIN_ID = 8741545426
BOT_USERNAME = "miserbot"

WEBHOOK_PATH = "/webhook"

INTRO_FILE_ID = os.environ.get(
    "INTRO_FILE_ID",
    "CQACAgEAAxkBAAICN2nUZHzzXlQszP-a08nJiSctUeOhAAL-BQACEbKpRg3vpxJvYve3OwQ"
)

CASHAPP = "https://cash.app/$BAZRAGOD"
PAYPAL = "https://paypal.me/bazragod1"

SOCIALS = {
    "📸 Instagram": "https://www.instagram.com/bazragod_timeless",
    "🎵 TikTok": "https://www.tiktok.com/@bazragod_official",
    "▶️ YouTube": "https://youtube.com/@bazragodmusictravelandleis8835",
    "🐦 X": "https://x.com/toligarch65693",
}

flask_app = Flask(__name__)
openai_client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

pending_broadcasts = {}

db_pool = None


def init_pool():
    global db_pool
    db_pool = SimpleConnectionPool(1, 10, dsn=DATABASE_URL)
    print("DB POOL READY")


def get_db():
    return db_pool.getconn()


def release_db(conn):
    try:
        db_pool.putconn(conn)
    except Exception:
        pass
POINTS = {
    "start": 5,
    "play_song": 8,
    "play_beat": 6,
    "radio": 10,
    "share_location": 15,
    "follow_social": 3,
    "support_artist": 5,
    "invite_friend": 20,
    "wisdom": 3,
    "fitness": 3,
    "ai_chat": 2,
    "buy_music": 50,
    "mission": 100,
}

RANKS = [
    (0, "🎧 Fan"),
    (100, "⚔️ Supporter"),
    (500, "🎖 Recruiter"),
    (1000, "🏅 Commander"),
    (2500, "👑 General"),
    (5000, "🛸 Parish 14 Elite"),
]

SEED_SONGS = [
("Chibonge Remix Rap Version","CQACAgEAAxkBAAOtadMWVB7xX8ss7Nkp6neA0L7gbU0AAvQIAAI1Z5hGYMUV7Mozbyw7BA"),
("Natural Pussy (Tie Mi)","CQACAgEAAxkBAAO1adMZtjgiRqYxrOFbE3KOCNxVcxQAAvgIAAI1Z5hGm8QmWqNIojg7BA"),
("Fraid Ah Yuh (Feat. Dami D)","CQACAgEAAxkBAAO3adMZ_P5y2OoXlyY0XpO_fiPiahMAAvkIAAI1Z5hGgMZ1tOmyhjA7BA"),
("Mini 14 (Raw)","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("Boom Boom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("Summertime","CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA"),
("Mini 14 HD Mix","CQACAgEAAxkBAAPBadMcgWIUbXd6lfNjIt8C_SMhpz8AAv4IAAI1Z5hGrA8jfr5073A7BA"),
("Carry Guh Bring Come","CQACAgEAAxkBAAPFadMdgVBA0MIwyLNyU8mO5-djfawAAgQJAAI1Z5hGYmzehzRMIZY7BA"),
("Trapp (Master)","CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
("Gunman","CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
("Impeccable","CQACAgEAAxkBAAPRadMgsX9xJh3boHp64jA1-sVPC80AAgsJAAI1Z5hGIlCi8cg5E_k7BA"),
("Fear","CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA"),
("Bubble Fi Mi","CQACAgEAAxkBAAPPadMgBMh10TStncJQXpkyD0mJYM8AAgoJAAI1Z5hG10QJbSDmTyM7BA"),
("Big Fat Matic","CQACAgEAAxkBAAPNadMfiOZJNeE3Eihp-r-olvpfzWIAAgkJAAI1Z5hGaNvyiVRhwEw7BA"),
("Mi Alone","CQACAgEAAxkBAAPJadMeaMExYAvnDv8gswXyUgOMwpsAAgcJAAI1Z5hGxeKB46IBYZg7BA"),
("Real Gold","CQACAgEAAxkBAAO9adMbBDzajJrOcGNb6gVyZmjEXTYAAvwIAAI1Z5hGr3nvGz4AAYjbOwQ"),
("Facebook Lust","CQACAgEAAxkBAAOzadMY-pj_rWBB5wrRP6Nfymv4q6EAAvcIAAI1Z5hG4SGuftZqhPY7BA"),
("BAZRAGOD & Sara Charismata","CQACAgEAAxkBAAICWGnUbUMJb5_1Baajef0VQFq0HMCaAAIFBgACEbKpRluYDh3M8F57OwQ"),
]
main_menu = ReplyKeyboardMarkup(
[
["🎵 Music","📻 Radio"],
["🥁 Beats","🎤 Drops"],
["🏆 Leaderboard","⭐ My Points"],
["👤 My Profile","🎯 Daily Mission"],
["💰 Support Artist","🌐 Social"],
["🛒 Music Store","👕 Parish 14 Merch"],
["👑 Wisdom","🏋 Fitness"],
["📍 Share Location","👥 Refer a Friend"],
["🤖 AI Assistant"],
],
resize_keyboard=True,
)
telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))
telegram_app.add_handler(MessageHandler(filters.LOCATION, location_handler))
telegram_app.add_handler(MessageHandler(filters.AUDIO, upload_handler))

telegram_loop = asyncio.new_event_loop()

def start_telegram():
asyncio.set_event_loop(telegram_loop)
telegram_loop.run_until_complete(telegram_app.initialize())
telegram_loop.run_until_complete(telegram_app.start())
telegram_loop.run_forever()

threading.Thread(target=start_telegram, daemon=True).start()


@flask_app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():

try:
data = request.get_json(force=True)

update = Update.de_json(data, telegram_app.bot)

asyncio.run_coroutine_threadsafe(
telegram_app.process_update(update),
telegram_loop
)

except Exception as e:
print("WEBHOOK ERROR", e)

return "ok"


@flask_app.route("/health")
def health():
return "MISERBOT ONLINE", 200


if __name__ == "__main__":

init_pool()
init_db()

print("MISERBOT v5000 ONLINE")

flask_app.run(
host="0.0.0.0",
port=int(os.environ.get("PORT", 8080))
)
