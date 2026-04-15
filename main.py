import os
import requests
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

stripe.api_key = STRIPE_SECRET

TELEGRAM = f"https://api.telegram.org/bot{BOT_TOKEN}"

catalog = {}
users = {}
vault = {}
coins = {}

def send_message(chat_id,text):

    requests.post(
        f"{TELEGRAM}/sendMessage",
        json={
            "chat_id":chat_id,
            "text":text
        }
    )

def send_audio(chat_id,file_id):

    requests.post(
        f"{TELEGRAM}/sendAudio",
        json={
            "chat_id":chat_id,
            "audio":file_id
        }
    )

def send_buttons(chat_id,text,buttons):

    requests.post(
        f"{TELEGRAM}/sendMessage",
        json={
            "chat_id":chat_id,
            "text":text,
            "reply_markup":{
                "inline_keyboard":buttons
            }
        }
    )

@app.route("/")
def home():

    return "Miserbot backend running"

@app.route("/webhook",methods=["POST"])
def webhook():

    try:

        data = request.get_json(force=True)

        if not data:
            return "ok",200

        message = data.get("message")

        if not message:
            return "ok",200

        chat_id = message["chat"]["id"]
        text = message.get("text","")

        if chat_id not in users:

            users[chat_id] = True
            vault[chat_id] = []
            coins[chat_id] = 0

        if text == "/start":

            send_buttons(

                chat_id,

                "🔥 Welcome to Miserbot",

                [

                    [{"text":"🎵 Store","callback_data":"store"}],

                    [{"text":"🎧 Vault","callback_data":"vault"}],

                    [{"text":"⛏ Mine Coin","callback_data":"mine"}],

                    [{"text":"🏆 Leaderboard","callback_data":"leader"}]

                ]

            )

        if text == "/mine":

            coins[chat_id] += 1

            send_message(

                chat_id,

                f"Coin mined. Total: {coins[chat_id]}"

            )

        if text == "/vault":

            if not vault[chat_id]:

                send_message(chat_id,"Vault empty")

            else:

                for track in vault[chat_id]:

                    send_audio(chat_id,track)

        if "audio" in message and message["from"]["id"] == OWNER_ID:

            audio = message["audio"]

            file_id = audio["file_id"]
            title = audio.get("file_name","song")

            song_id = f"song_{len(catalog)+1}"

            catalog[song_id] = {

                "title":title,
                "price":1999,
                "file_id":file_id

            }

            send_message(

                chat_id,

                f"Captured song: {title}"

            )

        return "ok",200

    except Exception as e:

        print("Webhook error:",e)

        return "ok",200

@app.route("/callback",methods=["POST"])
def callback():

    try:

        data = request.json

        cb = data["callback_query"]

        chat_id = cb["message"]["chat"]["id"]
        action = cb["data"]

        if action == "mine":

            coins[chat_id] += 1

            send_message(

                chat_id,

                f"Coins: {coins[chat_id]}"

            )

        if action == "leader":

            ranking = sorted(

                coins.items(),

                key=lambda x:x[1],

                reverse=True

            )

            board = ""

            for i,(u,c) in enumerate(ranking[:10]):

                board += f"{i+1}. {u} — {c} coins\n"

            send_message(

                chat_id,

                "🏆 Leaderboard\n"+board

            )

        if action == "vault":

            if not vault[chat_id]:

                send_message(chat_id,"Vault empty")

            else:

                for track in vault[chat_id]:

                    send_audio(chat_id,track)

        if action == "store":

            buttons = []

            for sid,data in catalog.items():

                buttons.append(

                    [{

                        "text":f"{data['title']} $19.99",

                        "callback_data":f"buy_{sid}"

                    }]

                )

            send_buttons(

                chat_id,

                "🎵 Store",

                buttons

            )

        if action.startswith("buy_"):

            sid = action.split("_")[1]

            song = catalog[sid]

            session = stripe.checkout.Session.create(

                payment_method_types=["card"],

                line_items=[{

                    "price_data":{

                        "currency":"usd",

                        "product_data":{

                            "name":song["title"]

                        },

                        "unit_amount":song["price"]

                    },

                    "quantity":1

                }],

                mode="payment",

                success_url="https://miserbot-site.vercel.app/success",

                cancel_url="https://miserbot-site.vercel.app/cancel",

                client_reference_id=str(chat_id),

                metadata={

                    "song":sid

                }

            )

            send_message(

                chat_id,

                "Pay here:\n"+session.url

            )

        return "ok",200

    except Exception as e:

        print("Callback error:",e)

        return "ok",200

@app.route("/stripe-webhook",methods=["POST"])
def stripe_webhook():

    try:

        event = request.json

        if event["type"] == "checkout.session.completed":

            session = event["data"]["object"]

            chat_id = int(

                session["client_reference_id"]

            )

            sid = session["metadata"]["song"]

            song = catalog[sid]

            vault[chat_id].append(

                song["file_id"]

            )

            send_audio(

                chat_id,

                song["file_id"]

            )

            send_message(

                chat_id,

                "Purchase complete. Song delivered."

            )

        return "ok"

    except Exception as e:

        print("Stripe error:",e)

        return "ok"

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000

    )
