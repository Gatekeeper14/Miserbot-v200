import os
import psycopg2
import google.generativeai as genai
from openai import OpenAI
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-pro")


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


# ---------------- AI FUNCTIONS ---------------- #

def ask_openai(prompt):

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You help independent musicians grow their careers."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content


def ask_gemini(prompt):

    response = gemini_model.generate_content(prompt)
    return response.text


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
        "🛸 MiserBot v201 online\n\nWelcome to the command system.",
        reply_markup=keyboard
    )


# ---------------- BUTTON HANDLER ---------------- #

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🏆 Fans":

        count = get_fan_count()
        await update.message.reply_text(f"👥 Total Fans: {count}")


    elif text == "🎵 Music":

        answer = ask_openai(
            "Give promotion ideas for a new music release from an independent artist."
        )

        await update.message.reply_text(answer)


    elif text == "🌍 Radar":

        answer = ask_gemini(
            "List important music industry cities and what opportunities they offer artists."
        )

        await update.message.reply_text(answer)


    elif text == "✈️ Travel":

        answer = ask_openai(
            "Create a simple tour travel plan for a musician visiting three US cities."
        )

        await update.message.reply_text(answer)


# ---------------- MAIN ---------------- #

def main():

    init_db()
    print("Database initialized")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("MiserBot running")

    app.run_polling()


if __name__ == "__main__":
    main()
