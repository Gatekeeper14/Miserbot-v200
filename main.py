import os
import psycopg2
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ENV VARIABLES
BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")


# DATABASE CONNECTION
def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans(
        user_id TEXT PRIMARY KEY
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["🎵 Music", "🌍 Radar"],
        ["✈️ Travel", "🏆 Fans"]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👑 MiserBot Online\n\nWelcome to the fan command center.",
        reply_markup=reply_markup
    )


# MUSIC
async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Music catalog loading...")


# RADAR
async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌍 Radar scanning cities...")


# TRAVEL
async def travel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✈️ Travel planner loading...")


# FANS
async def fans(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_connection()
    cur = conn.cursor()

    user_id = str(update.effective_user.id)

    cur.execute(
        "INSERT INTO fans (user_id) VALUES (%s) ON CONFLICT DO NOTHING",
        (user_id,)
    )

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM fans")
    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    await update.message.reply_text(f"👥 Total Fans: {total}")


# ROUTER
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🎵 Music":
        await music(update, context)

    elif text == "🌍 Radar":
        await radar(update, context)

    elif text == "✈️ Travel":
        await travel(update, context)

    elif text == "🏆 Fans":
        await fans(update, context)


# MAIN
def main():

    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

    print("MiserBot running...")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
