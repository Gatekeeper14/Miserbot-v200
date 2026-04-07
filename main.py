"""
I.A.A.I.M.O — MASTER SYSTEM v5000
"""

import os
import random
import asyncio
import threading
from datetime import datetime, date
from io import BytesIO
import psycopg2
from psycopg2.pool import SimpleConnectionPool
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

BOT_TOKEN=os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL=os.environ.get("DATABASE_URL")
OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY")
OWNER_ID=int(os.environ.get("OWNER_ID","8741545426"))

BOT_USERNAME="miserbot"
WEBHOOK_PATH="/webhook"

openai_client=OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app=Flask(__name__)

# =========================
# DATABASE POOL
# =========================

db_pool=None

def init_pool():
    global db_pool
    db_pool=SimpleConnectionPool(1,10,dsn=DATABASE_URL)

def get_db():
    return db_pool.getconn()

def release_db(conn):
    db_pool.putconn(conn)

# =========================
# POINT SYSTEM
# =========================

POINTS={
"start":5,
"play_song":8,
"radio":10,
"invite_friend":20
}

RANKS=[
(0,"Fan"),
(100,"Supporter"),
(500,"Recruiter"),
(1000,"Commander"),
(2500,"General")
]

def get_rank(points):

    rank="Fan"

    for threshold,label in RANKS:
        if points>=threshold:
            rank=label

    return rank

# =========================
# MUSIC CATALOG
# =========================

SEED_SONGS=[

("Boom Boom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("MINI 14","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("GUNMAN","CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
("TRAPP MASTER","CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
("FEAR","CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA"),
("SUMMERTIME","CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA"),
("REAL GOLD","CQACAgEAAxkBAAO9adMbBDzajJrOcGNb6gVyZmjEXTYAAvwIAAI1Z5hGr3nvGz4AAYjbOwQ")

]

# =========================
# DATABASE INIT
# =========================

def init_db():

    conn=get_db()
    cur=conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans(
    telegram_id BIGINT PRIMARY KEY,
    username TEXT,
    points INT DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS songs(
    id SERIAL PRIMARY KEY,
    title TEXT,
    file_id TEXT
    )
    """)

    cur.execute("SELECT COUNT(*) FROM songs")

    if cur.fetchone()[0]==0:

        cur.executemany(
        "INSERT INTO songs(title,file_id) VALUES(%s,%s)",
        SEED_SONGS
        )

    conn.commit()
    release_db(conn)

# =========================
# MENU
# =========================

main_menu=ReplyKeyboardMarkup(

[
["🎧 Music","📻 Radio"],
["🏆 Leaderboard","⭐ My Points"],
["🛒 Store","👕 Merch"],
["🌐 Social","💰 Support"],
["🤖 MAXIMUS AI"]
],

resize_keyboard=True
)

# =========================
# START
# =========================

async def start(update,context):

    uid=update.effective_user.id
    name=update.effective_user.first_name

    conn=get_db()
    cur=conn.cursor()

    cur.execute(
    "INSERT INTO fans(telegram_id,username) VALUES(%s,%s) ON CONFLICT DO NOTHING",
    (uid,name)
    )

    conn.commit()
    release_db(conn)

    await update.message.reply_text(
    "Welcome to Miserbot — BAZRAGOD Platform",
    reply_markup=main_menu
    )

# =========================
# MUSIC MENU
# =========================

async def music(update,context):

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT id,title FROM songs ORDER BY id")

    rows=cur.fetchall()

    release_db(conn)

    keyboard=[]

    for r in rows:
        keyboard.append(
        [InlineKeyboardButton(r[1],callback_data=f"song:{r[0]}")]
        )

    await update.message.reply_text(
    "BAZRAGOD MUSIC",
    reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def play_song(update,context):

    query=update.callback_query
    await query.answer()

    song_id=int(query.data.split(":")[1])

    conn=get_db()
    cur=conn.cursor()

    cur.execute(
    "SELECT title,file_id FROM songs WHERE id=%s",
    (song_id,)
    )

    song=cur.fetchone()

    release_db(conn)

    if song:

        await query.message.reply_audio(
        song[1],
        caption=song[0]
        )

# =========================
# RADIO
# =========================

async def radio(update,context):

    conn=get_db()
    cur=conn.cursor()

    cur.execute(
    "SELECT title,file_id FROM songs ORDER BY RANDOM() LIMIT 1"
    )

    song=cur.fetchone()

    release_db(conn)

    if song:

        now=datetime.now().strftime("%I:%M %p")

        await update.message.reply_audio(
        song[1],
        caption=f"📻 BazraGod Radio — {now}\n\n{song[0]}"
        )
# =========================
# LEADERBOARD
# =========================

async def leaderboard(update,context):

    conn=get_db()
    cur=conn.cursor()

    cur.execute(
    "SELECT username,points FROM fans ORDER BY points DESC LIMIT 10"
    )

    rows=cur.fetchall()

    release_db(conn)

    if not rows:

        await update.message.reply_text(
        "🏆 Leaderboard\n\nNo stats yet."
        )

        return

    text="🏆 Leaderboard\n\n"

    for i,r in enumerate(rows):

        text+=f"{i+1}. {r[0]} — {r[1]} pts\n"

    await update.message.reply_text(text)

# =========================
# POINTS
# =========================

async def points(update,context):

    uid=update.effective_user.id

    conn=get_db()
    cur=conn.cursor()

    cur.execute(
    "SELECT points FROM fans WHERE telegram_id=%s",
    (uid,)
    )

    row=cur.fetchone()

    release_db(conn)

    if not row:

        await update.message.reply_text(
        "No points accumulated yet."
        )

        return

    await update.message.reply_text(
    f"⭐ Your Points: {row[0]}"
    )

# =========================
# ROUTER
# =========================

async def router(update,context):

    text=update.message.text

    if text=="🎧 Music":
        await music(update,context)

    elif text=="📻 Radio":
        await radio(update,context)

    elif text=="🏆 Leaderboard":
        await leaderboard(update,context)

    elif text=="⭐ My Points":
        await points(update,context)

# =========================
# TELEGRAM APP
# =========================

telegram_app=Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",start))

telegram_app.add_handler(
MessageHandler(filters.TEXT & ~filters.COMMAND,router)
)

telegram_app.add_handler(
CallbackQueryHandler(play_song,pattern="song:")
)

# =========================
# BOT LOOP
# =========================

loop=asyncio.new_event_loop()

def start_bot():

    asyncio.set_event_loop(loop)

    loop.run_until_complete(
    telegram_app.initialize()
    )

    loop.run_until_complete(
    telegram_app.start()
    )

    loop.run_forever()

threading.Thread(target=start_bot,daemon=True).start()

# =========================
# WEBHOOK
# =========================

@app.route(WEBHOOK_PATH,methods=["POST"])
def webhook():

    try:

        data=request.get_json(force=True)

        update=Update.de_json(data,telegram_app.bot)

        asyncio.run_coroutine_threadsafe(
        telegram_app.process_update(update),
        loop
        )

        return "ok"

    except Exception as e:

        print(e)

        return "error"

@app.route("/")
def health():

    return "MISERBOT ONLINE"

# =========================
# MAIN
# =========================

if __name__=="__main__":

    init_pool()

    init_db()

    app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT",8080))
    )
