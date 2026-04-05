import os
import psycopg2
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
PORT = int(os.environ.get("PORT", 8000))

app = Flask(__name__)

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()


# ---------------- DATABASE ----------------

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


# ---------------- COMMANDS ----------------

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


async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Music catalog loading...")


async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌍 Radar scanning cities...")


async def travel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✈️ Travel planner loading...")


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


# ---------------- ROUTER ----------------

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


# ---------------- HANDLERS ----------------

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))


# ---------------- WEBHOOK ----------------

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok"


# ---------------- START ----------------

if __name__ == "__main__":

    init_db()

    telegram_app.initialize()

    RAILWAY_URL = os.getenv("RAILWAY_STATIC_URL")

    if RAILWAY_URL:
        webhook_url = f"https://{RAILWAY_URL}/{BOT_TOKEN}"
        telegram_app.bot.set_webhook(webhook_url)

    print("MiserBot webhook running...")

    app.run(host="0.0.0.0", port=PORT)
