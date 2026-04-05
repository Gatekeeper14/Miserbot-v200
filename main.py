import os
import psycopg2
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# -------- DATABASE -------- #

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

# -------- AI HELPER -------- #

def ask_ai(prompt):

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant for musicians helping with travel planning, music industry research, and music promotion."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# -------- KEYBOARD -------- #

keyboard = ReplyKeyboardMarkup(
    [
        ["🎵 Music"],
        ["🌍 Radar"],
        ["✈️ Travel"],
        ["🏆 Fans"]
    ],
    resize_keyboard=True
)

# -------- COMMANDS -------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    add_fan(user.id, user.username)

    await update.message.reply_text(
        "🛸 MiserBot v201 online\n\nWelcome to the command system.",
        reply_markup=keyboard
    )

# -------- BUTTON HANDLER -------- #

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🏆 Fans":

        count = get_fan_count()
        await update.message.reply_text(f"👥 Total Fans: {count}")

    elif text == "🎵 Music":

        answer = ask_ai(
            "Give ideas for promoting a new music release for an independent artist."
        )

        await update.message.reply_text(answer)

    elif text == "🌍 Radar":

        answer = ask_ai(
            "List important music industry cities and why artists should focus on them."
        )

        await update.message.reply_text(answer)

    elif text == "✈️ Travel":

        answer = ask_ai(
            "Create a simple travel plan for a musician touring 3 US cities with budget advice."
        )

        await update.message.reply_text(answer)

# -------- MAIN -------- #

def main():

    init_db()
    print("Database initialized")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("MiserBot running")

    app.run_polling()

if __name__ == "__main__":
    main()
