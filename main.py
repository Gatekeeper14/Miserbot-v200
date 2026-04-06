import os
import asyncio
import random
import requests
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import psycopg2

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

keyboard = ReplyKeyboardMarkup(
[
["🎵 Music","🌍 Radar"],
["✈️ Travel","🏆 Fans"],
["👑 Wisdom","💪 Workout"],
["🥗 Meals","👕 PARISH 14"]
],
resize_keyboard=True
)

location_keyboard = ReplyKeyboardMarkup(
[[KeyboardButton("📍 Share Location", request_location=True)]],
resize_keyboard=True,
one_time_keyboard=True
)

stoic_quotes = [
"Waste no more time arguing what a good man should be. Be one. — Marcus Aurelius",
"He who conquers himself is the mightiest warrior. — Confucius",
"Luck is what happens when preparation meets opportunity. — Seneca",
"Appear weak when you are strong. — Sun Tzu",
"Never outshine the master. — 48 Laws of Power"
]

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def get_city(lat,lon):

    try:
        url=f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        r=requests.get(url,headers={"User-Agent":"MiserBot"})
        data=r.json()

        city=data["address"].get("city") or data["address"].get("town") or data["address"].get("village")
        state=data["address"].get("state","")

        return f"{city}, {state}"

    except:
        return "Unknown location"

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    conn=get_conn()
    cur=conn.cursor()

    cur.execute("INSERT INTO fans DEFAULT VALUES")

    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text(
"👑 Welcome back BAZRAGOD\nYour kingdom system is active.",
reply_markup=keyboard
)

async def music(update:Update,context:ContextTypes.DEFAULT_TYPE):

    msg="""
🎵 MiserBot Music

1️⃣ Stream Music
2️⃣ Support Artist
3️⃣ PARISH 14 Merch
4️⃣ Share with Friends
"""
    await update.message.reply_text(msg)

async def wisdom(update:Update,context:ContextTypes.DEFAULT_TYPE):

    quote=random.choice(stoic_quotes)

    await update.message.reply_text(
f"""
👑 Wisdom for BAZRAGOD

{quote}
"""
)

async def workout(update:Update,context:ContextTypes.DEFAULT_TYPE):

    msg="""
💪 Kingdom Workout

Pushups — 50
Pullups — 20
Squats — 50
Run — 1 mile
Stretch

Discipline builds power.
"""

    await update.message.reply_text(msg)

async def meals(update:Update,context:ContextTypes.DEFAULT_TYPE):

    msg="""
🥗 Kingdom Nutrition

Breakfast
Eggs + fruit

Lunch
Chicken + rice + vegetables

Dinner
Steak or fish + greens

Hydrate all day.
"""

    await update.message.reply_text(msg)

async def parish(update:Update,context:ContextTypes.DEFAULT_TYPE):

    msg="""
👕 PARISH 14

Official brand of BAZRAGOD

Coming soon:
Hoodies
Caps
Streetwear
"""

    await update.message.reply_text(msg)

async def travel(update:Update,context:ContextTypes.DEFAULT_TYPE):

    conn=get_conn()
    cur=conn.cursor()

    cur.execute("SELECT latitude,longitude FROM radar")

    rows=cur.fetchall()

    cur.close()
    conn.close()

    cities={}

    for lat,lon in rows:

        city=get_city(lat,lon)
        cities[city]=cities.get(city,0)+1

    msg="✈️ Tour Intelligence\n\n"

    for city,count in cities.items():

        msg+=f"{city} — {count} fans\n"

    await update.message.reply_text(msg)

async def fans(update:Update,context:ContextTypes.DEFAULT_TYPE):

    conn=get_conn()
    cur=conn.cursor()

    cur.execute("SELECT COUNT(*) FROM fans")

    count=cur.fetchone()[0]

    cur.close()
    conn.close()

    await update.message.reply_text(f"🏆 Total Fans: {count}")

async def radar(update:Update,context:ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
"🌍 Share your location to scan for nearby fans",
reply_markup=location_keyboard
)

async def location_handler(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.message.from_user
    lat=update.message.location.latitude
    lon=update.message.location.longitude

    conn=get_conn()
    cur=conn.cursor()

    cur.execute(
"INSERT INTO radar (user_id,latitude,longitude) VALUES (%s,%s,%s)",
(user.id,lat,lon)
)

    cur.execute("SELECT COUNT(*) FROM radar")

    fans=cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    city=get_city(lat,lon)

    await update.message.reply_text(
f"""
📍 Location saved

🌎 {city}
👥 {fans} fans detected in the network

🔥 Fan network growing
""",
reply_markup=keyboard
)

async def router(update:Update,context:ContextTypes.DEFAULT_TYPE):

    text=update.message.text

    if text=="🎵 Music":
        await music(update,context)

    elif text=="🌍 Radar":
        await radar(update,context)

    elif text=="✈️ Travel":
        await travel(update,context)

    elif text=="🏆 Fans":
        await fans(update,context)

    elif text=="👑 Wisdom":
        await wisdom(update,context)

    elif text=="💪 Workout":
        await workout(update,context)

    elif text=="🥗 Meals":
        await meals(update,context)

    elif text=="👕 PARISH 14":
        await parish(update,context)

telegram_app.add_handler(CommandHandler("start",start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,router))
telegram_app.add_handler(MessageHandler(filters.LOCATION,location_handler))

@app.route(f"/{BOT_TOKEN}",methods=["POST"])
def webhook():

    update=Update.de_json(request.get_json(force=True),telegram_app.bot)

    loop=asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.process_update(update))

    return "ok"

@app.route("/")
def home():
    return "MiserBot running"

if __name__=="__main__":

    port=int(os.environ.get("PORT",8080))

    app.run(host="0.0.0.0",port=port)
