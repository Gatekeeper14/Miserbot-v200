import os
import asyncio
import threading
import random
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

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
INTRO_FILE_ID = os.environ.get("INTRO_FILE_ID","")
ADMIN_ID = int(os.environ.get("OWNER_ID","8741545426"))

WEBHOOK_PATH = "/webhook"

app = Flask(__name__)

# =========================================================
# DATABASE
# =========================================================

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
    CREATE TABLE IF NOT EXISTS fan_locations(
        telegram_id BIGINT PRIMARY KEY,
        latitude FLOAT,
        longitude FLOAT
    )
    """)

    conn.commit()
    conn.close()

# =========================================================
# EMBEDDED SONG LIBRARY
# =========================================================

SONGS = [

("BoomBoom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("MINI 14 Raw","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("GUNMAN","CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
("TRAPP","CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
("FEAR","CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA"),
("SUMMER TIME","CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA"),
("REAL GOLD","CQACAgEAAxkBAAO9adMbBDzajJrOcGNb6gVyZmjEXTYAAvwIAAI1Z5hGr3nvGz4AAYjbOwQ"),
("FACEBOOK LUST","CQACAgEAAxkBAAOzadMY-pj_rWBB5wrRP6Nfymv4q6EAAvcIAAI1Z5hG4SGuftZqhPY7BA"),
("MI ALONE","CQACAgEAAxkBAAPJadMeaMExYAvnDv8gswXyUgOMwpsAAgcJAAI1Z5hGxeKB46IBYZg7BA"),
("BUBBLE FI MI","CQACAgEAAxkBAAPPadMgBMh10TStncJQXpkyD0mJYM8AAgoJAAI1Z5hG10QJbSDmTyM7BA")

]

# =========================================================
# MENU
# =========================================================

main_menu = ReplyKeyboardMarkup(
[
["🎵 Music","📻 Radio"],
["🌐 Social","💰 Support Artist"],
["👕 Parish 14","👑 Wisdom"],
["🏋 Fitness","📍 Share Location"]
],
resize_keyboard=True
)

# =========================================================
# START + INTRO GATE
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if INTRO_FILE_ID:

        await update.message.reply_text(
        "👑 Welcome to I.A.A.I.M.O\n\nPress play before entering."
        )

        keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("▶ ENTER PLATFORM",callback_data="intro:play")]]
        )

        await update.message.reply_voice(
        INTRO_FILE_ID,
        caption="🎙 BAZRAGOD INTRO",
        reply_markup=keyboard
        )

    else:

        await update.message.reply_text(
        "👑 Welcome to Miserbot",
        reply_markup=main_menu
        )

# =========================================================
# INTRO BUTTON
# =========================================================

async def intro_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    await query.message.reply_text(
    "🔥 Welcome inside the ecosystem.",
    reply_markup=main_menu
    )

# =========================================================
# MUSIC MENU
# =========================================================

async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard=[]

    for i,song in enumerate(SONGS):

        keyboard.append([
        InlineKeyboardButton(song[0],callback_data=f"song:{i}")
        ])

    await update.message.reply_text(
    "🎧 BAZRAGOD CATALOG",
    reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================================================
# PLAY SONG
# =========================================================

async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    song_id=int(query.data.split(":")[1])

    title,file_id=SONGS[song_id]

    await query.message.reply_audio(
    file_id,
    caption=f"🎵 {title}"
    )

# =========================================================
# RADIO
# =========================================================

async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    title,file_id=random.choice(SONGS)

    await update.message.reply_audio(
    file_id,
    caption=f"📻 BAZRAGOD RADIO\n\nNow Playing: {title}"
    )

# =========================================================
# SOCIAL
# =========================================================

async def social(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard=InlineKeyboardMarkup([
    [InlineKeyboardButton("Instagram",url="https://www.instagram.com/bazragod_timeless")],
    [InlineKeyboardButton("TikTok",url="https://www.tiktok.com/@bazragod_official")],
    [InlineKeyboardButton("YouTube",url="https://youtube.com/@bazragodmusictravelandleis8835")],
    [InlineKeyboardButton("X",url="https://x.com/toligarch65693")]
    ])

    await update.message.reply_text(
    "🌐 Follow BAZRAGOD",
    reply_markup=keyboard
    )

# =========================================================
# SUPPORT
# =========================================================

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard=InlineKeyboardMarkup([
    [InlineKeyboardButton("CashApp",url="https://cash.app/$BAZRAGOD")],
    [InlineKeyboardButton("PayPal",url="https://paypal.me/bazragod1")]
    ])

    await update.message.reply_text(
    "💰 Support the Artist",
    reply_markup=keyboard
    )

# =========================================================
# MERCH
# =========================================================

async def merch(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
    "👕 PARISH 14\n\n🔥 Merch drops coming soon\n🔔 Stay ready."
    )

# =========================================================
# WISDOM
# =========================================================

async def wisdom(update: Update, context: ContextTypes.DEFAULT_TYPE):

    quotes=[
    "Discipline builds empires.",
    "Move in silence.",
    "Focus beats talent.",
    "The mission comes first."
    ]

    await update.message.reply_text(
    f"👑 Wisdom\n\n{random.choice(quotes)}"
    )

# =========================================================
# FITNESS
# =========================================================

async def fitness(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
    "🏋 Fitness Protocol\n\n50 Pushups\n50 Squats\n50 Situps\n2km Run"
    )

# =========================================================
# LOCATION
# =========================================================

async def share_location(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard=ReplyKeyboardMarkup(
    [[KeyboardButton("Send Location",request_location=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
    )

    await update.message.reply_text(
    "📍 Share your location",
    reply_markup=keyboard
    )

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    loc=update.message.location
    user=update.effective_user.id

    conn=db()
    cur=conn.cursor()

    cur.execute("""
    INSERT INTO fan_locations(telegram_id,latitude,longitude)
    VALUES(%s,%s,%s)
    ON CONFLICT (telegram_id)
    DO UPDATE SET latitude=%s,longitude=%s
    """,(user,loc.latitude,loc.longitude,loc.latitude,loc.longitude))

    conn.commit()
    conn.close()

    await update.message.reply_text("🌍 Location saved")

# =========================================================
# ADMIN AUDIO ID CAPTURE
# =========================================================

async def capture_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id!=ADMIN_ID:
        return

    audio=update.message.voice or update.message.audio

    if audio:
        await update.message.reply_text(f"FILE_ID:\n{audio.file_id}")

# =========================================================
# ROUTER
# =========================================================

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text=update.message.text

    if text=="🎵 Music":
        await music(update,context)

    elif text=="📻 Radio":
        await radio(update,context)

    elif text=="🌐 Social":
        await social(update,context)

    elif text=="💰 Support Artist":
        await support(update,context)

    elif text=="👕 Parish 14":
        await merch(update,context)

    elif text=="👑 Wisdom":
        await wisdom(update,context)

    elif text=="🏋 Fitness":
        await fitness(update,context)

    elif text=="📍 Share Location":
        await share_location(update,context)

# =========================================================
# TELEGRAM APP
# =========================================================

telegram_app=Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",start))
telegram_app.add_handler(CallbackQueryHandler(intro_cb,pattern="^intro:"))
telegram_app.add_handler(CallbackQueryHandler(play_song,pattern="^song:"))

telegram_app.add_handler(MessageHandler(filters.LOCATION,location_handler))
telegram_app.add_handler(MessageHandler(filters.VOICE|filters.AUDIO,capture_audio))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,router))

# =========================================================
# ASYNC LOOP
# =========================================================

loop=asyncio.new_event_loop()

def start_bot():

    asyncio.set_event_loop(loop)

    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    loop.run_forever()

threading.Thread(target=start_bot,daemon=True).start()

# =========================================================
# WEBHOOK
# =========================================================

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
def home():
    return "MISERBOT ONLINE"

# =========================================================
# MAIN
# =========================================================

if __name__=="__main__":

    init_db()

    app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT",8080))
    )
