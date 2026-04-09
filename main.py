import os
import json
import time
import random
from datetime import datetime

from flask import Flask, request
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

API = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

# =========================
# DATABASE FILES
# =========================

USERS_DB = "users.json"
LIBRARY_DB = "library.json"
TRAVEL_DB = "travel.json"

# =========================
# LOAD DATABASES
# =========================

def load_db(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_db(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

users = load_db(USERS_DB)
library = load_db(LIBRARY_DB)
travel = load_db(TRAVEL_DB)

# =========================
# TELEGRAM HELPERS
# =========================

def send_message(chat_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)

    requests.post(f"{API}/sendMessage", data=payload)


def send_audio(chat_id, file_id, title="Track", performer="BazraGod"):
    payload = {
        "chat_id": chat_id,
        "audio": file_id,
        "title": title,
        "performer": performer
    }

    requests.post(f"{API}/sendAudio", data=payload)


# =========================
# KEYBOARDS
# =========================

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


# =========================
# USER SYSTEM
# =========================

def get_user(user_id):

    if str(user_id) not in users:

        users[str(user_id)] = {
            "language":"English",
            "points":0,
            "bio":"",
            "photo":None
        }

        save_db(USERS_DB, users)

    return users[str(user_id)]


# =========================
# DJ SCHEDULE
# =========================

def current_dj():

    hour = datetime.utcnow().hour

    if 6 <= hour < 18:
        return "🌞 DAY DJ"
    else:
        return "🌙 NIGHT DJ"


# =========================
# RADIO ENGINE
# =========================

radio_running = False
radio_chat = None

def radio_loop():

    global radio_running

    while radio_running:

        songs = library.get("songs", [])

        if not songs:
            time.sleep(10)
            continue

        track = random.choice(songs)

        send_message(
            radio_chat,
            f"🎧 Now Playing\n{track['title']}\nDJ: {current_dj()}"
        )

        send_audio(
            radio_chat,
            track["file_id"],
            track["title"],
            track["artist"]
        )

        duration = track.get("duration",180)

        time.sleep(duration)


# =========================
# SONG UPLOAD (ADMIN)
# =========================

def save_song(file_id, title, artist):

    if "songs" not in library:
        library["songs"] = []

    library["songs"].append({
        "file_id":file_id,
        "title":title,
        "artist":artist,
        "duration":180
    })

    save_db(LIBRARY_DB, library)
# =========================
# COMMAND HANDLER
# =========================

def handle_message(msg):

    chat = msg["chat"]["id"]
    user_id = msg["from"]["id"]
    text = msg.get("text","")

    user = get_user(user_id)

    # START
    if text == "/start":

        send_message(
            chat,
            "🌍 Choose your language",
            language_keyboard()
        )
        return


    # LANGUAGE SELECT
    if text in ["English","Spanish","French","Portuguese","German","Italian"]:

        user["language"] = text
        save_db(USERS_DB, users)

        send_message(
            chat,
            "Welcome to BAZRAGOD RADIO NETWORK\nPress enter to continue",
            enter_keyboard()
        )
        return


    # ENTER PLATFORM
    if text == "▶ ENTER PLATFORM":

        send_message(
            chat,
            "👑 Welcome inside Parish 14 Nation",
            main_keyboard()
        )
        return


    # RADIO
    if text == "📻 BAZRAGOD RADIO":

        global radio_running
        global radio_chat

        radio_chat = chat

        if not radio_running:

            radio_running = True

            import threading
            threading.Thread(target=radio_loop).start()

        send_message(chat,"📻 Radio is now live")
        return


    # SOCIAL HUB
    if text == "🌐 Social":

        keyboard = {
            "inline_keyboard":[
                [{"text":"Instagram","url":"https://instagram.com"}],
                [{"text":"YouTube","url":"https://youtube.com"}],
                [{"text":"Website","url":"https://example.com"}]
            ]
        }

        send_message(chat,"🌐 Social Links",keyboard)
        return


    # PROFILE
    if text == "👤 My Profile":

        profile = f"""
👤 PROFILE

Bio: {user['bio']}
Points: {user['points']}
"""

        send_message(chat,profile)
        return


    # DAILY MISSION
    if text == "🎯 Daily Mission":

        send_message(
            chat,
            "🎯 Mission: Listen to 3 songs today\nReward: +20 points"
        )
        return


    # MUSIC LIBRARY
    if text == "🎧 BAZRAGOD MUSIC":

        songs = library.get("songs",[])

        if not songs:
            send_message(chat,"Music library empty")
            return

        track = random.choice(songs)

        send_audio(
            chat,
            track["file_id"],
            track["title"],
            track["artist"]
        )

        return


# =========================
# TELEGRAM WEBHOOK
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    if "message" in data:

        handle_message(data["message"])

    return {"ok":True}


# =========================
# HEALTH CHECK
# =========================

@app.route("/")
def home():
    return "Miserbot running"


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT",5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
