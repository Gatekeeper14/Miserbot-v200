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
filters
)
from openai import OpenAI

BOT_TOKEN=os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL=os.environ.get("DATABASE_URL")
OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY")

openai_client=OpenAI(api_key=OPENAI_API_KEY)

app=Flask(__name__)
WEBHOOK_PATH="/webhook"

# =================================
# MUSIC CATALOG
# =================================

SEED_SONGS=[

("Boom Boom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("MINI 14","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("GUNMAN","CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
("TRAPP MASTER","CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
("FEAR","CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA"),
("SUMMERTIME","CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA"),
("REAL GOLD","CQACAgEAAxkBAAO9adMbBDzajJrOcGNb6gVyZmjEXTYAAvwIAAI1Z5hGr3nvGz4AAYjbOwQ"),
("FACEBOOK LUST","CQACAgEAAxkBAAOzadMY-pj_rWBB5wrRP6Nfymv4q6EAAvcIAAI1Z5hG4SGuftZqhPY7BA")

]

# =================================
# DATABASE
# =================================

def db():
    return psycopg2.connect(DATABASE_URL)

def init_db():

    conn=db()
    cur=conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS songs(
    id SERIAL PRIMARY KEY,
    title TEXT,
    file_id TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans(
    telegram_id BIGINT PRIMARY KEY,
    points INT DEFAULT 0
    )
    """)

    cur.execute("SELECT COUNT(*) FROM songs")

    if cur.fetchone()[0]==0:
        cur.executemany(
        "INSERT INTO songs(title,file_id) VALUES(%s,%s)",
        SEED_SONGS
        )

    conn.commit()
    conn.close()

# =================================
# MENU
# =================================

menu=ReplyKeyboardMarkup([

["🎧 BAZRAGOD MUSIC","📻 BazraGod Radio"],
["🛒 Music Store","👕 Parish 14"],
["🏆 Leaderboard","⭐ My Points"],
["🌐 Social","💰 Support Artist"],
["👑 Wisdom","🏋 Fitness"],
["📍 Share Location"]

],resize_keyboard=True)

# =================================
# START
# =================================

async def start(update,context):

    conn=db()
    cur=conn.cursor()

    cur.execute(
    "INSERT INTO fans(telegram_id) VALUES(%s) ON CONFLICT DO NOTHING",
    (update.effective_user.id,)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
    "👑 Welcome to Miserbot — BAZRAGOD Platform",
    reply_markup=menu
    )

# =================================
# MUSIC
# =================================

async def music(update,context):

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT id,title FROM songs")

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

    sid=int(query.data.split(":")[1])

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT title,file_id FROM songs WHERE id=%s",(sid,))
    song=cur.fetchone()

    conn.close()

    await ai_dj(context,query.from_user.id,song[0])

    await query.message.reply_audio(song[1],caption=song[0])

# =================================
# AI DJ
# =================================

async def ai_dj(context,chat_id,title):

    try:

        text=f"Now playing {title} on BazraGod Radio."

        response=openai_client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=text
        )

        audio=BytesIO(response.content)
        audio.name="dj.ogg"

        await context.bot.send_voice(chat_id=chat_id,voice=audio)

    except:
        pass

# =================================
# RADIO
# =================================

async def radio(update,context):

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT title,file_id FROM songs ORDER BY RANDOM() LIMIT 1")

    song=cur.fetchone()

    conn.close()

    await ai_dj(context,update.effective_user.id,song[0])

    await update.message.reply_audio(song[1],caption=f"📻 {song[0]}")

# =================================
# STORE
# =================================

async def store(update,context):

    keyboard=InlineKeyboardMarkup([

    [InlineKeyboardButton("Single Track $5",callback_data="buy_single")],
    [InlineKeyboardButton("Bundle 7 Songs $20",callback_data="buy_bundle")],
    [InlineKeyboardButton("VIP Album $500",callback_data="buy_album")]

    ])

    await update.message.reply_text(
    "🛒 BAZRAGOD Music Store",
    reply_markup=keyboard
    )

# =================================
# MERCH
# =================================

async def merch(update,context):

    keyboard=InlineKeyboardMarkup([

    [InlineKeyboardButton("T-Shirt $50",url="https://cash.app/$BAZRAGOD")],
    [InlineKeyboardButton("Pullover $150",url="https://cash.app/$BAZRAGOD")]

    ])

    await update.message.reply_text(
    "👕 Parish 14 Merch",
    reply_markup=keyboard
    )

# =================================
# LEADERBOARD
# =================================

async def leaderboard(update,context):

    conn=db()
    cur=conn.cursor()

    cur.execute(
    "SELECT telegram_id,points FROM fans ORDER BY points DESC LIMIT 10"
    )

    rows=cur.fetchall()
    conn.close()

    if not rows:

        await update.message.reply_text("🏆 Leaderboard\n\nNo stats yet.")
        return

    text="🏆 Leaderboard\n\n"

    for i,r in enumerate(rows):
        text+=f"{i+1}. {r[0]} — {r[1]} pts\n"

    await update.message.reply_text(text)

# =================================
# POINTS
# =================================

async def points(update,context):

    conn=db()
    cur=conn.cursor()

    cur.execute(
    "SELECT points FROM fans WHERE telegram_id=%s",
    (update.effective_user.id,)
    )

    row=cur.fetchone()
    conn.close()

    if not row or row[0]==0:

        await update.message.reply_text("⭐ No points accumulated yet.")
        return

    await update.message.reply_text(f"⭐ Your points: {row[0]}")

# =================================
# ROUTER
# =================================

async def router(update,context):

    t=update.message.text

    if t=="🎧 BAZRAGOD MUSIC":
        await music(update,context)

    elif t=="📻 BazraGod Radio":
        await radio(update,context)

    elif t=="🛒 Music Store":
        await store(update,context)

    elif t=="👕 Parish 14":
        await merch(update,context)

    elif t=="🏆 Leaderboard":
        await leaderboard(update,context)

    elif t=="⭐ My Points":
        await points(update,context)

# =================================
# TELEGRAM
# =================================

telegram_app=Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,router))
telegram_app.add_handler(CallbackQueryHandler(play_song,pattern="song:"))

# =================================
# LOOP
# =================================

loop=asyncio.new_event_loop()

def start_bot():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    loop.run_forever()

threading.Thread(target=start_bot,daemon=True).start()

# =================================
# WEBHOOK
# =================================

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

# =================================
# MAIN
# =================================

if __name__=="__main__":

    init_db()

    app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT",8080))
    )
