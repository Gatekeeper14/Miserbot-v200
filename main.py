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

BOT_TOKEN=os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL=os.environ.get("DATABASE_URL")
OWNER_ID=int(os.environ.get("OWNER_ID","0"))

app=Flask(__name__)
WEBHOOK_PATH="/webhook"

# ============================================
# MUSIC CATALOG
# ============================================

SEED_SONGS=[

("Boom Boom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("MINI 14","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("GUNMAN","CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
("TRAPP MASTER","CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
("FEAR","CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA"),
("SUMMERTIME","CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA"),
("REAL GOLD","CQACAgEAAxkBAAO9adMbBDzajJrOcGNb6gVyZmjEXTYAAvwIAAI1Z5hGr3nvGz4AAYjbOwQ"),
("FACEBOOK LUST","CQACAgEAAxkBAAOzadMY-pj_rWBB5wrRP6Nfymv4q6EAAvcIAAI1Z5hG4SGuftZqhPY7BA"),
("MI ALONE","CQACAgEAAxkBAAPJadMeaMExYAvnDv8gswXyUgOMwpsAAgcJAAI1Z5hGxeKB46IBYZg7BA"),
("BUBBLE FI MI","CQACAgEAAxkBAAPPadMgBMh10TStncJQXpkyD0mJYM8AAgoJAAI1Z5hG10QJbSDmTyM7BA")

]

# ============================================
# DATABASE
# ============================================

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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fan_locations(
        telegram_id BIGINT PRIMARY KEY,
        latitude FLOAT,
        longitude FLOAT
    )
    """)

    cur.execute("SELECT COUNT(*) FROM songs")
    if cur.fetchone()[0]==0:
        cur.executemany("INSERT INTO songs(title,file_id) VALUES(%s,%s)",SEED_SONGS)

    conn.commit()
    conn.close()

# ============================================
# MENU
# ============================================

menu=ReplyKeyboardMarkup([
["🎧 BAZRAGOD MUSIC","📻 BazraGod Radio"],
["🏆 Leaderboard","💰 Support Artist"],
["🌐 Social","👕 Parish 14"],
["👑 Wisdom","🏋 Fitness"],
["⭐ My Points","👥 Refer"],
["📍 Share Location"]
],resize_keyboard=True)

# ============================================
# START
# ============================================

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
    "👑 Welcome to Miserbot — Official BAZRAGOD Platform",
    reply_markup=menu
    )

# ============================================
# MUSIC
# ============================================

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

    await update.message.reply_audio(song[1],caption=f"📻 {song[0]}")

# ============================================
# SOCIAL
# ============================================

async def social(update,context):

    keyboard=InlineKeyboardMarkup([
    [InlineKeyboardButton("Instagram",url="https://instagram.com/bazragod_timeless")],
    [InlineKeyboardButton("TikTok",url="https://tiktok.com/@bazragod_official")],
    [InlineKeyboardButton("YouTube",url="https://youtube.com/@bazragodmusictravelandleis8835")]
    ])

    await update.message.reply_text("Follow BAZRAGOD",reply_markup=keyboard)

# ============================================
# SUPPORT
# ============================================

async def support(update,context):

    keyboard=InlineKeyboardMarkup([
    [InlineKeyboardButton("CashApp",url="https://cash.app/$BAZRAGOD")],
    [InlineKeyboardButton("PayPal",url="https://paypal.me/bazragod1")]
    ])

    await update.message.reply_text("Support the artist",reply_markup=keyboard)

# ============================================
# MERCH
# ============================================

async def merch(update,context):

    await update.message.reply_text(
    "👕 Parish 14 Merch\n\nT-Shirt $50\nPullover $150\n\nComing soon."
    )

# ============================================
# WISDOM
# ============================================

async def wisdom(update,context):

    quotes=[
    "Discipline equals freedom.",
    "Kings are built through struggle.",
    "Move in silence.",
    "Focus creates destiny."
    ]

    await update.message.reply_text(random.choice(quotes))

# ============================================
# FITNESS
# ============================================

async def fitness(update,context):

    await update.message.reply_text(
    "🏋 Fitness Protocol\n\n50 Pushups\n50 Squats\n50 Situps\nRun 2km"
    )

# ============================================
# LEADERBOARD
# ============================================

async def leaderboard(update,context):

    conn=db()
    cur=conn.cursor()

    cur.execute(
    "SELECT telegram_id,points FROM fans ORDER BY points DESC LIMIT 10"
    )

    rows=cur.fetchall()
    conn.close()

    text="🏆 Leaderboard\n\n"

    for i,r in enumerate(rows):
        text+=f"{i+1}. {r[0]} — {r[1]} pts\n"

    await update.message.reply_text(text)

# ============================================
# POINTS
# ============================================

async def points(update,context):

    conn=db()
    cur=conn.cursor()

    cur.execute(
    "SELECT points FROM fans WHERE telegram_id=%s",
    (update.effective_user.id,)
    )

    row=cur.fetchone()
    conn.close()

    if row:
        await update.message.reply_text(f"⭐ Your points: {row[0]}")
    else:
        await update.message.reply_text("⭐ 0 points")

# ============================================
# REFERRAL
# ============================================

async def refer(update,context):

    uid=update.effective_user.id
    link=f"https://t.me/{context.bot.username}?start={uid}"

    await update.message.reply_text(
    f"Invite friends and earn points\n\n{link}"
    )

# ============================================
# LOCATION
# ============================================

async def location_prompt(update,context):

    kb=ReplyKeyboardMarkup(
    [[KeyboardButton("Send Location",request_location=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
    )

    await update.message.reply_text(
    "Share your location to join the fan map",
    reply_markup=kb
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
    (update.effective_user.id,loc.latitude,loc.longitude,loc.latitude,loc.longitude))

    conn.commit()
    conn.close()

    await update.message.reply_text("Location saved")

# ============================================
# ROUTER
# ============================================

async def router(update,context):

    t=update.message.text

    if t=="🎧 BAZRAGOD MUSIC":
        await music(update,context)

    elif t=="📻 BazraGod Radio":
        await radio(update,context)

    elif t=="🌐 Social":
        await social(update,context)

    elif t=="💰 Support Artist":
        await support(update,context)

    elif t=="👕 Parish 14":
        await merch(update,context)

    elif t=="👑 Wisdom":
        await wisdom(update,context)

    elif t=="🏋 Fitness":
        await fitness(update,context)

    elif t=="🏆 Leaderboard":
        await leaderboard(update,context)

    elif t=="⭐ My Points":
        await points(update,context)

    elif t=="👥 Refer":
        await refer(update,context)

    elif t=="📍 Share Location":
        await location_prompt(update,context)

# ============================================
# TELEGRAM
# ============================================

telegram_app=Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,router))
telegram_app.add_handler(CallbackQueryHandler(play_song,pattern="song:"))
telegram_app.add_handler(MessageHandler(filters.LOCATION,location_handler))

# ============================================
# LOOP
# ============================================

loop=asyncio.new_event_loop()

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
