import os
import psycopg2
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

# ---------------- DATABASE ---------------- #

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
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
    cur.close()
    conn.close()

def add_fan(user_id, username):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO fans (user_id, username) VALUES (%s,%s) ON CONFLICT (user_id) DO NOTHING",
        (user_id, username)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_fan_count():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM fans")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

def get_all_fans():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM fans")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return [u[0] for u in users]

# ---------------- KEYBOARD ---------------- #

keyboard = ReplyKeyboardMarkup(
    [
        ["🎵 Music"],
        ["🌍 Radar"],
        ["✈️ Travel"],
        ["🏆 Fans"]
    ],
    resize_keyboard=True
)

# ---------------- COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_fan(user.id, user.username)

    await update.message.reply_text(
        "🛸 MiserBot v200 activated\n\nWelcome to the command system.",
        reply_markup=keyboard
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage:\n/broadcast message")
        return

    message = " ".join(context.args)
    fans = get_all_fans()

    sent = 0
    for user_id in fans:
        try:
            await context.bot.send_message(user_id, message)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"Broadcast sent to {sent} fans.")

# ---------------- BUTTON HANDLER ---------------- #

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🏆 Fans":
        count = get_fan_count()
        await update.message.reply_text(f"👥 Total Fans: {count}")

    elif text == "🎵 Music":
        await update.message.reply_text("Music store coming online soon.")

    elif text == "🌍 Radar":
        await update.message.reply_text("Industry radar scanning cities soon.")

    elif text == "✈️ Travel":
        await update.message.reply_text("Travel planner loading.")

# ---------------- MAIN ---------------- #

def main():
    init_db()
    print("Database initialized")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("MiserBot running")
    app.run_polling()

if __name__ == "__main__":
    main()
