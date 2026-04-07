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

# ================================
# CONFIG
# ================================

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
OWNER_ID = int(os.environ.get("OWNER_ID","8741545426"))

app = Flask(__name__)
WEBHOOK_PATH="/webhook"

# ================================
# HARDWIRED MUSIC
# ================================

SONGS = [

("Boom Boom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("MINI 14","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("GUNMAN","CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
("TRAPP MASTER","CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
("FEAR","CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA"),
("SUMMERTIME","CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA"),
("REAL GOLD","CQACAgEAAxkBAAO9adMbBDzajJrOcGNb6gVyZmjEXTYAAvwIAAI1Z5hGr3nvGz4AAYjbOwQ")

]

# ================================
# DATABASE
# ================================

def db():
    return psycopg2.connect(DATABASE_URL)

def add_points(user_id,username,pts):

    conn=db()
    cur=conn.cursor()

    cur.execute("""
    INSERT INTO fans(telegram_id,username,points)
    VALUES(%s,%s,%s)
    ON CONFLICT (telegram_id)
    DO UPDATE SET
    username=EXCLUDED.username,
    points=fans.points + %s
    """,(user_id,username,pts,pts))

    conn.commit()
    conn.close()

def get_points(user_id):

    conn=db()
    cur=conn.cursor()

    cur.execute(
    "SELECT points FROM fans WHERE telegram_id=%s",
    (user_id,)
    )

    row=cur.fetchone()
    conn.close()

    if row:
        return row[0]
    return 0

# ================================
# MENUS
# ================================

menu1 = ReplyKeyboardMarkup(
[
["🎧 Music","📻 Radio"],
["🏆 Leaderboard","⭐ My Points"],
["🛒 Store","👕 Merch"],
["➡ Next"]
],
resize_keyboard=True
)

menu2 = ReplyKeyboardMarkup(
[
["💰 Support","🌐 Social"],
["📍 Location"],
["⬅ Back"]
],
resize_keyboard=True
)

# ================================
# START
# ================================

async def start(update,context):

    user=update.effective_user
    add_points(user.id,user.username,5)

    await update.message.reply_text(
        "👑 Welcome to Miserbot\nBAZRAGOD Platform",
        reply_markup=menu1
    )

# ================================
# MUSIC MENU
# ================================

async def music(update,context):

    keyboard=[]

    i=0
    for s in SONGS:

        keyboard.append(
        [InlineKeyboardButton(s[0],callback_data=f"song:{i}")]
        )

        i+=1

    await update.message.reply_text(
        "🎧 BAZRAGOD MUSIC",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def play_song(update,context):

    query=update.callback_query
    await query.answer()

    idx=int(query.data.split(":")[1])

    title,file_id = SONGS[idx]

    await query.message.reply_audio(
        file_id,
        caption=title
    )

    user=query.from_user
    add_points(user.id,user.username,5)

# ================================
# RADIO
# ================================

async def radio(update,context):

    song=random.choice(SONGS)

    await update.message.reply_audio(
        song[1],
        caption=f"📻 BazraGod Radio\n{song[0]}"
    )

    user=update.effective_user
    add_points(user.id,user.username,3)

# ================================
# LEADERBOARD
# ================================

async def leaderboard(update,context):

    conn=db()
    cur=conn.cursor()

    cur.execute("""
    SELECT username,points
    FROM fans
    ORDER BY points DESC
    LIMIT 5
    """)

    rows=cur.fetchall()
    conn.close()

    text="🏆 Leaderboard\n\n"

    i=1

    for r in rows:

        name=r[0] if r[0] else "fan"
        pts=r[1]

        text+=f"{i}. @{name} — {pts} pts\n"

        i+=1

    await update.message.reply_text(text)

# ================================
# POINTS
# ================================

async def mypoints(update,context):

    user=update.effective_user
    pts=get_points(user.id)

    await update.message.reply_text(
        f"⭐ Your Points: {pts}"
    )
# ================================
# STORE
# ================================

async def store(update,context):

    keyboard=InlineKeyboardMarkup([
    [InlineKeyboardButton("Single Song $5",url="https://cash.app/$BAZRAGOD")],
    [InlineKeyboardButton("Bundle $20",url="https://cash.app/$BAZRAGOD")]
    ])

    await update.message.reply_text(
        "🛒 Music Store",
        reply_markup=keyboard
    )

# ================================
# MERCH
# ================================

async def merch(update,context):

    keyboard=InlineKeyboardMarkup([
    [InlineKeyboardButton("T-Shirt $50",url="https://cash.app/$BAZRAGOD")],
    [InlineKeyboardButton("Pullover $150",url="https://cash.app/$BAZRAGOD")]
    ])

    await update.message.reply_text(
        "👕 Parish 14 Merch",
        reply_markup=keyboard
    )

# ================================
# SUPPORT
# ================================

async def support(update,context):

    keyboard=InlineKeyboardMarkup([
    [InlineKeyboardButton("CashApp",url="https://cash.app/$BAZRAGOD")],
    [InlineKeyboardButton("PayPal",url="https://paypal.me/bazragod1")]
    ])

    await update.message.reply_text(
        "💰 Support the Artist",
        reply_markup=keyboard
    )

# ================================
# SOCIAL
# ================================

async def social(update,context):

    keyboard=InlineKeyboardMarkup([
    [InlineKeyboardButton("Instagram",url="https://instagram.com/bazragod_timeless")],
    [InlineKeyboardButton("TikTok",url="https://tiktok.com/@bazragod_official")],
    [InlineKeyboardButton("YouTube",url="https://youtube.com/@bazragodmusictravelandleis8835")]
    ])

    await update.message.reply_text(
        "🌐 Follow BAZRAGOD",
        reply_markup=keyboard
    )

# ================================
# LOCATION
# ================================

async def location_prompt(update,context):

    keyboard=ReplyKeyboardMarkup(
        [[KeyboardButton("Send Location",request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await update.message.reply_text(
        "📍 Share your location",
        reply_markup=keyboard
    )

async def location_handler(update,context):

    loc=update.message.location

    conn=db()
    cur=conn.cursor()

    cur.execute("""
    INSERT INTO fan_locations(telegram_id,latitude,longitude)
    VALUES(%s,%s,%s)
    ON CONFLICT (telegram_id)
    DO UPDATE SET latitude=%s,longitude=%s
    """,
    (update.effective_user.id,loc.latitude,loc.longitude,
    loc.latitude,loc.longitude))

    conn.commit()
    conn.close()

    await update.message.reply_text("Location saved")

# ================================
# ROUTER
# ================================

async def router(update,context):

    text=update.message.text

    if text=="🎧 Music":
        await music(update,context)

    elif text=="📻 Radio":
        await radio(update,context)

    elif text=="🏆 Leaderboard":
        await leaderboard(update,context)

    elif text=="⭐ My Points":
        await mypoints(update,context)

    elif text=="🛒 Store":
        await store(update,context)

    elif text=="👕 Merch":
        await merch(update,context)

    elif text=="💰 Support":
        await support(update,context)

    elif text=="🌐 Social":
        await social(update,context)

    elif text=="📍 Location":
        await location_prompt(update,context)

    elif text=="➡ Next":
        await update.message.reply_text(
            "More options",
            reply_markup=menu2
        )

    elif text=="⬅ Back":
        await update.message.reply_text(
            "Main Menu",
            reply_markup=menu1
        )

# ================================
# TELEGRAM APP
# ================================

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,router))
telegram_app.add_handler(MessageHandler(filters.LOCATION,location_handler))
telegram_app.add_handler(CallbackQueryHandler(play_song,pattern="song:"))

# ================================
# BOT LOOP
# ================================

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

# ================================
# WEBHOOK
# ================================

@app.route("/webhook",methods=["POST"])
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

# ================================
# MAIN
# ================================

if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT",8080))
    )
