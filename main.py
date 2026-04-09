import os
import json
import time
import random
import threading
from datetime import datetime
from flask import Flask, request
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID","0"))

API = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

USERS_DB="users.json"
LIBRARY_DB="library.json"

# -------------------------
# DATABASE
# -------------------------

def load_db(path,default):
    if not os.path.exists(path):
        with open(path,"w") as f:
            json.dump(default,f)
        return default

    with open(path) as f:
        return json.load(f)

def save_db(path,data):
    with open(path,"w") as f:
        json.dump(data,f,indent=2)

users=load_db(USERS_DB,{})
library=load_db(LIBRARY_DB,{"songs":[]})

# -------------------------
# TELEGRAM SEND
# -------------------------

def send_message(chat_id,text,keyboard=None):

    payload={
        "chat_id":chat_id,
        "text":text
    }

    if keyboard:
        payload["reply_markup"]=keyboard

    r=requests.post(
        f"{API}/sendMessage",
        json=payload
    )

    print("SEND MESSAGE STATUS:",r.status_code)
    print(r.text)


def send_audio(chat_id,file_id,title,artist):

    payload={
        "chat_id":chat_id,
        "audio":file_id,
        "title":title,
        "performer":artist
    }

    r=requests.post(
        f"{API}/sendAudio",
        json=payload
    )

    print("SEND AUDIO:",r.text)


# -------------------------
# KEYBOARDS
# -------------------------

def language_keyboard():

    return {
        "keyboard":[
            ["English","Spanish"],
            ["French","Portuguese"],
            ["German","Italian"]
        ],
        "resize_keyboard":True
    }


def enter_keyboard():

    return {
        "keyboard":[
            ["▶ ENTER PLATFORM"]
        ],
        "resize_keyboard":True
    }


def main_keyboard():

    return {
        "keyboard":[
            ["🎧 BAZRAGOD MUSIC","📻 BAZRAGOD RADIO"],
            ["👤 My Profile","🌐 Social"]
        ],
        "resize_keyboard":True
    }


# -------------------------
# USER SYSTEM
# -------------------------

def get_user(uid):

    uid=str(uid)

    if uid not in users:

        users[uid]={
            "language":"English",
            "points":0
        }

        save_db(USERS_DB,users)

    return users[uid]
# -------------------------
# MESSAGE HANDLER
# -------------------------

def handle_message(msg):

    chat=msg["chat"]["id"]
    user_id=msg["from"]["id"]

    text=msg.get("text") or msg.get("caption") or ""
    text=text.strip()

    print("USER MESSAGE:",text)

    user=get_user(user_id)

    # START
    if text=="/start":

        print("START COMMAND DETECTED")

        send_message(
            chat,
            "🌍 Choose your language",
            language_keyboard()
        )

        return


    # LANGUAGE
    if text in ["English","Spanish","French","Portuguese","German","Italian"]:

        user["language"]=text
        save_db(USERS_DB,users)

        send_message(
            chat,
            "Welcome to BAZRAGOD RADIO NETWORK",
            enter_keyboard()
        )

        return


    # ENTER PLATFORM
    if "ENTER PLATFORM" in text:

        send_message(
            chat,
            "👑 Welcome inside Parish 14 Nation",
            main_keyboard()
        )

        return


# -------------------------
# WEBHOOK
# -------------------------

@app.route("/webhook",methods=["POST"])
def webhook():

    data=request.json

    print("UPDATE:",data)

    if "message" in data:
        handle_message(data["message"])

    return {"ok":True}


# -------------------------
# HEALTH CHECK
# -------------------------

@app.route("/")
def home():
    return "Bot running"


# -------------------------
# START SERVER
# -------------------------

if __name__=="__main__":

    port=int(os.environ.get("PORT",8080))

    app.run(
        host="0.0.0.0",
        port=port
    )
