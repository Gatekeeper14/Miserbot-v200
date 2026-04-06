import os
import random
import asyncio
import threading
import psycopg2
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
OWNER_ID = int(os.environ.get("OWNER_ID"))

app = Flask(__name__)

# MUSIC LIBRARY (YOUR FILE IDS)

SONGS = [

("Boom Boom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("MINI 14 Raw","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("GUNMAN","CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
("TRAPP","CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
("FEAR","CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA"),
("SUMMER TIME","CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA"),
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

# MENU

menu = ReplyKeyboardMarkup(
[
["🎵 Music","📻 BazraGod Radio"],
["🏆 Leaderboard","💰 Support Artist"],
["🌐 Social","👕 Parish 14"],
["👑 Wisdom","🏋 Fitness"],
["📍 Share Location","⭐ My Points"]
],
resize_keyboard=True
)

# DATABASE

def db():
    return psycopg2.connect(DATABASE_URL)

def init_db():

    conn=db()
    cur=conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans(
    telegram_id BIGINT PRIMARY KEY,
    username TEXT,
    points INT DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

# POINTS

def add_points(uid,name,pts):

    conn=db()
    cur=conn.cursor()

    cur.execute("""
    INSERT INTO fans(telegram_id,username,points)
    VALUES(%s,%s,%s)
    ON CONFLICT (telegram_id)
    DO UPDATE SET points=fans.points+%s
    """,(uid,name,pts,pts))

    conn.commit()
    conn.close()

# START

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.effective_user

    add_points(user.id,user.username or user.first_name,5)

    await update.message.reply_text(
    "👑 Welcome to BazraGod Official Bot",
    reply_markup=menu
    )

# MUSIC

async def music(update:Update,context:ContextTypes.DEFAULT_TYPE):

    keyboard=[
    [InlineKeyboardButton(song[0],callback_data=f"song{idx}")]
    for idx,song in enumerate(SONGS)
    ]

    await update.message.reply_text(
    "🎧 BazraGod Playlist",
    reply_markup=InlineKeyboardMarkup(keyboard)
    )

# PLAY SONG

async def play(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    idx=int(q.data.replace("song",""))

    title,file_id=SONGS[idx]

    await q.message.reply_audio(
    file_id,
    caption=f"🎵 {title}"
    )

# RADIO

async def radio(update:Update,context:ContextTypes.DEFAULT_TYPE):

    song=random.choice(SONGS)

    await update.message.reply_audio(
    song[1],
    caption=f"📻 BazraGod Radio\n{song[0]}"
    )

# LEADERBOARD

async def leaderboard(update:Update,context:ContextTypes.DEFAULT_TYPE):

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT username,points FROM fans ORDER BY points DESC LIMIT 10")

    rows=cur.fetchall()

    conn.close()

    text="🏆 Leaderboard\n\n"

    for r in rows:

        text+=f"{r[0]} — {r[1]} pts\n"

    await update.message.reply_text(text)

# LOCATION

async def location(update:Update,context:ContextTypes.DEFAULT_TYPE):

    loc=update.message.location

    await update.message.reply_text(
    f"📍 Location received\nLat:{loc.latitude}\nLon:{loc.longitude}"
    )

# ROUTER

async def router(update:Update,context:ContextTypes.DEFAULT_TYPE):

    text=update.message.text

    if text=="🎵 Music":
        await music(update,context)

    elif text=="📻 BazraGod Radio":
        await radio(update,context)

    elif text=="🏆 Leaderboard":
        await leaderboard(update,context)

    elif text=="👑 Wisdom":

        quotes=[
        "Discipline equals freedom",
        "Move in silence",
        "The obstacle is the way",
        "Conquer yourself"
        ]

        await update.message.reply_text(random.choice(quotes))

    elif text=="🏋 Fitness":

        await update.message.reply_text(
        "🏋 50 Pushups\n50 Squats\n50 Situps\n2km Run"
        )

    elif text=="💰 Support Artist":

        keyboard=InlineKeyboardMarkup([
        [InlineKeyboardButton("CashApp",url="https://cash.app/$BAZRAGOD")],
        [InlineKeyboardButton("PayPal",url="https://paypal.me/bazragod1")]
        ])

        await update.message.reply_text(
        "Support BazraGod",
        reply_markup=keyboard
        )

    elif text=="🌐 Social":

        keyboard=InlineKeyboardMarkup([
        [InlineKeyboardButton("Instagram",url="https://instagram.com/bazragod_timeless")],
        [InlineKeyboardButton("TikTok",url="https://tiktok.com/@bazragod_official")],
        [InlineKeyboardButton("YouTube",url="https://youtube.com/@bazragodmusictravelandleis8835")]
        ])

        await update.message.reply_text(
        "Follow BazraGod",
        reply_markup=keyboard
        )

# TELEGRAM

telegram_app=Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",start))
telegram_app.add_handler(CallbackQueryHandler(play))
telegram_app.add_handler(MessageHandler(filters.LOCATION,location))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,router))

loop=asyncio.new_event_loop()

def run_bot():

    asyncio.set_event_loop(loop)

    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    loop.run_forever()

threading.Thread(target=run_bot,daemon=True).start()

# WEBHOOK

@app.route("/webhook",methods=["POST"])

def webhook():

    data=request.get_json(force=True)

    update=Update.de_json(data,telegram_app.bot)

    asyncio.run_coroutine_threadsafe(
    telegram_app.process_update(update),
    loop
    )

    return "ok"

# MAIN

if __name__=="__main__":

    init_db()

    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
