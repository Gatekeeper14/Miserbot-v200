import os
import json
import requests
from flask import Flask, request

TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

print("TOKEN LENGTH:", len(TOKEN))

app = Flask(__name__)

# ----------------------
# SEND MESSAGE
# ----------------------

def send_message(chat_id, text, keyboard=None):

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json=payload
    )

    print("SEND MESSAGE:", r.status_code)
    print(r.text)


# ----------------------
# KEYBOARDS
# ----------------------

def language_keyboard():

    return {
        "keyboard": [
            ["English", "Spanish"],
            ["French", "Portuguese"],
            ["German", "Italian"]
        ],
        "resize_keyboard": True
    }


def enter_keyboard():

    return {
        "keyboard": [
            ["▶ ENTER PLATFORM"]
        ],
        "resize_keyboard": True
    }


def main_keyboard():

    return {
        "keyboard": [
            ["🎧 BAZRAGOD MUSIC", "📻 BAZRAGOD RADIO"],
            ["👤 My Profile", "🌐 Social"]
        ],
        "resize_keyboard": True
    }# ----------------------
# MESSAGE HANDLER
# ----------------------

def handle_message(msg):

    chat = msg["chat"]["id"]
    text = msg.get("text", "")

    print("USER MESSAGE:", text)

    if text == "/start":

        print("START COMMAND DETECTED")

        send_message(
            chat,
            "🌍 Choose your language",
            language_keyboard()
        )
        return


    if text in ["English", "Spanish", "French", "Portuguese", "German", "Italian"]:

        send_message(
            chat,
            "Welcome to BAZRAGOD RADIO NETWORK\nPress ENTER PLATFORM",
            enter_keyboard()
        )
        return


    if "ENTER PLATFORM" in text:

        send_message(
            chat,
            "👑 Welcome inside Parish 14 Nation",
            main_keyboard()
        )
        return


# ----------------------
# WEBHOOK
# ----------------------

@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    print("FULL UPDATE:")
    print(json.dumps(data, indent=2))

    if "message" in data:
        handle_message(data["message"])

    return {"ok": True}


# ----------------------
# HEALTH CHECK
# ----------------------

@app.route("/")
def home():
    return "Miserbot running"


# ----------------------
# START SERVER
# ----------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port
    )
