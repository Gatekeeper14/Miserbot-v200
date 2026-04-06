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
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ---------------- CONFIG ----------------

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
ADMIN_ID = int(os.environ.get("OWNER_ID"))

WEBHOOK_PATH = "/webhook"

app = Flask(__name__)

# ---------------- DATABASE ----------------

def get_db():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans (
        telegram_id BIGINT PRIMARY KEY,
        username TEXT,
        points INT DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS songs (
        id SERIAL PRIMARY KEY,
        title TEXT,
        file_id TEXT
    )
    """)

    conn.commit()
    conn.close()

# ---------------- MENU ----------------

menu = ReplyKeyboardMarkup(
    [
        ["🎵 Music", "📻 BazraGod Radio"],
        ["🏆 Leaderboard", "💰 Support Artist"],
        ["🌐 Social", "👕 Parish 14"],
        ["👑 Wisdom", "🏋 Fitness"],
        ["⭐ My Points"],
    ],
    resize_keyboard=True,
)

# ---------------- POINT SYSTEM ----------------

POINTS = {
    "start": 5,
    "music": 2,
    "play": 8,
    "radio": 10,
}

def add_points(uid, name, action):

    pts = POINTS.get(action, 1)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO fans (telegram_id, username, points)
    VALUES (%s,%s,%s)
    ON CONFLICT (telegram_id)
    DO UPDATE SET points = fans.points + %s
    """,(uid,name,pts,pts))

    conn.commit()
    conn.close()

    return pts

# ---------------- COMMANDS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    name = update.effective_user.username or update.effective_user.first_name

    pts = add_points(uid,name,"start")

    await update.message.reply_text(
        f"👑 Welcome to Miserbot\n\nYou earned {pts} points",
        reply_markup=menu
    )

# ---------------- MUSIC ----------------

async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id,title FROM songs ORDER BY id")
    rows = cur.fetchall()

    conn.close()

    if not rows:
        await update.message.reply_text("No songs uploaded yet.")
        return

    keyboard = [
        [InlineKeyboardButton(r[1],callback_data=f"song:{r[0]}")]
        for r in rows
    ]

    await update.message.reply_text(
        "🎧 Playlist",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    sid = int(q.data.split(":")[1])

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT title,file_id FROM songs WHERE id=%s",(sid,))
    row = cur.fetchone()

    conn.close()

    if row:

        uid = q.from_user.id
        name = q.from_user.username or q.from_user.first_name

        pts = add_points(uid,name,"play")

        await q.message.reply_audio(
            row[1],
            caption=f"🎵 {row[0]}\n\n+{pts} points"
        )

# ---------------- RADIO ----------------

async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT title,file_id FROM songs ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone()

    conn.close()

    if row:
        await update.message.reply_audio(
            row[1],
            caption=f"📻 BazraGod Radio\n\n{row[0]}"
        )

# ---------------- LEADERBOARD ----------------

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT username,points
    FROM fans
    ORDER BY points DESC
    LIMIT 10
    """)

    rows = cur.fetchall()
    conn.close()

    text = "🏆 Leaderboard\n\n"

    for i,r in enumerate(rows,1):
        text += f"{i}. {r[0]} — {r[1]} pts\n"

    await update.message.reply_text(text)

# ---------------- MY POINTS ----------------

async def my_points(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT points FROM fans WHERE telegram_id=%s",(uid,))
    r = cur.fetchone()

    conn.close()

    pts = r[0] if r else 0

    await update.message.reply_text(f"⭐ You have {pts} points")

# ---------------- ROUTER ----------------

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🎵 Music":
        await music(update,context)

    elif text == "📻 BazraGod Radio":
        await radio(update,context)

    elif text == "🏆 Leaderboard":
        await leaderboard(update,context)

    elif text == "⭐ My Points":
        await my_points(update,context)

    elif text == "💰 Support Artist":

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("CashApp",url="https://cash.app/$BAZRAGOD")],
            [InlineKeyboardButton("PayPal",url="https://paypal.me/bazragod1")]
        ])

        await update.message.reply_text(
            "Support BazraGod 👑",
            reply_markup=keyboard
        )

    elif text == "🌐 Social":

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Instagram",url="https://instagram.com/bazragod_timeless")],
            [InlineKeyboardButton("TikTok",url="https://tiktok.com/@bazragod_official")],
            [InlineKeyboardButton("YouTube",url="https://youtube.com/@bazragodmusictravelandleis8835")]
        ])

        await update.message.reply_text(
            "Follow BazraGod",
            reply_markup=keyboard
        )

    elif text == "👑 Wisdom":

        quotes = [
            "Move in silence. Only speak when it's time to say checkmate.",
            "A lion doesn't concern himself with the opinions of sheep.",
            "Discipline equals freedom.",
            "He who conquers himself is the mightiest warrior."
        ]

        await update.message.reply_text(
            f"👑 Wisdom\n\n{random.choice(quotes)}"
        )

    elif text == "🏋 Fitness":

        await update.message.reply_text(
            "🏋 BazraGod Fitness\n\n"
            "50 Pushups\n"
            "50 Squats\n"
            "50 Situps\n"
            "2km Run"
        )

    elif text == "👕 Parish 14":

        await update.message.reply_text(
            "👕 Parish 14 merch coming soon 🔥"
        )

# ---------------- ADMIN UPLOAD ----------------

async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    audio = update.message.audio

    if not audio:
        return

    title = audio.title or "Unknown"
    file_id = audio.file_id

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO songs (title,file_id) VALUES (%s,%s)",
        (title,file_id)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text("Song added")

# ---------------- TELEGRAM APP ----------------

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",start))
telegram_app.add_handler(CallbackQueryHandler(play_song))
telegram_app.add_handler(MessageHandler(filters.AUDIO,upload))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,router))

# ---------------- LOOP ----------------

loop = asyncio.new_event_loop()

def run_bot():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    loop.run_forever()

threading.Thread(target=run_bot,daemon=True).start()

# ---------------- WEBHOOK ----------------

@app.route(WEBHOOK_PATH,methods=["POST"])
def webhook():

    data = request.get_json(force=True)

    update = Update.de_json(data,telegram_app.bot)

    asyncio.run_coroutine_threadsafe(
        telegram_app.process_update(update),
        loop
    )

    return "ok"

@app.route("/health")
def health():
    return "ONLINE"

# ---------------- MAIN ----------------

if __name__ == "__main__":

    init_db()

    print("MISERBOT RUNNING")

    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",8080)))
