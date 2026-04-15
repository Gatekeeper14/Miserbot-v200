import os
import stripe
import random
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BOT_TOKEN=os.getenv("ROYAL_BOT_TOKEN")
OWNER_ID=os.getenv("OWNER_ID")

STRIPE_KEY=os.getenv("STRIPE_SECRET_KEY")
stripe.api_key=STRIPE_KEY

TELEGRAM_API=f"https://api.telegram.org/bot{BOT_TOKEN}"

users={}
coins={}
vault={}
leaderboard={}

def send_message(chat_id,text):

    requests.post(f"{TELEGRAM_API}/sendMessage",json={
        "chat_id":chat_id,
        "text":text
    })

def send_audio(chat_id,file_url):

    requests.post(f"{TELEGRAM_API}/sendAudio",json={
        "chat_id":chat_id,
        "audio":file_url
    })

@app.route("/")
def home():
    return "Miserbot backend running"

@app.route("/webhook",methods=["POST"])
def telegram_webhook():

    data=request.json

    if "message" not in data:
        return "ok"

    msg=data["message"]
    chat_id=msg["chat"]["id"]

    text=msg.get("text","")

    if chat_id not in users:
        users[chat_id]=True
        coins[chat_id]=0
        vault[chat_id]=[]

    if text=="/start":

        send_message(chat_id,
        "Welcome to Bazragod Network\n\nOpen Mini App")

    elif text=="/mine":

        coins[chat_id]+=1
        send_message(chat_id,f"Coins: {coins[chat_id]}")

    elif text=="/vault":

        if not vault[chat_id]:
            send_message(chat_id,"Vault empty")
        else:
            for song in vault[chat_id]:
                send_audio(chat_id,song)

    return "ok"

@app.route("/create-checkout",methods=["POST"])
def create_checkout():

    data=request.json

    session=stripe.checkout.Session.create(

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

@app.route("/stripe-webhook",methods=["POST"])
def stripe_webhook():

    payload=request.data
    sig=request.headers.get("stripe-signature")

    event=stripe.Event.construct_from(request.json,stripe.api_key)

    if event["type"]=="checkout.session.completed":

        session=event["data"]["object"]

        chat_id=session.get("client_reference_id")

        if chat_id:

            song="https://example.com/song.mp3"

            vault[int(chat_id)].append(song)

            send_audio(chat_id,song)

    return "ok"

@app.route("/leaderboard")
def board():

    ranking=sorted(coins.items(),key=lambda x:x[1],reverse=True)

    return jsonify(ranking)

@app.route("/passport/<chat_id>")
def passport(chat_id):

    code="P"+str(random.randint(100000,999999))

    return jsonify({
        "passport":code
    })

@app.route("/youtube-feed")
def youtube():

    channel=os.getenv("YOUTUBE_CHANNEL_ID")
    key=os.getenv("YOUTUBE_API_KEY")

    url=f"https://www.googleapis.com/youtube/v3/search?key={key}&channelId={channel}&part=snippet,id&order=date&maxResults=5"

    r=requests.get(url)

    return r.json()

@app.route("/events")
def events():

    return jsonify({

        "shows":[
            {"city":"Miami","date":"July"},
            {"city":"NYC","date":"August"}
        ]

    })

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)
