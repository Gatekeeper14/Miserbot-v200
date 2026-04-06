import os
import random
import psycopg2
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

ADMIN_ID = 8741545426


# ---------------- DATABASE ----------------

def get_db():
    return psycopg2.connect(DATABASE_URL)


def init_db():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans (
        telegram_id BIGINT PRIMARY KEY,
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
        ["👑 Wisdom", "🏋 Fitness"]
    ],
    resize_keyboard=True
)


# ---------------- START ----------------

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
        "👑 Welcome to MISERBOT V1500\n\nOfficial BAZRAGOD Music Platform",
        reply_markup=menu
    )


# ---------------- MUSIC MENU ----------------

async def music_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, title FROM songs ORDER BY id")

    rows = cur.fetchall()

    conn.close()

    if not rows:

        await update.message.reply_text("No songs uploaded yet.")
        return

    keyboard = []

    for r in rows:

        keyboard.append(
            [InlineKeyboardButton(f"▶ {r[1]}", callback_data=str(r[0]))]
        )

    await update.message.reply_text(
        "🎧 BAZRAGOD PLAYLIST",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- PLAY SONG ----------------

async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    song_id = query.data

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT title, file_id FROM songs WHERE id=%s",
        (song_id,)
    )

    song = cur.fetchone()

    conn.close()

    if song:

        await query.message.reply_audio(
            song[1],
            caption=f"🎵 {song[0]}"
        )


# ---------------- RADIO ----------------

async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT title, file_id FROM songs ORDER BY RANDOM() LIMIT 1")

    song = cur.fetchone()

    conn.close()

    if song:

        await update.message.reply_audio(
            song[1],
            caption=f"📻 BazraGod Radio\n\n{song[0]}"
        )


# ---------------- SONG UPLOAD (ADMIN) ----------------

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
        "INSERT INTO songs (title, file_id) VALUES (%s,%s)",
        (title, file_id)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"🎵 Song added\n\n{title}"
    )


# ---------------- LEADERBOARD ----------------

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT telegram_id, points FROM fans ORDER BY points DESC LIMIT 10"
    )

    rows = cur.fetchall()

    conn.close()

    text = "🏆 TOP SUPPORTERS\n\n"

    for r in rows:

        text += f"{r[0]} — {r[1]} pts\n"

    await update.message.reply_text(text)


# ---------------- WISDOM ----------------

async def wisdom(update: Update, context: ContextTypes.DEFAULT_TYPE):

    quotes = [
        "He who conquers himself is the mightiest warrior.",
        "Never outshine the master.",
        "Discipline equals freedom.",
        "Appear weak when you are strong.",
        "Control your mind or it will control you."
    ]

    await update.message.reply_text(
        f"👑 Royal Wisdom\n\n{random.choice(quotes)}"
    )


# ---------------- FITNESS ----------------

async def fitness(update: Update, context: ContextTypes.DEFAULT_TYPE):

    plan = """
🏋 BAZRAGOD FITNESS

Morning
Pushups 50
Squats 50
Run 2km

Meal
Eggs
Rice
Chicken
Fruit
"""

    await update.message.reply_text(plan)


# ---------------- SUPPORT ----------------

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = """
💰 SUPPORT BAZRAGOD

CashApp
https://cash.app/$BAZRAGOD

PayPal
Bazragod1@gmail.com
"""

    await update.message.reply_text(msg)


# ---------------- SOCIAL ----------------

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


# ---------------- MERCH ----------------

async def merch(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👕 PARISH 14\n\nOfficial BAZRAGOD merchandise coming soon."
    )


# ---------------- ROUTER ----------------

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🎵 Music":

        await music_menu(update, context)

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


# ---------------- MAIN ----------------

def main():

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(play_song))

    app.add_handler(MessageHandler(filters.AUDIO, upload_song))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

    print("MISERBOT V1500 RUNNING")

    app.run_polling()


if __name__ == "__main__":
    main()
