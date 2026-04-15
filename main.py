import os
import requests
from flask import Flask, request, jsonify

# =========================
# ENV VARIABLES
# =========================

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# =========================
# FLASK APP
# =========================

app = Flask(__name__)

print("🚀 MISERBOT V200 STARTING...")
print("Bot token loaded")
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

    url = f"{TELEGRAM_API}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Send message error:", e)


# =========================
# COMMAND HANDLER
# =========================

def handle_command(chat_id, text):

    print("COMMAND:", text)

    if text == "/start":

        send_message(
            chat_id,
            "🚀 Welcome to BAZRAGOD NETWORK\n\n"
            "Commands:\n"
            "/radio\n"
            "/vault\n"
            "/coins\n"
            "/passport\n"
        )

    elif text == "/radio":

        send_message(
            chat_id,
            "📻 BazraGod Radio\nStreaming now."
        )

    elif text == "/vault":

        send_message(
            chat_id,
            "💎 Superfan Vault\nExclusive tracks live here."
        )

    elif text == "/coins":

        send_message(
            chat_id,
            "🪙 Miser Coin mining activated."
        )

    elif text == "/passport":

        send_message(
            chat_id,
            "🪪 Digital fan passport system active."
        )

    else:

        send_message(
            chat_id,
            "Command not recognized."
        )


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

            handle_command(chat_id, text)

        return jsonify({"ok": True})

    except Exception as e:

        print("Webhook error:", e)

        return jsonify({"ok": True})


# =========================
# HEALTH CHECK
# =========================

@app.route("/health")
def health():
    return jsonify({"status": "running"})


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
