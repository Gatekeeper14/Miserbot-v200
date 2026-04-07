import os
import random
import asyncio
import threading
from datetime import datetime
from io import BytesIO
import psycopg2
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
from openai import OpenAI

# ============================================
# CONFIG
# ============================================

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

openai_client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
WEBHOOK_PATH = "/webhook"

# ============================================
# BAZRAGOD MUSIC CATALOG
# ============================================

SEED_SONGS = [
("Boom Boom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("MINI 14","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("GUNMAN","CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
("TRAPP MASTER","CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
("FEAR","CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA"),
("SUMMERTIME","CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA"),
("REAL GOLD","CQACAgEAAxkBAAO9adMbBDzajJrOcGNb6gVyZmjEXTYAAvwIAAI1Z5hGr3nvGz4AAYjbOwQ"),
("FACEBOOK LUST","CQACAgEAAxkBAAOzadMY-pj_rWBB5wrRP6Nfymv4q6EAAvcIAAI1Z5hG4SGuftZqhPY7BA"),
("MI ALONE","CQACAgEAAxkBAAPJadMeaMExYAvnDv8gswXyUgOMwpsAAgcJAAI1Z5hGxeKB46IBYZg7BA"),
("BUBBLE FI MI","CQACAgEAAxkBAAPPadMgBMh10TStncJQXpkyD0mJYM8AAgoJAAI1Z5hG10QJbSDmTyM7BA"),
("NATURAL PUSSY","CQACAgEAAxkBAAO1adMZtjgiRqYxrOFbE3KOCNxVcxQAAvgIAAI1Z5hGm8QmWqNIojg7BA"),
("FRAID AH YUH","CQACAgEAAxkBAAO3adMZ_P5y2OoXlyY0XpO_fiPiahMAAvkIAAI1Z5hGgMZ1tOmyhjA7BA"),
("CARRY GUH BRING COME","CQACAgEAAxkBAAPFadMdgVBA0MIwyLNyU8mO5-djfawAAgQJAAI1Z5hGYmzehzRMIZY7BA"),
("IMPECCABLE","CQACAgEAAxkBAAPRadMgsX9xJh3boHp64jA1-sVPC80AAgsJAAI1Z5hGIlCi8cg5E_k7BA"),
("BIG FAT MATIC","CQACAgEAAxkBAAPNadMfiOZJNeE3Eihp-r-olvpfzWIAAgkJAAI1Z5hGaNvyiVRhwEw7BA")
]

# ============================================
# DATABASE
# ============================================

def db():
    return psycopg2.connect(DATABASE_URL)

def init_db():

    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS songs(
        id SERIAL PRIMARY KEY,
        title TEXT
    )
    """)

    cur.execute("ALTER TABLE songs ADD COLUMN IF NOT EXISTS file_id TEXT")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fan_locations(
        telegram_id BIGINT PRIMARY KEY,
        latitude FLOAT,
        longitude FLOAT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans(
        telegram_id BIGINT PRIMARY KEY,
        points INT DEFAULT 0
    )
    """)

    cur.execute("SELECT COUNT(*) FROM songs")
    count = cur.fetchone()[0]

    if count == 0:
        cur.executemany(
            "INSERT INTO songs(title,file_id) VALUES(%s,%s)",
            SEED_SONGS
        )

    conn.commit()
    conn.close()

# ============================================
# MENU
# ============================================

menu = ReplyKeyboardMarkup(
[
["🎧 BAZRAGOD MUSIC","📻 BazraGod Radio"],
["🏆 Leaderboard","💰 Support Artist"],
["🌐 Social","👕 Parish 14"],
["👑 Wisdom","🏋 Fitness"],
["⭐ My Points","👥 Refer"],
["📍 Share Location"]
],
resize_keyboard=True
)

# ============================================
# START
# ============================================

async def start(update,context):
    await update.message.reply_text(
        "👑 Welcome to Miserbot — Official BAZRAGOD Platform",
        reply_markup=menu
    )

# ============================================
# MUSIC SYSTEM
# ============================================

async def music(update,context):

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT id,title FROM songs ORDER BY id")
    rows=cur.fetchall()

    conn.close()

    keyboard=[]
    for r in rows:
        keyboard.append([InlineKeyboardButton(r[1],callback_data=f"song:{r[0]}")])

    await update.message.reply_text(
        "🎧 BAZRAGOD MUSIC",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def play_song(update,context):

    query=update.callback_query
    await query.answer()

    song_id=int(query.data.split(":")[1])

    conn=db()
    cur=conn.cursor()
    cur.execute("SELECT title,file_id FROM songs WHERE id=%s",(song_id,))
    song=cur.fetchone()
    conn.close()

    if song:
        await query.message.reply_audio(song[1],caption=song[0])

# ============================================
# RADIO
# ============================================

async def radio(update,context):

    conn=db()
    cur=conn.cursor()
    cur.execute("SELECT title,file_id FROM songs ORDER BY RANDOM() LIMIT 1")
    song=cur.fetchone()
    conn.close()

    if song:
        await update.message.reply_audio(
            song[1],
            caption=f"📻 BazraGod Radio\n🎵 {song[0]}"
        )

# ============================================
# SOCIAL
# ============================================

async def social(update,context):

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Instagram",url="https://www.instagram.com/bazragod_timeless")],
        [InlineKeyboardButton("🎵 TikTok",url="https://www.tiktok.com/@bazragod_official")],
        [InlineKeyboardButton("▶️ YouTube",url="https://youtube.com/@bazragodmusictravelandleis8835")],
        [InlineKeyboardButton("🐦 X",url="https://x.com/toligarch65693")]
    ])

    await update.message.reply_text(
        "🌐 Follow BAZRAGOD",
        reply_markup=keyboard
    )

# ============================================
# SUPPORT
# ============================================

async def support(update,context):

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("CashApp",url="https://cash.app/$BAZRAGOD")],
        [InlineKeyboardButton("PayPal",url="https://paypal.me/bazragod1")]
    ])

    await update.message.reply_text(
        "💰 Support the Artist",
        reply_markup=keyboard
    )

# ============================================
# POINTS FIX
# ============================================

async def points(update,context):

    uid = update.effective_user.id

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT points FROM fans WHERE telegram_id=%s",(uid,))
    row=cur.fetchone()

    conn.close()

    if row:
        await update.message.reply_text(f"⭐ Your points: {row[0]}")
    else:
        await update.message.reply_text("⭐ You have 0 points")

# ============================================
# REFERRAL FIX
# ============================================

async def refer(update,context):

    uid = update.effective_user.id
    link = f"https://t.me/{context.bot.username}?start={uid}"

    await update.message.reply_text(
        f"👥 Invite friends and earn points\n\n{link}"
    )

# ============================================
# ROUTER
# ============================================

async def router(update,context):

    text=update.message.text

    if text=="🎧 BAZRAGOD MUSIC":
        await music(update,context)

    elif text=="📻 BazraGod Radio":
        await radio(update,context)

    elif text=="🌐 Social":
        await social(update,context)

    elif text=="💰 Support Artist":
        await support(update,context)

    elif text=="⭐ My Points":
        await points(update,context)

    elif text=="👥 Refer":
        await refer(update,context)

# ============================================
# TELEGRAM APP
# ============================================

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,router))
telegram_app.add_handler(CallbackQueryHandler(play_song,pattern="song:"))

# ============================================
# ASYNC LOOP
# ============================================

loop = asyncio.new_event_loop()

def start_bot():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    loop.run_forever()

threading.Thread(target=start_bot,daemon=True).start()

# ============================================
# WEBHOOK
# ============================================

@app.route(WEBHOOK_PATH,methods=["POST"])
def webhook():

    data=request.get_json(force=True)
    update=Update.de_json(data,telegram_app.bot)

    asyncio.run_coroutine_threadsafe(
        telegram_app.process_update(update),
        loop
    )

    return "ok"

@app.route("/")
def health():
    return "MISERBOT ONLINE"

# ============================================
# MAIN
# ============================================

if __name__=="__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT",8080))
    )
