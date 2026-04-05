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
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print("Database connection failed:", e)
        return None


def init_db():
    conn = get_db()
    if not conn:
        print("Skipping DB init (no database connection)")
        return

    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE,
        username TEXT,
        points INT DEFAULT 0,
        joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


# ---------------- START ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    conn = get_db()

    if conn:
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (telegram_id, username) VALUES (%s,%s) ON CONFLICT DO NOTHING",
            (user.id, user.username)
        )

        conn.commit()
        cur.close()
        conn.close()

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


# ---------------- MENU ---------------- #

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🎵 Music":
        await update.message.reply_text("Music store coming online soon.")

    elif text == "🌍 Radar":
        await update.message.reply_text("Industry radar scanning cities soon.")

    elif text == "✈️ Travel":
        await update.message.reply_text("Travel planner loading.")

    elif text == "🏆 Fans":

        conn = get_db()

        if not conn:
            await update.message.reply_text("Fan database not connected yet.")
            return

        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]

        cur.close()
        conn.close()

        await update.message.reply_text(f"👥 Total Fans: {total}")


# ---------------- BROADCAST ---------------- #

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    conn = get_db()

    if not conn:
        await update.message.reply_text("Database not connected.")
        return

    message = " ".join(context.args)

    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users")
    users = cur.fetchall()

    for user in users:
        try:
            await context.bot.send_message(chat_id=user[0], text=message)
        except:
            pass

    cur.close()
    conn.close()

    await update.message.reply_text("Broadcast sent.")


# ---------------- MAIN ---------------- #

def main():

    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))

    print("MiserBot v200 running...")

    app.run_polling()


if __name__ == "__main__":
    main()
