import os
import psycopg2
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
DATABASE_URL = os.getenv("DATABASE_URL")

# ---------------- DATABASE ---------------- #

def get_db():
    if not DATABASE_URL:
        return None

    url = DATABASE_URL

    # Railway sometimes uses postgres:// instead of postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    try:
        conn = psycopg2.connect(url, sslmode="require")
        return conn
    except Exception as e:
        print("DB connection error:", e)
        return None


def init_db():
    conn = get_db()
    if not conn:
        print("Database not ready")
        return

    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE
    )
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("Database initialized")


# ---------------- COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["🎵 Music"],
        ["🌍 Radar"],
        ["✈️ Travel"],
        ["🏆 Fans"]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "🛸 MiserBot v200 activated\n\nWelcome to the command system.",
        reply_markup=reply_markup
    )

    conn = get_db()
    if conn:
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO fans (telegram_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (update.effective_user.id,)
        )

        conn.commit()
        cur.close()
        conn.close()


# ---------------- BUTTONS ---------------- #

async def fans(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()

    if not conn:
        await update.message.reply_text("Fan database not connected yet.")
        return

    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM fans")
    count = cur.fetchone()[0]

    await update.message.reply_text(f"👥 Total Fans: {count}")

    cur.close()
    conn.close()


async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Music store coming online soon.")


async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌍 Industry radar scanning cities soon.")


async def travel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✈️ Travel planner loading.")


# ---------------- ROUTER ---------------- #

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


# ---------------- MAIN ---------------- #

def main():

    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("MiserBot running")

    app.run_polling()


if __name__ == "__main__":
    main()
