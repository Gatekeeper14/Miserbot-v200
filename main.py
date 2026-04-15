import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

print("🚀 MISERBOT V200 STARTING...")

# =========================
# LOAD ENV VARIABLES
# =========================

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")

if BOT_TOKEN:
    print("Bot token loaded")
else:
    print("❌ BOT TOKEN MISSING")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

print("Webhook ready")


# =========================
# ROOT ROUTE (Railway health)
# =========================

@app.route("/")
def home():
    return "🚀 Miserbot backend alive", 200


# =========================
# TELEGRAM SEND MESSAGE
# =========================

def send_message(chat_id, text):

    try:

        url = f"{TELEGRAM_API}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": text
        }

        requests.post(url, json=payload)

    except Exception as e:

        print("Send message error:", e)


# =========================
# TELEGRAM WEBHOOK
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():

    try:

        data = request.get_json()

        print("📩 TELEGRAM UPDATE:", data)

        if "message" in data:

            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")

            if text == "/start":

                send_message(
                    chat_id,
                    "🚀 Miserbot is online."
                )

            else:

                send_message(
                    chat_id,
                    "Command received."
                )

        return jsonify({"ok": True})

    except Exception as e:

        print("Webhook error:", e)

        return jsonify({"ok": True})


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
