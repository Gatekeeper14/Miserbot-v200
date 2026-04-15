import os
import logging
import stripe
import requests
from flask import Flask, request, jsonify

# ---------------------------------------------------
# ENV VARIABLES
# ---------------------------------------------------

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK = os.getenv("STRIPE_WEBHOOK_SECRET")

RADIO_CHANNEL = os.getenv("RADIO_CHANNEL")
PARISH_LOUNGE = os.getenv("PARISH_LOUNGE")

DATABASE_URL = os.getenv("DATABASE_URL")

if STRIPE_SECRET:
    stripe.api_key = STRIPE_SECRET

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ---------------------------------------------------
# FLASK APP
# ---------------------------------------------------

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

print("🚀 MISERBOT V200 STARTING...")
print("Bot token loaded")
print("Webhook ready")

# ---------------------------------------------------
# ROOT ROUTE (RAILWAY HEALTH CHECK)
# ---------------------------------------------------

@app.route("/")
def home():
    return "🚀 Miserbot backend alive", 200

# ---------------------------------------------------
# TELEGRAM SEND FUNCTION
# ---------------------------------------------------

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)

# ---------------------------------------------------
# TELEGRAM COMMAND HANDLER
# ---------------------------------------------------

def handle_command(chat_id, text):

    if text == "/start":
        send_message(chat_id,
        "🚀 Welcome to BAZRAGOD NETWORK\n\n"
        "Use the menu to explore:\n"
        "🎧 Music\n"
        "📻 Radio\n"
        "💎 Vault\n"
        "🏆 Leaderboard\n"
        "🪙 Miser Coins\n"
        "🪪 Passport\n"
        "📅 Events")

    elif text == "/radio":
        send_message(chat_id,
        f"📻 Listen live:\n{RADIO_CHANNEL}")

    elif text == "/lounge":
        send_message(chat_id,
        f"🎙 Parish 14 Lounge:\n{PARISH_LOUNGE}")

    elif text == "/coins":
        send_message(chat_id,
        "🪙 Miser Coins mining active.\n"
        "Tap music daily to earn points.")

    elif text == "/vault":
        send_message(chat_id,
        "💎 Superfan Vault\nExclusive tracks stored here.")

    elif text == "/passport":
        send_message(chat_id,
        "🪪 Digital Passport\n"
        "Tracks shows, fan points and VIP access.")

    else:
        send_message(chat_id,
        "Command not recognized.\nUse /start")

# ---------------------------------------------------
# TELEGRAM WEBHOOK
# ---------------------------------------------------

@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    if "message" in data:

        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text:
            handle_command(chat_id, text)

    return jsonify({"status": "ok"})

# ---------------------------------------------------
# STRIPE WEBHOOK
# ---------------------------------------------------

@app.route("/stripe", methods=["POST"])
def stripe_webhook():

    payload = request.data
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK
        )
    except Exception as e:
        return str(e), 400

    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        telegram_id = session.get("client_reference_id")

        if telegram_id:
            send_message(
                telegram_id,
                "✅ Payment received.\n"
                "Your download is being prepared."
            )

    return jsonify({"status": "success"})

# ---------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------

@app.route("/health")
def health():
    return jsonify({"status": "running"})

# ---------------------------------------------------
# RUN SERVER
# ---------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
