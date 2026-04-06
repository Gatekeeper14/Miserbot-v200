import os
import random
import psycopg2
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
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

    conn.commit()
    conn.close()


# ---------- MUSIC LIBRARY ----------

songs = {

    "1": "CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA",  # Boom Boom

    "2": "CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA",  # Mini 14

    "3": "CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA",  # Gunman

    "4": "CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA",  # Trap

    "5": "CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA",  # Fear

    "6": "CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA",  # Summer Time

    "7": "CQACAgEAAxkBAAO9adMbBDzajJrOcGNb6gVyZmjEXTYAAvwIAAI1Z5hGr3nvGz4AAYjbOwQ",  # Real Gold

    "8": "CQACAgEAAxkBAAOzadMY-pj_rWBB5wrRP6Nfymv4q6EAAvcIAAI1Z5hG4SGuftZqhPY7BA",  # Facebook Lust (FIXED)

    "9": "CQACAgEAAxkBAAPJadMeaMExYAvnDv8gswXyUgOMwpsAAgcJAAI1Z5hGxeKB46IBYZg7BA",  # Mi Alone

    "10": "CQACAgEAAxkBAAPPadMgBMh10TStncJQXpkyD0mJYM8AAgoJAAI1Z5hG10QJbSDmTyM7BA"  # Bubbie Fi Mi
}


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
        "👑 Welcome to MISERBOT V950\n\nThe Official BAZRAGOD Fan System",
        reply_markup=menu
    )


# ---------- MUSIC MENU (BUTTON PLAYER) ----------

async def music_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("▶ Boom Boom", callback_data="1")],
        [InlineKeyboardButton("▶ Mini 14", callback_data="2")],
        [InlineKeyboardButton("▶ Gunman", callback_data="3")],
        [InlineKeyboardButton("▶ Trap", callback_data="4")],
        [InlineKeyboardButton("▶ Fear", callback_data="5")],
        [InlineKeyboardButton("▶ Summer Time", callback_data="6")],
        [InlineKeyboardButton("▶ Real Gold", callback_data="7")],
        [InlineKeyboardButton("▶ Facebook Lust", callback_data="8")],
        [InlineKeyboardButton("▶ Mi Alone", callback_data="9")],
        [InlineKeyboardButton("▶ Bubbie Fi Mi", callback_data="10")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎵 BAZRAGOD MUSIC\n\nTap a song to play:",
        reply_markup=reply_markup
    )


# ---------- BUTTON SONG PLAYER ----------

async def button_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    song_number = query.data

    if song_number in songs:

        await query.message.reply_audio(
            songs[song_number]
        )


# ---------- RADIO ----------

async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    song = random.choice(list(songs.values()))

    await update.message.reply_audio(
        song,
        caption="📻 BazraGod Radio"
    )


# ---------- SUPPORT ----------

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "💰 Support Independent Artist BAZRAGOD\n\n"
        "Cash App\n"
        "https://cash.app/$BAZRAGOD\n\n"
        "PayPal\n"
        "Bazragod1@gmail.com\n\n"
        "Every contribution supports music and travel."
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


# ---------- NUMBER SONG PLAY ----------

async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text in songs:

        await update.message.reply_audio(songs[text])


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

    else:

        await play_song(update, context)


# ---------- MAIN ----------

def main():

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(button_song))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

    print("MISERBOT V950 RUNNING")

    app.run_polling()


if __name__ == "__main__":
    main()
