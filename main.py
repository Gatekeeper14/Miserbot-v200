import os
import random
import psycopg2
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

ADMIN_ID = 8741545426

WEBHOOK_URL = "https://worker-production-9d2b.up.railway.app/webhook"

app_flask = Flask(__name__)


# ---------- DATABASE ----------

def get_db():
    return psycopg2.connect(DATABASE_URL)


def init_db():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans(
        telegram_id BIGINT PRIMARY KEY,
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

    conn.commit()
    conn.close()


# ---------- MENU ----------

menu = ReplyKeyboardMarkup(
[
["🎵 Music","📻 BazraGod Radio"],
["🏆 Leaderboard","💰 Support Artist"],
["🌐 Social","👕 Parish 14"],
["👑 Wisdom","🏋 Fitness"],
["🚀 Open Player"]
],
resize_keyboard=True
)


# ---------- START ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO fans (telegram_id) VALUES (%s) ON CONFLICT DO NOTHING",
        (user,)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "👑 Welcome to MISERBOT V2000\n\nBAZRAGOD Official Music Platform",
        reply_markup=menu
    )


# ---------- MUSIC MENU ----------

async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id,title FROM songs ORDER BY id")

    songs = cur.fetchall()

    conn.close()

    if not songs:
        await update.message.reply_text("No songs uploaded yet.")
        return

    keyboard = []

    for s in songs:
        keyboard.append(
            [InlineKeyboardButton(f"▶ {s[1]}", callback_data=str(s[0]))]
        )

    await update.message.reply_text(
        "🎧 BAZRAGOD PLAYLIST",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------- PLAY SONG ----------

async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    song_id = query.data

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT title,file_id FROM songs WHERE id=%s",
        (song_id,)
    )

    song = cur.fetchone()

    conn.close()

    if song:

        await query.message.reply_audio(
            song[1],
            caption=f"🎵 {song[0]}"
        )


# ---------- RADIO ----------

async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT title,file_id FROM songs ORDER BY RANDOM() LIMIT 1"
    )

    song = cur.fetchone()

    conn.close()

    if song:

        await update.message.reply_audio(
            song[1],
            caption=f"📻 BazraGod Radio\n\n{song[0]}"
        )


# ---------- SONG UPLOAD (ADMIN) ----------

async def upload_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    audio = update.message.audio

    if not audio:
        return

    title = audio.title if audio.title else "Unknown"
    file_id = audio.file_id

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO songs (title,file_id) VALUES (%s,%s)",
        (title,file_id)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"🎵 Song added\n\n{title}"
    )


# ---------- LEADERBOARD ----------

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT telegram_id FROM fans LIMIT 10")

    rows = cur.fetchall()

    conn.close()

    text = "🏆 BAZRAGOD SUPPORTERS\n\n"

    for r in rows:
        text += f"{r[0]}\n"

    await update.message.reply_text(text)


# ---------- WISDOM ----------

async def wisdom(update: Update, context: ContextTypes.DEFAULT_TYPE):

    quotes = [
        "He who conquers himself is the mightiest warrior.",
        "Never outshine the master.",
        "Discipline equals freedom.",
        "Appear weak when you are strong.",
    ]

    await update.message.reply_text(
        f"👑 Royal Wisdom\n\n{random.choice(quotes)}"
    )


# ---------- FITNESS ----------

async def fitness(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = """
🏋 BAZRAGOD FITNESS

Pushups 50
Squats 50
Run 2km

Meal:
Eggs
Rice
Chicken
Fruit
"""

    await update.message.reply_text(msg)


# ---------- SUPPORT ----------

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = """
💰 SUPPORT BAZRAGOD

CashApp
https://cash.app/$BAZRAGOD

PayPal
Bazragod1@gmail.com
"""

    await update.message.reply_text(msg)


# ---------- SOCIAL ----------

async def social(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = """
🌐 BAZRAGOD SOCIAL

Instagram
https://www.instagram.com/bazragod_timeless

TikTok
https://www.tiktok.com/@bazragod_official

YouTube
https://youtube.com/@bazragodmusictravelandleis8835

X
https://x.com/toligarch65693
"""

    await update.message.reply_text(msg)


# ---------- MERCH ----------

async def merch(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👕 PARISH 14\n\nOfficial BAZRAGOD merch coming soon."
    )


# ---------- MINI APP ----------

async def open_player(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎧 Open BazraGod Player",
                    web_app=WebAppInfo(url="https://miserbot.vercel.app")
                )
            ]
        ]
    )

    await update.message.reply_text(
        "🚀 Launch BAZRAGOD Player",
        reply_markup=keyboard
    )


# ---------- ROUTER ----------

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🎵 Music":
        await music(update, context)

    elif text == "📻 BazraGod Radio":
        await radio(update, context)

    elif text == "🏆 Leaderboard":
        await leaderboard(update, context)

    elif text == "💰 Support Artist":
        await support(update, context)

    elif text == "🌐 Social":
        await social(update, context)

    elif text == "👕 Parish 14":
        await merch(update, context)

    elif text == "👑 Wisdom":
        await wisdom(update, context)

    elif text == "🏋 Fitness":
        await fitness(update, context)

    elif text == "🚀 Open Player":
        await open_player(update, context)


# ---------- TELEGRAM APP ----------

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(play_song))
telegram_app.add_handler(MessageHandler(filters.AUDIO, upload_song))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))


# ---------- WEBHOOK ----------

@app_flask.route("/webhook", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok"


# ---------- START ----------

if __name__ == "__main__":

    init_db()

    telegram_app.bot.set_webhook(WEBHOOK_URL)

    print("MISERBOT V2000 RUNNING")

    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
