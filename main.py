import os
import json
import requests
from flask import Flask, request

# ================================
# ENVIRONMENT VARIABLES
# ================================

TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

print("TOKEN LENGTH:", len(TOKEN))

API_URL = f"https://api.telegram.org/bot{TOKEN}"

# ================================
# CREATE FLASK APP
# ================================

app = Flask(__name__)

# ================================
# TELEGRAM FUNCTIONS
# ================================

def send_message(chat_id, text, keyboard=None):

    url = f"{API_URL}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    r = requests.post(url, json=payload)

    print("SEND MESSAGE STATUS:", r.status_code)
    print(r.text)


def main_menu():

    return {
        "keyboard": [
            ["📻 BazraGod Radio"],
            ["🌍 Language"],
            ["👤 My Profile"],
            ["⚙️ Settings"]
        ],
        "resize_keyboard": True
    }

# ================================
# ROUTES
# ================================

@app.route("/")
def home():
    return "Miserbot running"


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    print("FULL UPDATE:")
    print(json.dumps(data, indent=2))

    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")

    text = message.get("text", "")

    print("USER MESSAGE:", text)

    # ================================
    # START COMMAND
    # ================================

    if text == "/start":

        print("START COMMAND DETECTED")

        send_message(
            chat_id,
            "👑 Welcome to BAZRAGOD RADIO NETWORK\n\nSelect an option below.",
            main_menu()
        )

    # ================================
    # RADIO BUTTON
    # ================================

    elif text == "📻 BazraGod Radio":

        send_message(
            chat_id,
            "📻 Radio system will begin here."
        )

    # ================================
    # LANGUAGE BUTTON
    # ================================

    elif text == "🌍 Language":

        send_message(
            chat_id,
            "🌍 Language system coming soon."
        )

    # ================================
    # PROFILE BUTTON
    # ================================

    elif text == "👤 My Profile":

        send_message(
            chat_id,
            "👤 Profile system coming soon."
        )

    else:

        send_message(
            chat_id,
            "Command received."
        )

    return {"ok": True}

# ================================
# RUN SERVER
# ================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(host="0.0.0.0", port=port)
