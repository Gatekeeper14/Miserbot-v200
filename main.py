import os
import random
import psycopg2
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE
    )
    """)

    conn.commit()
    conn.close()


# ---------------- MUSIC LIBRARY ----------------

songs = {

    "1": "CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA",  # Boom Boom

    "2": "CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA",  # Mini 14

    "3": "CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA",  # Gunman

    "4": "CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA",  # Trap

    "5": "CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA",  # Fear

    "6": "CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA",  # Summer Time

    "7": "CQACAgEAAxkBAAO9adMbBDzajJrOcGNb6gVyZmjEXTYAAvwIAAI1Z5hGr3nvGz4AAYjbOwQ",  # Real Gold

    "8": "CQACAgEAAxkBAAPFadMdgVBA0MIwyLNyU8mO5-djfawAAgQJAAI1Z5hGYmzehzRMIZY7BA",  # Facebook Lust

    "9": "CQACAgEAAxkBAAPJadMeaMExYAvnDv8gswXyUgOMwpsAAgcJAAI1Z5hGxeKB46IBYZg7BA",  # Mi Alone

    "10": "CQACAgEAAxkBAAPPadMgBMh10TStncJQXpkyD0mJYM8AAgoJAAI1Z5hG10QJbSDmTyM7BA"  # Bubbie Fi Mi

}


# ---------------- MENU ----------------

menu = ReplyKeyboardMarkup(
    [
        ["🎵 Music", "📻 BazraGod Radio"],
        ["💰 Support Artist", "🏆 Top Fans"],
        ["👕 Parish 14", "🌐 Social"]
    ],
    resize_keyboard=True
)


# ---------------- START ----------------

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
        "👑 Welcome to MISERBOT V900\n\nThe Official BAZRAGOD Fan System",
        reply_markup=menu
    )


# ---------------- MUSIC MENU ----------------

async def music_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "🎵 BAZRAGOD MUSIC\n\n"
        "1 Boom Boom\n"
        "2 Mini 14\n"
        "3 Gunman\n"
        "4 Trap\n"
        "5 Fear\n"
        "6 Summer Time\n"
        "7 Real Gold\n"
        "8 Facebook Lust\n"
        "9 Mi Alone\n"
        "10 Bubbie Fi Mi\n\n"
        "Send the number to play."
    )

    await update.message.reply_text(text)


# ---------------- RADIO ----------------

async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    song = random.choice(list(songs.values()))

    await update.message.reply_audio(
        song,
        caption="📻 BazraGod Radio"
    )


# ---------------- SUPPORT ----------------

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


# ---------------- FAN COUNT ----------------

async def fans(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM fans")

    count = cur.fetchone()[0]

    conn.close()

    await update.message.reply_text(
        f"🏆 Total BazraGod Fans: {count}"
    )


# ---------------- MERCH ----------------

async def merch(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👕 PARISH 14\n\nOfficial BAZRAGOD merchandise coming soon."
    )


# ---------------- SOCIAL ----------------

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


# ---------------- PLAY SONG ----------------

async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text in songs:

        await update.message.reply_audio(songs[text])


# ---------------- ROUTER ----------------

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


# ---------------- MAIN ----------------

def main():

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

    print("MISERBOT V900 RUNNING")

    app.run_polling()


if __name__ == "__main__":
    main()
