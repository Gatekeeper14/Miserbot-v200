import os
import random
import psycopg2
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

ADMIN_ID = 8741545426


# ---------- DATABASE ----------

def get_db():
    return psycopg2.connect(DATABASE_URL)


def init_db():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS songs (
        id SERIAL PRIMARY KEY,
        title TEXT,
        file_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# ---------- MAIN MENU ----------

menu = ReplyKeyboardMarkup(
    [
        ["🎵 Music", "📻 BazraGod Radio"],
        ["💰 Support Artist", "🏆 Top Fans"],
        ["👕 Parish 14", "🌐 Social"]
    ],
    resize_keyboard=True
)


# ---------- START ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO fans (telegram_id) VALUES (%s) ON CONFLICT DO NOTHING",
        (user_id,)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "👑 Welcome to MISERBOT V975\n\nOfficial BAZRAGOD Music System",
        reply_markup=menu
    )


# ---------- MUSIC MENU ----------

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

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎧 BAZRAGOD PLAYLIST\n\nTap a song:",
        reply_markup=reply_markup
    )


# ---------- PLAY SONG BUTTON ----------

async def play_song_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    song_id = query.data

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT file_id, title FROM songs WHERE id=%s",
        (song_id,)
    )

    song = cur.fetchone()

    conn.close()

    if song:

        await query.message.reply_audio(
            song[0],
            caption=f"🎵 {song[1]}"
        )


# ---------- RADIO ----------

async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT file_id, title FROM songs ORDER BY RANDOM() LIMIT 1")

    song = cur.fetchone()

    conn.close()

    if song:

        await update.message.reply_audio(
            song[0],
            caption=f"📻 BazraGod Radio\n{song[1]}"
        )

    else:

        await update.message.reply_text("No songs available yet.")


# ---------- SUPPORT ----------

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "💰 Support Independent Artist BAZRAGOD\n\n"
        "Cash App\n"
        "https://cash.app/$BAZRAGOD\n\n"
        "PayPal\n"
        "Bazragod1@gmail.com"
    )

    await update.message.reply_text(text)


# ---------- FAN COUNT ----------

async def fans(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM fans")

    count = cur.fetchone()[0]

    conn.close()

    await update.message.reply_text(
        f"🏆 Total BazraGod Fans: {count}"
    )


# ---------- MERCH ----------

async def merch(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👕 PARISH 14\n\nOfficial BAZRAGOD merchandise coming soon."
    )


# ---------- SOCIAL ----------

async def social(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "🌐 Follow BAZRAGOD\n\n"
        "Instagram\n"
        "https://www.instagram.com/bazragod_timeless\n\n"
        "TikTok\n"
        "https://www.tiktok.com/@bazragod_official\n\n"
        "YouTube\n"
        "https://youtube.com/@bazragodmusictravelandleis8835\n\n"
        "X\n"
        "https://x.com/toligarch65693"
    )

    await update.message.reply_text(text)


# ---------- ADMIN SONG UPLOAD ----------

async def save_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

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
        "INSERT INTO songs (title, file_id) VALUES (%s, %s)",
        (title, file_id)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"Song added to catalog\n\n{title}"
    )


# ---------- ROUTER ----------

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🎵 Music":

        await music_menu(update, context)

    elif text == "📻 BazraGod Radio":

        await radio(update, context)

    elif text == "💰 Support Artist":

        await support(update, context)

    elif text == "🏆 Top Fans":

        await fans(update, context)

    elif text == "👕 Parish 14":

        await merch(update, context)

    elif text == "🌐 Social":

        await social(update, context)


# ---------- MAIN ----------

def main():

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(play_song_button))

    app.add_handler(MessageHandler(filters.AUDIO, save_song))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

    print("MISERBOT V975 RUNNING")

    app.run_polling()


if __name__ == "__main__":
    main()
