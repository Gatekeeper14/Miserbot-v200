import os
import json
import time
import random
import threading
from datetime import datetime
from flask import Flask, request
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

API = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

USERS_DB = "users.json"
LIBRARY_DB = "library.json"

# -----------------------
# DATABASE
# -----------------------

def load_db(path, default):
    if not os.path.exists(path):
        with open(path,"w") as f:
            json.dump(default,f)
        return default
    with open(path) as f:
        return json.load(f)

def save_db(path,data):
    with open(path,"w") as f:
        json.dump(data,f,indent=2)

users = load_db(USERS_DB,{})
library = load_db(LIBRARY_DB,{"songs":[]})

# -----------------------
# TELEGRAM SEND
# -----------------------

def send_message(chat_id,text,keyboard=None,inline=None):

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    if inline:
        payload["reply_markup"] = inline

    requests.post(
        f"{API}/sendMessage",
        json=payload
    )


def send_audio(chat_id,file_id,title="Track",artist="BazraGod"):

    payload = {
        "chat_id": chat_id,
        "audio": file_id,
        "title": title,
        "performer": artist
    }

    requests.post(
        f"{API}/sendAudio",
        json=payload
    )

# -----------------------
# KEYBOARDS
# -----------------------

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
            ["🧠 Mood Radio","⚔️ Lyric Cipher"],
            ["📊 Top Charts","💎 Supporter"],
            ["🥁 Beats","🎤 Drops"],
            ["🏆 Leaderboard","⭐ My Points"],
            ["👤 My Profile","🎯 Daily Mission"],
            ["💰 Support Artist","🌐 Social"]
        ],
        "resize_keyboard":True
    }

# -----------------------
# USER SYSTEM
# -----------------------

def get_user(uid):

    uid=str(uid)

    if uid not in users:

        users[uid]={
            "language":"English",
            "points":0,
            "bio":"",
            "photo":None
        }

        save_db(USERS_DB,users)

    return users[uid]

# -----------------------
# DJ SYSTEM
# -----------------------

def current_dj():

    hour=datetime.utcnow().hour

    if 6<=hour<18:
        return "🌞 DAY DJ"

    return "🌙 NIGHT DJ"

# -----------------------
# RADIO ENGINE
# -----------------------

radio_running=False
radio_chat=None

def radio_loop():

    global radio_running

    while radio_running:

        songs=library.get("songs",[])

        if not songs:
            print("NO SONGS")
            time.sleep(10)
            continue

        track=random.choice(songs)

        send_message(
            radio_chat,
            f"🎧 Now Playing\n{track['title']}\nDJ {current_dj()}"
        )

        send_audio(
            radio_chat,
            track["file_id"],
            track["title"],
            track["artist"]
        )

        time.sleep(track.get("duration",180))

# -----------------------
# SONG SAVE
# -----------------------

def save_song(file_id,title,artist):

    library["songs"].append({
        "file_id":file_id,
        "title":title,
        "artist":artist,
        "duration":180
    })

    save_db(LIBRARY_DB,library)

    print("SONG SAVED",title)
# -----------------------
# MESSAGE HANDLER
# -----------------------

def handle_message(msg):

    chat=msg["chat"]["id"]
    user_id=msg["from"]["id"]

    text=msg.get("text") or msg.get("caption") or ""
    text=text.strip()

    print("USER MESSAGE:",text)

    user=get_user(user_id)

    # START
    if text=="/start":

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
            "Welcome to BAZRAGOD RADIO NETWORK\nPress ENTER PLATFORM",
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


    # RADIO
    if "BAZRAGOD RADIO" in text:

        global radio_running
        global radio_chat

        radio_chat=chat

        if not radio_running:

            radio_running=True
            threading.Thread(target=radio_loop).start()

        send_message(chat,"📻 Radio Started")
        return


    # MUSIC
    if "BAZRAGOD MUSIC" in text:

        songs=library.get("songs",[])

        if not songs:
            send_message(chat,"Music library empty")
            return

        track=random.choice(songs)

        send_audio(
            chat,
            track["file_id"],
            track["title"],
            track["artist"]
        )

        return


    # PROFILE
    if "My Profile" in text:

        profile=f"""
👤 PROFILE

Bio: {user['bio']}
Points: {user['points']}
"""

        send_message(chat,profile)
        return


    # SOCIAL
    if "Social" in text:

        inline={
            "inline_keyboard":[
                [{"text":"Instagram","url":"https://instagram.com"}],
                [{"text":"YouTube","url":"https://youtube.com"}],
                [{"text":"Website","url":"https://example.com"}]
            ]
        }

        send_message(chat,"🌐 Social Links",inline=inline)
        return


    # ADMIN SONG UPLOAD
    if "audio" in msg and user_id==ADMIN_ID:

        caption=msg.get("caption","")

        if caption.startswith("upload:song"):

            try:
                parts=caption.split("|")
                title=parts[1]
                artist=parts[2]
            except:
                title="Track"
                artist="Unknown"

            file_id=msg["audio"]["file_id"]

            save_song(file_id,title,artist)

            send_message(chat,f"✅ Song saved\n{title}")

            return


# -----------------------
# WEBHOOK
# -----------------------

@app.route("/webhook",methods=["POST"])
def webhook():

    data=request.json

    print("UPDATE:",data)

    if "message" in data:
        handle_message(data["message"])

    return {"ok":True}


# -----------------------
# HEALTH CHECK
# -----------------------

@app.route("/")
def home():
    return "Miserbot running"


# -----------------------
# SERVER
# -----------------------

if __name__=="__main__":

    port=int(os.environ.get("PORT",8080))

    app.run(
        host="0.0.0.0",
        port=port
    )
