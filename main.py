import os
import random
import time
import threading
import stripe
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
RADIO_CHANNEL_ID = os.getenv("RADIO_CHANNEL_ID")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

stripe.api_key = STRIPE_SECRET_KEY


# =========================
# SAFE TELEGRAM FUNCTIONS
# =========================

def send_message(chat_id, text):

    if not BOT_TOKEN:
        return

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        requests.post(url,json={
            "chat_id":chat_id,
            "text":text
        },timeout=10)

    except Exception as e:
        print("send_message error:",e)


def send_audio(chat_id,file_id):

    if not BOT_TOKEN:
        return

    try:

        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"

        requests.post(url,json={
            "chat_id":chat_id,
            "audio":file_id
        },timeout=15)

    except Exception as e:
        print("send_audio error:",e)



# =========================
# ENTRY AUDIO
# =========================

ENTRY_AUDIO="CQACAgEAAxkBAAEdA9Jp2WRb5KP00P7uDWZQhizBRaY0nAACfwcAAmxuyUaMnHhvbPnphTsE"

ENTRY_CONFIRM="CQACAgEAAxkBAAEdBA5p2WpPQ99yqaSeaKFJ1e2byrh1fwACjAcAAmxuyUYlAZdP-EiH0zsE"



# =========================
# SONG SEEDS
# =========================

SONGS=[

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



# =========================
# BEATS
# =========================

BEATS=[

("BazraGod Beat","CQACAgEAAxkBAAEdA-Zp2Wc0fY3nXOytykCPAAHjrr27BPgAAoIHAAJsbslGBBD2WfxSy987BA"),

("Stamp Dem Out","CQACAgEAAxkBAAEdA-hp2Wc0xqwDQ_PgXmy_9BMKWOgq7wAChAcAAmxuyUa3R76448OH-zsE"),

("Thing Dem Work","CQACAgEAAxkBAAEdA-lp2Wc0PDZ4Hl_TDsO61qPqODq6WwAChQcAAmxuyUbCwPZz3etTETsE")

]



# =========================
# DROPS
# =========================

DROPS=[

("BazraGod Drop","CQACAgEAAxkBAAEdBAxp2WpPO2qN05UvBgqyRxxlKSdITAACigcAAmxuyUZ_p1-vZV720TsE"),

("BazraGod Energy","CQACAgEAAxkBAAEdBBJp2WpPVvtkxNj3s50URaj7tGmP3AACkAcAAmxuyUaoKg1vw-BhfDsE")

]



# =========================
# RADIO FUNCTIONS
# =========================

def play_song(chat):

    song=random.choice(SONGS)

    send_message(chat,f"🎵 {song[0]}")
    send_audio(chat,song[1])


def play_beat(chat):

    beat=random.choice(BEATS)

    send_message(chat,f"🥁 {beat[0]}")
    send_audio(chat,beat[1])


def play_drop(chat):

    drop=random.choice(DROPS)

    send_message(chat,f"⚡ {drop[0]}")
    send_audio(chat,drop[1])



# =========================
# RADIO LOOP (SAFE)
# =========================

def radio_engine():

    while True:

        try:

            if not RADIO_CHANNEL_ID:
                time.sleep(60)
                continue

            play_beat(RADIO_CHANNEL_ID)
            time.sleep(15)

            play_song(RADIO_CHANNEL_ID)
            time.sleep(120)

            play_drop(RADIO_CHANNEL_ID)
            time.sleep(25)

        except Exception as e:

            print("radio error:",e)
            time.sleep(30)



# =========================
# TELEGRAM WEBHOOK
# =========================

@app.route("/telegram-webhook",methods=["POST"])

def telegram():

    data=request.json

    if "message" not in data:
        return jsonify(ok=True)

    chat=data["message"]["chat"]["id"]

    text=data["message"].get("text","").lower()

    if text=="/start":

        send_audio(chat,ENTRY_AUDIO)

        send_message(chat,
        "🚀 Miserbot Entry System\n\nType ENTER")

    elif text=="enter":

        send_audio(chat,ENTRY_CONFIRM)

        send_message(chat,"Welcome to Miserbot Radio")

        play_song(chat)

    elif text=="/radio":

        play_song(chat)

    elif text=="/beat":

        play_beat(chat)

    elif text=="/drop":

        play_drop(chat)

    return jsonify(ok=True)



# =========================
# STRIPE WEBHOOK
# =========================

@app.route("/stripe-webhook",methods=["POST"])

def stripe_hook():

    payload=request.data
    sig=request.headers.get("Stripe-Signature")

    try:

        event=stripe.Webhook.construct_event(
            payload,sig,STRIPE_WEBHOOK_SECRET)

    except Exception:

        return "invalid",400

    if event["type"]=="checkout.session.completed":

        session=event["data"]["object"]

        email=session.get("customer_details",{}).get("email")

        send_message(
            OWNER_ID,
            f"Payment received from {email}"
        )

    return jsonify(success=True)



# =========================
# ROOT
# =========================

@app.route("/")

def home():

    return "Miserbot AI Radio Online"



# =========================
# START
# =========================

if __name__=="__main__":

    threading.Thread(target=radio_engine,daemon=True).start()

    port=int(os.environ.get("PORT",8080))

    app.run(host="0.0.0.0",port=port)
