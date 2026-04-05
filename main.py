import os
import asyncio
import requests
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import psycopg2

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

main_keyboard = ReplyKeyboardMarkup(
    [
        ["🎵 Music", "🌍 Radar"],
        ["✈️ Travel", "🏆 Fans"]
    ],
    resize_keyboard=True
)

location_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("📍 Share Location", request_location=True)]],
    resize_keyboard=True,
    one_time_keyboard=True
)

def get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans(
        id SERIAL PRIMARY KEY
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS radar(
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        latitude FLOAT,
        longitude FLOAT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()


def get_city(lat, lon):

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        r = requests.get(url, headers={"User-Agent": "MiserBot"})
        data = r.json()

        city = data["address"].get("city") or data["address"].get("town") or data["address"].get("village") or "Unknown city"
        state = data["address"].get("state", "")

        return f"{city}, {state}"

    except:
        return "Unknown location"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("INSERT INTO fans DEFAULT VALUES")

    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text(
        "👑 Welcome to MiserBot\n\nYour fan network is active.",
        reply_markup=main_keyboard
    )


async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = """
🎵 MiserBot Music

1️⃣ Stream Music
2️⃣ Support Artist
3️⃣ PARISH 14 Merch
4️⃣ Share with Friends
"""

    await update.message.reply_text(msg)


async def travel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT latitude, longitude FROM radar
        LIMIT 10
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if not rows:
        await update.message.reply_text("✈️ No travel data yet.\nUse Radar to build the fan map.")
        return

    cities = {}

    for lat, lon in rows:
        city = get_city(lat, lon)
        cities[city] = cities.get(city, 0) + 1

    msg = "✈️ Tour Intelligence\n\n"

    for city, count in cities.items():
        msg += f"{city} — {count} fans\n"

    await update.message.reply_text(msg)


async def fans(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM fans")
    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    await update.message.reply_text(f"🏆 Total Fans: {count}")


async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🌍 Share your location to scan for nearby fans",
        reply_markup=location_keyboard
    )


async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user
    lat = update.message.location.latitude
    lon = update.message.location.longitude

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO radar (user_id, latitude, longitude) VALUES (%s,%s,%s)",
        (user.id, lat, lon)
    )

    cur.execute("SELECT COUNT(*) FROM radar")
    fans = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    city = get_city(lat, lon)

    msg = f"""
📍 Location saved

🌎 {city}
👥 {fans} fans detected in the network

🔥 Fan network growing
"""

    await update.message.reply_text(msg, reply_markup=main_keyboard)


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


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))
telegram_app.add_handler(MessageHandler(filters.LOCATION, location_handler))


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():

    update = Update.de_json(request.get_json(force=True), telegram_app.bot)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.process_update(update))

    return "ok"


@app.route("/")
def home():
    return "MiserBot running"


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(host="0.0.0.0", port=port)
