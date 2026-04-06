import os
import random
import asyncio
import threading
from datetime import datetime
import psycopg2
from flask import Flask, request
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
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
from io import BytesIO

# ═══════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OWNER_ID = int(os.environ.get("OWNER_ID"))

openai_client = OpenAI(api_key=OPENAI_API_KEY)

WEBHOOK_PATH = "/webhook"
app = Flask(__name__)

# ═══════════════════════════════════════════════════
# ORIGINAL BAZRAGOD MUSIC
# ═══════════════════════════════════════════════════

SEED_SONGS = [
("Boom Boom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("MINI 14","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("GUNMAN","CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
("TRAP","CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
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

# ═══════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════

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
        username TEXT,
        points INT DEFAULT 0
    )
    """)

    cur.execute("SELECT COUNT(*) FROM songs")
    count=cur.fetchone()[0]

    if count==0:
        cur.executemany(
        "INSERT INTO songs(title,file_id) VALUES(%s,%s)",
        SEED_SONGS
        )

    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════
# MAXIMUS VOICE ENGINE
# ═══════════════════════════════════════════════════

async def maximus_speak(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str):

    if not openai_client:
        return

    try:

        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=text,
            speed=0.95
        )

        audio_bytes = response.content
        audio_file = BytesIO(audio_bytes)
        audio_file.name = "maximus.ogg"

        await context.bot.send_voice(chat_id=chat_id, voice=audio_file)

    except Exception as e:
        print("MAXIMUS voice error:",e)

# ═══════════════════════════════════════════════════
# MENU
# ═══════════════════════════════════════════════════

menu = ReplyKeyboardMarkup([
["🎧 BAZRAGOD MUSIC","📻 BazraGod Radio"],
["🏆 Leaderboard","💰 Support Artist"],
["🌐 Social","👕 Parish 14"],
["👑 Wisdom","🏋 Fitness"]
],resize_keyboard=True)

# ═══════════════════════════════════════════════════
# START
# ═══════════════════════════════════════════════════

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
    "👑 Welcome to Miserbot\nOfficial AI platform of BAZRAGOD",
    reply_markup=menu
    )

# ═══════════════════════════════════════════════════
# MUSIC
# ═══════════════════════════════════════════════════

async def music(update:Update,context:ContextTypes.DEFAULT_TYPE):

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT id,title FROM songs ORDER BY id")
    rows=cur.fetchall()

    conn.close()

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

        await maximus_speak(context,query.from_user.id,f"Now playing {song[0]}")

        await query.message.reply_audio(song[1],caption=song[0])

# ═══════════════════════════════════════════════════
# RADIO
# ═══════════════════════════════════════════════════

async def radio(update:Update,context:ContextTypes.DEFAULT_TYPE):

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT title,file_id FROM songs ORDER BY RANDOM() LIMIT 1")
    song=cur.fetchone()

    conn.close()

    if song:

        now=datetime.now().strftime("%I:%M %p")

        dj_lines=[
        f"You are now listening to BazraGod Radio. Next up {song[0]}",
        f"This is I.A.A.I.M.O radio. The time is {now}. We running {song[0]}",
        f"No label no middleman. BazraGod Radio playing {song[0]}"
        ]

        dj_text=random.choice(dj_lines)

        await maximus_speak(context,update.effective_user.id,dj_text)

        await update.message.reply_audio(
        song[1],
        caption=f"📻 BazraGod Radio\nNow Playing: {song[0]}"
        )

# ═══════════════════════════════════════════════════
# LEADERBOARD
# ═══════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════
# SUPPORT
# ═══════════════════════════════════════════════════

async def support(update:Update,context:ContextTypes.DEFAULT_TYPE):

    keyboard=InlineKeyboardMarkup([
    [InlineKeyboardButton("CashApp",url="https://cash.app/$BAZRAGOD")],
    [InlineKeyboardButton("PayPal",url="https://paypal.me/bazragod1")]
    ])

    await update.message.reply_text("Support the artist 👑",reply_markup=keyboard)

# ═══════════════════════════════════════════════════
# SOCIAL
# ═══════════════════════════════════════════════════

async def social(update:Update,context:ContextTypes.DEFAULT_TYPE):

    keyboard=InlineKeyboardMarkup([
    [InlineKeyboardButton("Instagram",url="https://instagram.com")],
    [InlineKeyboardButton("TikTok",url="https://tiktok.com")],
    [InlineKeyboardButton("YouTube",url="https://youtube.com")]
    ])

    await update.message.reply_text("Follow BAZRAGOD",reply_markup=keyboard)

# ═══════════════════════════════════════════════════
# OTHER MODULES
# ═══════════════════════════════════════════════════

async def merch(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👕 Parish 14 merchandise coming soon.")

quotes=[
"Discipline equals freedom",
"Move in silence",
"Kings are made through struggle"
]

async def wisdom(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(quotes))

async def fitness(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏋 50 Pushups\n50 Squats\n50 Situps")

# ═══════════════════════════════════════════════════
# ADMIN UPLOAD
# ═══════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════════════════

telegram_app=Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,router))
telegram_app.add_handler(MessageHandler(filters.AUDIO,upload))
telegram_app.add_handler(CallbackQueryHandler(play_song,pattern="song:"))

# ═══════════════════════════════════════════════════
# LOOP
# ═══════════════════════════════════════════════════

loop=asyncio.new_event_loop()

def start_bot():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    loop.run_forever()

threading.Thread(target=start_bot,daemon=True).start()

# ═══════════════════════════════════════════════════
# WEBHOOK
# ═══════════════════════════════════════════════════

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
    return "MISERBOT MASTER ONLINE"

# ═══════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════

if __name__=="__main__":

    init_db()

    print("MISERBOT MASTER RUNNING")

    app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT",8080))
    )
