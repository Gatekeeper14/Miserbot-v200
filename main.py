import os
import random
import logging
from flask import Flask, request

import stripe
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters

# ------------------------------------------------
# ENV VARIABLES
# ------------------------------------------------

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

PORT = int(os.environ.get("PORT", 8080))

stripe.api_key = STRIPE_SECRET

bot = Bot(token=BOT_TOKEN)

# ------------------------------------------------
# FLASK
# ------------------------------------------------

app = Flask(__name__)

# ------------------------------------------------
# AUDIO SEEDS
# ------------------------------------------------

ENTRY_AUDIO = [
("Spaceship Entry",
"CQACAgEAAxkBAAEdFp1p3Cj-NIKT9FKEC_0X6Eniz_m2FwACnQYAAkpQ4UamWd5J9YX8JjsE")
]

AI_ANNOUNCEMENTS = [
("Welcome Announcement",
"CQACAgEAAxkBAAEdFp5p3Cj-zQABWAvFYVmk1cUfHKQ50YcAAp4GAAJKUOFGOvHURZUOztM7BA")
]

DROPS = [

("Drop_01","CQACAgEAAxkBAAEdFp1p3Cj-NIKT9FKEC_0X6Eniz_m2FwACnQYAAkpQ4UamWd5J9YX8JjsE"),
("Drop_02","CQACAgEAAxkBAAEdFp5p3Cj-zQABWAvFYVmk1cUfHKQ50YcAAp4GAAJKUOFGOvHURZUOztM7BA"),
("Drop_03","CQACAgEAAxkBAAEdFp9p3Cj-P0XFqQfgEmAP0vaC6PO4MQACnAYAAkpQ4Ub_QfJxunLKEjsE"),
("Drop_04","CQACAgEAAxkBAAEdFqBp3Cj-omwk9N0fA9IyicoGrIZgjwACmwYAAkpQ4UZNaMqq821M2DsE"),
("Drop_05","CQACAgEAAxkBAAEdFqFp3Cj-eJ9jh1uq9zkFq_TAoxOY8QACmgYAAkpQ4UZGYgiIil9iaTsE"),
("Drop_06","CQACAgEAAxkBAAEdFrdp3C2KTQABozdiEIV3KxzfYS3oW4UAAqIGAAJKUOFGUrhbQZsus-g7BA"),
("Drop_07","CQACAgEAAxkBAAEdFrhp3C2K2zWlpPHPD_JiMmqSx1sw0QACoQYAAkpQ4UbZlr5tW1xVLzsE"),
("Drop_08","CQACAgEAAxkBAAEdFrlp3C2KK6G3iLzCTpGm8aM6-O104gACpgYAAkpQ4UZ2RoURBVl9LjsE"),
("Drop_09","CQACAgEAAxkBAAEdFrpp3C2KyWJ_WPqKN6dFqAOum-OGNAACowYAAkpQ4Ub_8eRpccT7xzsE"),
("Drop_10","CQACAgEAAxkBAAEdFrtp3C2KR1i-fXRTv3aOAAGZ3VlypLEAAqQGAAJKUOFGq1Ghf3qJTs07BA"),
("Drop_11","CQACAgEAAxkBAAEdFrxp3C2KU6CFxRwnQE07PXndP3ZsBQACnwYAAkpQ4UZIhW5zxICIHDsE"),
("Drop_12","CQACAgEAAxkBAAEdFr1p3C2K2NUeOqY9-jvNhPcjtoqn2wACoAYAAkpQ4UbjeWTlslw2ujsE"),
("Drop_13","CQACAgEAAxkBAAEdFr5p3C2Kse8hvZYZq4Fd7Mt-sKMu-wACpQYAAkpQ4UbvCfrvUVAhwzsE")

]

# ------------------------------------------------
# RADIO ENGINE
# ------------------------------------------------

def play_spaceship_entry(chat_id):

    name, audio = random.choice(ENTRY_AUDIO)
    bot.send_audio(chat_id, audio, caption="🚀 Miserbot Launch Sequence")

    name, audio = random.choice(AI_ANNOUNCEMENTS)
    bot.send_audio(chat_id, audio, caption="🤖 AI Station Online")

def play_random_drop(chat_id):

    name, audio = random.choice(DROPS)
    bot.send_audio(chat_id, audio, caption=f"🎧 {name}")

# ------------------------------------------------
# BOT COMMANDS
# ------------------------------------------------

def start(update, context):

    chat_id = update.effective_chat.id

    play_spaceship_entry(chat_id)

    context.bot.send_message(
        chat_id,
        "🎵 Welcome to Miserbot Radio\n\n"
        "Commands:\n"
        "/radio\n"
        "/drop\n"
        "/mint\n"
        "/shop"
    )

def radio(update, context):

    chat_id = update.effective_chat.id

    context.bot.send_message(chat_id, "📡 Radio Mode Activated")

    play_random_drop(chat_id)

def drop(update, context):

    chat_id = update.effective_chat.id

    play_random_drop(chat_id)

def shop(update, context):

    update.message.reply_text(
        "💳 Support Miserbot\n"
        "https://buy.stripe.com/6oUeVf0Ml7Iv6Wg1PM5Rm00"
    )

def mint(update, context):

    update.message.reply_text(
        "🪙 NFT Drop Coming Soon"
    )

# ------------------------------------------------
# TELEGRAM DISPATCHER
# ------------------------------------------------

dispatcher = Dispatcher(bot, None, workers=0)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("radio", radio))
dispatcher.add_handler(CommandHandler("drop", drop))
dispatcher.add_handler(CommandHandler("shop", shop))
dispatcher.add_handler(CommandHandler("mint", mint))

# ------------------------------------------------
# TELEGRAM WEBHOOK
# ------------------------------------------------

@app.route("/webhook", methods=["POST"])
def telegram_webhook():

    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)

    return "ok"

# ------------------------------------------------
# STRIPE WEBHOOK
# ------------------------------------------------

@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():

    payload = request.data
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return "invalid", 400

    if event["type"] == "checkout.session.completed":
        print("💰 Payment received")

    return "success"

# ------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------

@app.route("/")
def index():
    return "Miserbot AI Radio Engine Online"

# ------------------------------------------------
# RUN
# ------------------------------------------------

if __name__ == "__main__":

    print("🚀 MISERBOT ENGINE ONLINE")
    print("Drops:", len(DROPS))

    app.run(host="0.0.0.0", port=PORT)
