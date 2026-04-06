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
OWNER_ID = int(os.environ.get("OWNER_ID"))

WEBHOOK_PATH = "/webhook"

app = Flask(__name__)

# DATABASE

def db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = db()
    cur = conn.cursor()

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
        username TEXT,
        points INT DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

# MENU

main_menu = ReplyKeyboardMarkup(
[
["🎧 BAZRAGOD MUSIC","📻 BazraGod Radio"],
["🏆 Leaderboard","💰 Support Artist"],
["🌐 Social","👕 Parish 14"],
["👑 Wisdom","🏋 Fitness"]
],
resize_keyboard=True
)

# START

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
    "👑 Welcome to Miserbot\n\nOfficial AI platform of BAZRAGOD",
    reply_markup=main_menu
    )

# MUSIC

async def music(update:Update,context:ContextTypes.DEFAULT_TYPE):

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT id,title FROM songs ORDER BY id")
    rows=cur.fetchall()

    conn.close()

    if not rows:
        await update.message.reply_text("No songs uploaded yet")
        return

    keyboard=[]

    for r in rows:
        keyboard.append(
        [InlineKeyboardButton(r[1],callback_data=f"song:{r[0]}")]
        )

    await update.message.reply_text(
    "🎧 BAZRAGOD MUSIC",
    reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def play_song(update:Update,context:ContextTypes.DEFAULT_TYPE):

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

# RADIO

async def radio(update:Update,context:ContextTypes.DEFAULT_TYPE):

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT title,file_id FROM songs ORDER BY RANDOM() LIMIT 1")
    song=cur.fetchone()

    conn.close()

    if song:
        await update.message.reply_audio(
        song[1],
        caption=f"📻 BazraGod Radio\n\nNow Playing: {song[0]}"
        )

# LEADERBOARD

async def leaderboard(update:Update,context:ContextTypes.DEFAULT_TYPE):

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT username,points FROM fans ORDER BY points DESC LIMIT 10")
    rows=cur.fetchall()

    conn.close()

    text="🏆 Leaderboard\n\n"

    for i,r in enumerate(rows):
        text+=f"{i+1}. {r[0]} - {r[1]} pts\n"

    await update.message.reply_text(text)

# SUPPORT

async def support(update:Update,context:ContextTypes.DEFAULT_TYPE):

    keyboard=InlineKeyboardMarkup([
    [InlineKeyboardButton("CashApp",url="https://cash.app/$BAZRAGOD")],
    [InlineKeyboardButton("PayPal",url="https://paypal.me/bazragod1")]
    ])

    await update.message.reply_text(
    "Support the artist 👑",
    reply_markup=keyboard
    )

# SOCIAL

async def social(update:Update,context:ContextTypes.DEFAULT_TYPE):

    keyboard=InlineKeyboardMarkup([
    [InlineKeyboardButton("Instagram",url="https://instagram.com")],
    [InlineKeyboardButton("TikTok",url="https://tiktok.com")],
    [InlineKeyboardButton("YouTube",url="https://youtube.com")]
    ])

    await update.message.reply_text(
    "Follow BAZRAGOD",
    reply_markup=keyboard
    )

# MERCH

async def merch(update:Update,context:ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
    "👕 Parish 14 merchandise coming soon."
    )

# WISDOM

quotes=[
"Discipline equals freedom.",
"Move in silence.",
"Kings are made through struggle."
]

async def wisdom(update:Update,context:ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
    random.choice(quotes)
    )

# FITNESS

async def fitness(update:Update,context:ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
    "🏋 BAZRAGOD Fitness Protocol\n\n50 Pushups\n50 Squats\n50 Situps"
    )

# ADMIN SONG UPLOAD

async def upload(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id!=OWNER_ID:
        return

    audio=update.message.audio

    if not audio:
        return

    title=audio.title or "Untitled"
    file_id=audio.file_id

    conn=db()
    cur=conn.cursor()

    cur.execute(
    "INSERT INTO songs(title,file_id) VALUES(%s,%s)",
    (title,file_id)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(f"Song uploaded: {title}")

# ROUTER FIX (THIS WAS THE PROBLEM)

async def router(update:Update,context:ContextTypes.DEFAULT_TYPE):

    text=update.message.text

    if text=="🎧 BAZRAGOD MUSIC":
        await music(update,context)

    elif text=="📻 BazraGod Radio":
        await radio(update,context)

    elif text=="🏆 Leaderboard":
        await leaderboard(update,context)

    elif text=="💰 Support Artist":
        await support(update,context)

    elif text=="🌐 Social":
        await social(update,context)

    elif text=="👕 Parish 14":
        await merch(update,context)

    elif text=="👑 Wisdom":
        await wisdom(update,context)

    elif text=="🏋 Fitness":
        await fitness(update,context)

# TELEGRAM

telegram_app=Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,router))
telegram_app.add_handler(MessageHandler(filters.AUDIO,upload))
telegram_app.add_handler(CallbackQueryHandler(play_song,pattern="song:"))

# LOOP

loop=asyncio.new_event_loop()

def start_bot():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    loop.run_forever()

threading.Thread(target=start_bot,daemon=True).start()

# WEBHOOK

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

# MAIN

if __name__=="__main__":

    init_db()

    print("MISERBOT RUNNING")

    app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT",8080))
    )
