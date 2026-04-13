import os
import random
import threading
import time
import stripe
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# =============================
# ENV VARIABLES
# =============================

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
RADIO_CHANNEL_ID = os.getenv("RADIO_CHANNEL_ID")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

stripe.api_key = STRIPE_SECRET_KEY

SUPPORT_LINK = "https://buy.stripe.com/6oUeVf0Ml7Iv6Wg1PM5Rm00"
CONTACT_EMAIL = "miserbot.ai@gmail.com"

# =============================
# TELEGRAM HELPERS
# =============================

def send_message(chat_id, text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })


def send_audio(chat_id, file_id):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"

    requests.post(url, json={
        "chat_id": chat_id,
        "audio": file_id
    })


# =============================
# ENTRY SYSTEM
# =============================

ENTRY_AUDIO = "CQACAgEAAxkBAAEdA9Jp2WRb5KP00P7uDWZQhizBRaY0nAACfwcAAmxuyUaMnHhvbPnphTsE"
ENTRY_CONFIRM_AUDIO = "CQACAgEAAxkBAAEdBA5p2WpPQ99yqaSeaKFJ1e2byrh1fwACjAcAAmxuyUYlAZdP-EiH0zsE"

def spaceship_entry(chat_id):

    send_audio(chat_id, ENTRY_AUDIO)

    send_message(chat_id,
"""
🚀 MISERBOT ENTRY SYSTEM

Approaching Miserbot AI Radio Station.

Type ENTER to access the station.
""")


def enter_station(chat_id):

    send_audio(chat_id, ENTRY_CONFIRM_AUDIO)

    send_message(chat_id,
f"""
WELCOME TO MISERBOT RADIO 🔊

Independent Artists AI Music Ops

Owner: BAZRAGOD
Contact: {CONTACT_EMAIL}

Support Miserbot:
{SUPPORT_LINK}

Commands
/radio
/beat
/drop
""")


# =============================
# SONG SEEDS
# =============================

SONGS = [

("Boom Boom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("Mini 14","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("Gunman","CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
("Trap Master","CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
("Fear","CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA"),
("Summertime","CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA"),
("Real Gold","CQACAgEAAxkBAAO9adMbBDzajJrOcGNb6gVyZmjEXTYAAvwIAAI1Z5hGr3nvGz4AAYjbOwQ"),
("Facebook Lust","CQACAgEAAxkBAAOzadMY-pj_rWBB5wrRP6Nfymv4q6EAAvcIAAI1Z5hG4SGuftZqhPY7BA"),
("Mi Alone","CQACAgEAAxkBAAPJadMeaMExYAvnDv8gswXyUgOMwpsAAgcJAAI1Z5hGxeKB46IBYZg7BA"),
("Bubble Fi Mi","CQACAgEAAxkBAAPPadMgBMh10TStncJQXpkyD0mJYM8AAgoJAAI1Z5hG10QJbSDmTyM7BA"),
("Natural Pussy","CQACAgEAAxkBAAO1adMZtjgiRqYxrOFbE3KOCNxVcxQAAvgIAAI1Z5hGm8QmWqNIojg7BA"),
("Fraid Ah Yuh","CQACAgEAAxkBAAO3adMZ_P5y2OoXlyY0XpO_fiPiahMAAvkIAAI1Z5hGgMZ1tOmyhjA7BA")

]

# =============================
# BEATS
# =============================

BEATS = [

("BazraGod Beat","CQACAgEAAxkBAAEdA-Zp2Wc0fY3nXOytykCPAAHjrr27BPgAAoIHAAJsbslGBBD2WfxSy987BA"),
("Stamp Dem Out","CQACAgEAAxkBAAEdA-hp2Wc0xqwDQ_PgXmy_9BMKWOgq7wAChAcAAmxuyUa3R76448OH-zsE"),
("Thing Dem Work","CQACAgEAAxkBAAEdA-lp2Wc0PDZ4Hl_TDsO61qPqODq6WwAChQcAAmxuyUbCwPZz3etTETsE")

]

# =============================
# DROPS
# =============================

DROPS = [

("BazraGod Drop","CQACAgEAAxkBAAEdBAxp2WpPO2qN05UvBgqyRxxlKSdITAACigcAAmxuyUZ_p1-vZV720TsE"),
("BazraGod Energy","CQACAgEAAxkBAAEdBBJp2WpPVvtkxNj3s50URaj7tGmP3AACkAcAAmxuyUaoKg1vw-BhfDsE")

]

# =============================
# RADIO FUNCTIONS
# =============================

def play_song(chat_id):

    song = random.choice(SONGS)
    send_message(chat_id, f"🎵 {song[0]}")
    send_audio(chat_id, song[1])


def play_beat(chat_id):

    beat = random.choice(BEATS)
    send_message(chat_id, f"🥁 {beat[0]}")
    send_audio(chat_id, beat[1])


def play_drop(chat_id):

    drop = random.choice(DROPS)
    send_message(chat_id, f"⚡ {drop[0]}")
    send_audio(chat_id, drop[1])


# =============================
# 24/7 AUTO RADIO
# =============================

def radio_loop():

    while True:

        if RADIO_CHANNEL_ID:

            play_beat(RADIO_CHANNEL_ID)
            time.sleep(15)

            play_song(RADIO_CHANNEL_ID)
            time.sleep(120)

            play_drop(RADIO_CHANNEL_ID)
            time.sleep(20)


radio_thread = threading.Thread(target=radio_loop)
radio_thread.daemon = True
radio_thread.start()


# =============================
# STRIPE WEBHOOK
# =============================

@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():

    payload = request.data
    sig = request.headers.get("Stripe-Signature")

    try:

        event = stripe.Webhook.construct_event(
            payload,
            sig,
            STRIPE_WEBHOOK_SECRET
        )

    except Exception:

        return "invalid", 400

    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        email = session.get("customer_details",{}).get("email")
        amount = session.get("amount_total")

        send_message(
            OWNER_ID,
            f"💰 Payment Received\n{email}\n${amount/100}"
        )

    return jsonify(success=True)


# =============================
# TELEGRAM WEBHOOK
# =============================

@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():

    data = request.json

    if "message" not in data:
        return jsonify(ok=True)

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text","").lower()

    if text == "/start":
        spaceship_entry(chat_id)

    elif text == "enter":
        enter_station(chat_id)
        play_song(chat_id)

    elif text == "/radio":
        play_song(chat_id)

    elif text == "/beat":
        play_beat(chat_id)

    elif text == "/drop":
        play_drop(chat_id)

    return jsonify(ok=True)


# =============================
# SERVER ROOT
# =============================

@app.route("/")
def home():
    return "Miserbot AI Radio Online"


# =============================
# START SERVER
# =============================

if __name__ == "__main__":

    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0", port=port)
