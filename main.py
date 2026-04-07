"""
╔══════════════════════════════════════════════════════════════╗
║           I.A.A.I.M.O — MASTER SYSTEM v6000                 ║
║   Independent Artists Artificial Intelligence Music Ops      ║
║   Bot: Miserbot                                              ║
║   Owner: BAZRAGOD                                            ║
║   Nation: Parish 14                                          ║
╚══════════════════════════════════════════════════════════════╝
"""

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

# CONFIG

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

STORE_ITEMS = {
    "single": ("Single Song Download", 5),
    "bundle": ("Bundle — 7 Songs", 20),
    "exclusive": ("Exclusive Album — VIP", 500),
}

MERCH_ITEMS = {
    "tshirt": ("Parish 14 T-Shirt", 50),
    "pullover": ("Parish 14 Pullover", 150),
}

RADIO_CYCLE = ["song","song","drop","song","beat","promo"]

radio_position = 0

# MUSIC CATALOG

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

flask_app = Flask(__name__)
openai_client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

db_pool = SimpleConnectionPool(1,10,dsn=DATABASE_URL)

def get_db():
    return db_pool.getconn()

def release_db(conn):
    db_pool.putconn(conn)

def init_db():
# MUSIC MODULE

async def music(update,context):

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT id,title FROM songs ORDER BY id")

    songs=cur.fetchall()

    cur.close()
    release_db(conn)

    keyboard=[
        [InlineKeyboardButton(f"▶ {s[1]}",callback_data=f"song:{s[0]}")]
        for s in songs
    ]

    await update.message.reply_text(
        "🎧 BAZRAGOD CATALOG",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# PLAY SONG

async def play_song_cb(update,context):

    query=update.callback_query
    await query.answer()

    try:
        song_id=int(query.data.split(":")[1])
    except:
        return

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT title,file_id FROM songs WHERE id=%s",(song_id,))

    song=cur.fetchone()

    cur.close()
    release_db(conn)

    if song:

        await query.message.reply_audio(
            song[1],
            caption=f"🎵 {song[0]}"
        )

# RADIO ENGINE

async def radio(update,context):

    global radio_position

    slot=RADIO_CYCLE[radio_position%len(RADIO_CYCLE)]

    radio_position+=1

    conn=get_db()
    cur=conn.cursor()

    if slot=="promo":

        cur.execute("SELECT text FROM radio_promos ORDER BY RANDOM() LIMIT 1")

        promo=cur.fetchone()

        if promo:

            await update.message.reply_text(
                f"📢 {promo[0]}"
            )

        cur.close()
        release_db(conn)
        return

    cur.execute("SELECT title,file_id FROM songs ORDER BY RANDOM() LIMIT 1")

    song=cur.fetchone()

    cur.close()
    release_db(conn)

    if not song:
        return

    await update.message.reply_audio(
        song[1],
        caption=f"📻 BazraGod Radio\n🎵 {song[0]}"
    )

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,music))
telegram_app.add_handler(CallbackQueryHandler(play_song_cb,pattern="^song:"))

telegram_loop=asyncio.new_event_loop()

def start_telegram():

    asyncio.set_event_loop(telegram_loop)

    telegram_loop.run_until_complete(
        telegram_app.initialize()
    )

    telegram_loop.run_until_complete(
        telegram_app.start()
    )

    telegram_loop.run_forever()

threading.Thread(target=start_telegram,daemon=True).start()

@flask_app.route("/webhook",methods=["POST"])
def webhook():

    data=request.get_json(force=True)

    update=Update.de_json(data,telegram_app.bot)

    asyncio.run_coroutine_threadsafe(
        telegram_app.process_update(update),
        telegram_loop
    )

    return "ok"

@flask_app.route("/health")
def health():
    return "I.A.A.I.M.O ONLINE",200

if __name__=="__main__":

    init_db()

    print("MISERBOT v6000 ONLINE")

    flask_app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT",8080))
    )
    conn=get_db()
    cur=conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS songs(id SERIAL PRIMARY KEY,title TEXT,file_id TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS radio_promos(id SERIAL PRIMARY KEY,text TEXT)")

    cur.execute("SELECT COUNT(*) FROM songs")

    if cur.fetchone()[0]==0:
        cur.executemany(
            "INSERT INTO songs(title,file_id) VALUES(%s,%s)",
            SEED_SONGS
        )

    conn.commit()

    cur.close()
    release_db(conn)
