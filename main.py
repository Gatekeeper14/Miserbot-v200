"""
═══════════════════════════════════════════════════════
  I.A.A.I.M.O — Independent Artists Artificial
  Intelligence Music Operations
  Bot:     Miserbot
  Owner:   BAZRAGOD
  Mission: Global Artist Independence
═══════════════════════════════════════════════════════
"""

import os
import random
import asyncio
import threading
import psycopg2
from datetime import datetime
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

# ═══════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

ADMIN_ID = 8741545426

# FIXED BOT USERNAME FOR REFERRALS
BOT_USERNAME = "miserbot_v200_bot"

WEBHOOK_PATH = "/webhook"

CASHAPP = "https://cash.app/$BAZRAGOD"
PAYPAL = "https://paypal.me/bazragod1"

SOCIALS = {
    "📸 Instagram": "https://www.instagram.com/bazragod_timeless",
    "🎵 TikTok": "https://www.tiktok.com/@bazragod_official",
    "▶️ YouTube": "https://youtube.com/@bazragodmusictravelandleis8835",
    "🐦 X": "https://x.com/toligarch65693",
}

# SAFE OPENAI INITIALIZATION
openai_client = None
if OPENAI_KEY:
    openai_client = OpenAI(api_key=OPENAI_KEY)

# ═══════════════════════════════════════════════════
# RADIO ENGINE STATE
# ═══════════════════════════════════════════════════

RADIO_CYCLE = ["music", "music", "drop", "music", "beat", "music"]
radio_position = 0

pending_broadcasts = {}

# ═══════════════════════════════════════════════════
# FLASK
# ═══════════════════════════════════════════════════

app = Flask(__name__)

# ═══════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════

def get_db():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans(
        telegram_id BIGINT PRIMARY KEY,
        username TEXT,
        points INT DEFAULT 0,
        invites INT DEFAULT 0,
        tier TEXT DEFAULT 'Fan',
        joined_at TIMESTAMP DEFAULT NOW()
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS songs(
        id SERIAL PRIMARY KEY,
        title TEXT,
        file_id TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS beats(
        id SERIAL PRIMARY KEY,
        title TEXT,
        file_id TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS drops(
        id SERIAL PRIMARY KEY,
        title TEXT,
        file_id TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fan_locations(
        telegram_id BIGINT PRIMARY KEY,
        latitude FLOAT,
        longitude FLOAT,
        updated_at TIMESTAMP DEFAULT NOW()
    )
    """)

    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════
# POINT SYSTEM
# ═══════════════════════════════════════════════════

POINTS = {
    "start": 5,
    "play_song": 8,
    "radio": 10,
    "share_location": 15,
    "ai_chat": 2
}

def award_points(uid, action, username=None):

    pts = POINTS.get(action, 1)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO fans (telegram_id,username,points)
    VALUES (%s,%s,%s)
    ON CONFLICT (telegram_id)
    DO UPDATE SET points=fans.points + %s
    """,(uid,username,pts,pts))

    conn.commit()
    conn.close()

    return pts

# ═══════════════════════════════════════════════════
# MENU
# ═══════════════════════════════════════════════════

main_menu = ReplyKeyboardMarkup(
[
["🎵 Music","📻 Radio"],
["🥁 Beats","🎤 Drops"],
["🏆 Leaderboard","⭐ My Points"],
["💰 Support Artist","🌐 Social"],
["👕 Parish 14","👑 Wisdom"],
["🏋 Fitness","📍 Share Location"],
["🤖 AI Assistant","👥 Refer a Friend"]
],
resize_keyboard=True
)

# ═══════════════════════════════════════════════════
# START
# ═══════════════════════════════════════════════════

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    name = update.effective_user.username or update.effective_user.first_name

    pts = award_points(uid,"start",name)

    msg = (
        "👑 WELCOME TO MISERBOT\n\n"
        "I.A.A.I.M.O\n\n"
        "Stream BAZRAGOD music\n"
        "Earn points\n"
        "Climb the leaderboard\n\n"
        f"+{pts} pts"
    )

    await update.message.reply_text(msg,reply_markup=main_menu)

# ═══════════════════════════════════════════════════
# MUSIC
# ═══════════════════════════════════════════════════

async def music(update:Update,context:ContextTypes.DEFAULT_TYPE):

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT id,title FROM songs ORDER BY id")

    songs=cur.fetchall()

    conn.close()

    keyboard=[
        [InlineKeyboardButton(s[1],callback_data=f"song:{s[0]}")]
        for s in songs
    ]

    await update.message.reply_text(
        "🎧 BAZRAGOD MUSIC",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def play_song(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    song_id=int(query.data.split(":")[1])

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT title,file_id FROM songs WHERE id=%s",(song_id,))
    song=cur.fetchone()

    conn.close()

    if song:

        uid=query.from_user.id
        name=query.from_user.username or query.from_user.first_name

        pts=award_points(uid,"play_song",name)

        await query.message.reply_audio(
            song[1],
            caption=f"🎵 {song[0]}\n\n+{pts} pts"
        )

# ═══════════════════════════════════════════════════
# RADIO
# ═══════════════════════════════════════════════════

async def radio(update:Update,context:ContextTypes.DEFAULT_TYPE):

    global radio_position

    slot=RADIO_CYCLE[radio_position%len(RADIO_CYCLE)]
    radio_position+=1

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT title,file_id FROM songs ORDER BY RANDOM() LIMIT 1")
    song=cur.fetchone()

    conn.close()

    if song:

        await update.message.reply_audio(
            song[1],
            caption=f"📻 BazraGod Radio\n\nNow playing: {song[0]}"
        )

# ═══════════════════════════════════════════════════
# AI ASSISTANT
# ═══════════════════════════════════════════════════

async def ai(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if not openai_client:
        await update.message.reply_text("AI unavailable.")
        return

    msg=update.message.text

    response=openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":msg}]
    )

    await update.message.reply_text(
        response.choices[0].message.content
    )

# ═══════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════

async def router(update:Update,context:ContextTypes.DEFAULT_TYPE):

    text=update.message.text

    routes={
        "🎵 Music":music,
        "📻 Radio":radio,
        "🤖 AI Assistant":ai
    }

    handler=routes.get(text)

    if handler:
        await handler(update,context)

# ═══════════════════════════════════════════════════
# TELEGRAM APP
# ═══════════════════════════════════════════════════

telegram_app=Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",start))
telegram_app.add_handler(CallbackQueryHandler(play_song,pattern="^song:"))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,router))

# ═══════════════════════════════════════════════════
# ASYNC LOOP
# ═══════════════════════════════════════════════════

telegram_loop=asyncio.new_event_loop()

def start_telegram():

    asyncio.set_event_loop(telegram_loop)

    telegram_loop.run_until_complete(telegram_app.initialize())
    telegram_loop.run_until_complete(telegram_app.start())

    telegram_loop.run_forever()

threading.Thread(target=start_telegram,daemon=True).start()

# ═══════════════════════════════════════════════════
# WEBHOOK
# ═══════════════════════════════════════════════════

@app.route(WEBHOOK_PATH,methods=["POST"])
def webhook():

    data=request.get_json(force=True)

    update=Update.de_json(data,telegram_app.bot)

    asyncio.run_coroutine_threadsafe(
        telegram_app.process_update(update),
        telegram_loop
    )

    return "ok"

@app.route("/health")
def health():
    return "I.A.A.I.M.O ONLINE",200

# ═══════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════

if __name__=="__main__":

    init_db()

    print("MISERBOT ONLINE")

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT",8080))
    )
