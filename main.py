import os
import logging
import psycopg2
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------------------------
# Environment variables
# ---------------------------
BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OWNER_ID = os.getenv("OWNER_ID")

# ---------------------------
# Database connection
# ---------------------------
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS fans (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE,
    username TEXT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()

# ---------------------------
# Keyboard
# ---------------------------
keyboard = ReplyKeyboardMarkup(
    [
        ["🎵 Music", "🌍 Radar"],
        ["✈️ Travel", "🏆 Fans"]
    ],
    resize_keyboard=True
)

# ---------------------------
# Commands
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    try:
        cur.execute(
            "INSERT INTO fans (user_id, username) VALUES (%s,%s) ON CONFLICT (user_id) DO NOTHING",
            (user.id, user.username)
        )
        conn.commit()
    except:
        pass

    await update.message.reply_text(
        "👑 MiserBot v600 activated.\n\nWelcome to the command system.",
        reply_markup=keyboard
    )


async def fans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur.execute("SELECT COUNT(*) FROM fans")
    count = cur.fetchone()[0]

    await update.message.reply_text(f"👥 Total Fans: {count}")


async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 Your music catalog will appear here soon.\nFans will be able to stream directly."
    )


async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌍 Fan radar system scanning cities..."
    )


async def travel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✈️ Travel planner loading..."
    )


# ---------------------------
# Message router
# ---------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🏆 Fans":
        await fans(update, context)

    elif text == "🎵 Music":
        await music(update, context)

    elif text == "🌍 Radar":
        await radar(update, context)

    elif text == "✈️ Travel":
        await travel(update, context)


# ---------------------------
# Main
# ---------------------------
def main():

    print("👑 MiserBot starting...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Permanent Telegram conflict fix
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
