import os
import stripe
import random
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ENV VARIABLES
BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")
OWNER_ID = os.getenv("OWNER_ID")
YOUTUBE_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL = os.getenv("YOUTUBE_CHANNEL_ID")

stripe.api_key = STRIPE_KEY

TELEGRAM = f"https://api.telegram.org/bot{BOT_TOKEN}"

users = {}
coins = {}
vault = {}

# TELEGRAM HELPERS

def send_message(chat_id,text):

    requests.post(
        f"{TELEGRAM}/sendMessage",
        json={
            "chat_id":chat_id,
            "text":text
        }
    )

def send_audio(chat_id,url):

    requests.post(
        f"{TELEGRAM}/sendAudio",
        json={
            "chat_id":chat_id,
            "audio":url
        }
    )

# HEALTH CHECK

@app.route("/")
def home():
    return "Miserbot Master Backend Online"

# TELEGRAM WEBHOOK

@app.route("/webhook",methods=["POST"])
def webhook():

    data = request.json

    if "message" not in data:
        return "ok"

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text","")

    if chat_id not in users:

        users[chat_id] = True
        coins[chat_id] = 0
        vault[chat_id] = []

    if text == "/start":

        send_message(chat_id,
        "🔥 BAZRAGOD NETWORK\n\nOpen the Mini App to explore music, vault, coins and events.")

    elif text == "/mine":

        coins[chat_id] += 1

        send_message(chat_id,
        f"⛏ Miser Coin mined\nBalance: {coins[chat_id]}")

    elif text == "/vault":

        if not vault[chat_id]:

            send_message(chat_id,"Vault empty")

        else:

            for track in vault[chat_id]:
                send_audio(chat_id,track)

    return "ok"

# STRIPE CHECKOUT

@app.route("/create-checkout",methods=["POST"])
def checkout():

    data = request.json

    session = stripe.checkout.Session.create(

        payment_method_types=["card"],

        line_items=[{
            "price_data":{
                "currency":"usd",
                "product_data":{
                    "name":data["name"]
                },
                "unit_amount":data["price"]
            },
            "quantity":1
        }],

        mode="payment",

        success_url="https://miserbot-site.vercel.app/?success=true",

        cancel_url="https://miserbot-site.vercel.app/?cancel=true"

    )

    return jsonify({"url":session.url})

# STRIPE WEBHOOK

@app.route("/stripe-webhook",methods=["POST"])
def stripe_webhook():

    event = request.json

    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        chat_id = session.get("client_reference_id")

        if chat_id:

            song = "https://example.com/song.mp3"

            vault[int(chat_id)].append(song)

            send_audio(chat_id,song)

    return "ok"

# COIN LEADERBOARD

@app.route("/leaderboard")
def leaderboard():

    ranking = sorted(coins.items(),key=lambda x:x[1],reverse=True)

    return jsonify(ranking)

# PASSPORT

@app.route("/passport/<chat_id>")
def passport(chat_id):

    code = "P" + str(random.randint(100000,999999))

    return jsonify({

        "passport":code

    })

# EVENTS

@app.route("/events")
def events():

    return jsonify({

        "events":[

            {"city":"Miami","month":"July"},
            {"city":"Atlanta","month":"August"},
            {"city":"New York","month":"September"}

        ]

    })

# YOUTUBE FEED

@app.route("/youtube")
def youtube():

    url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_KEY}&channelId={YOUTUBE_CHANNEL}&part=snippet,id&order=date&maxResults=5"

    r = requests.get(url)

    return r.json()

# RADIO LINK

@app.route("/radio")
def radio():

    return jsonify({

        "radio":"https://t.me/yourradiochannel"

    })

# BOOKING INFO

@app.route("/booking")
def booking():

    return jsonify({

        "packages":[

            {"name":"Feature Verse","price":5000},
            {"name":"Studio Bundle","price":1200},
            {"name":"Small Club Show","price":2500},
            {"name":"Medium Club Show","price":5000},
            {"name":"Large Club Show","price":15000},
            {"name":"Video Cameo","price":1200},
            {"name":"Full Record Collab","price":5000}

        ]

    })

if __name__ == "__main__":

    app.run(host="0.0.0.0",port=5000)
