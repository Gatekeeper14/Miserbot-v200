import os
import random
import logging

from flask import Flask, request

from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

# -----------------------------
# ENVIRONMENT
# -----------------------------

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

bot = Bot(token=BOT_TOKEN)

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# -----------------------------
# AUDIO SEEDS
# -----------------------------

SPACESHIP_ENTRY = [
"CQACAgEAAxkBAAEdFp1p3Cj-NIKT9FKEC_0X6Eniz_m2FwACnQYAAkpQ4UamWd5J9YX8JjsE"
]

AI_ANNOUNCE = [
"CQACAgEAAxkBAAEdFp5p3Cj-zQABWAvFYVmk1cUfHKQ50YcAAp4GAAJKUOFGOvHURZUOztM7BA"
]

DROPS = [

"CQACAgEAAxkBAAEdFp9p3Cj-P0XFqQfgEmAP0vaC6PO4MQACnAYAAkpQ4Ub_QfJxunLKEjsE",
"CQACAgEAAxkBAAEdFqBp3Cj-omwk9N0fA9IyicoGrIZgjwACmwYAAkpQ4UZNaMqq821M2DsE",
"CQACAgEAAxkBAAEdFqFp3Cj-eJ9jh1uq9zkFq_TAoxOY8QACmgYAAkpQ4UZGYgiIil9iaTsE",
"CQACAgEAAxkBAAEdFrdp3C2KTQABozdiEIV3KxzfYS3oW4UAAqIGAAJKUOFGUrhbQZsus-g7BA",
"CQACAgEAAxkBAAEdFrhp3C2K2zWlpPHPD_JiMmqSx1sw0QACoQYAAkpQ4UbZlr5tW1xVLzsE",
"CQACAgEAAxkBAAEdFrlp3C2KK6G3iLzCTpGm8aM6-O104gACpgYAAkpQ4UZ2RoURBVl9LjsE",
"CQACAgEAAxkBAAEdFrpp3C2KyWJ_WPqKN6dFqAOum-OGNAACowYAAkpQ4Ub_8eRpccT7xzsE",
"CQACAgEAAxkBAAEdFrtp3C2KR1i-fXRTv3aOAAGZ3VlypLEAAqQGAAJKUOFGq1Ghf3qJTs07BA",
"CQACAgEAAxkBAAEdFrxp3C2KU6CFxRwnQE07PXndP3ZsBQACnwYAAkpQ4UZIhW5zxICIHDsE",
"CQACAgEAAxkBAAEdFr1p3C2K2NUeOqY9-jvNhPcjtoqn2wACoAYAAkpQ4UbjeWTlslw2ujsE",
"CQACAgEAAxkBAAEdFr5p3C2Kse8hvZYZq4Fd7Mt-sKMu-wACpQYAAkpQ4UbvCfrvUVAhwzsE"

]

# -----------------------------
# SAFE MEDIA SENDER
# -----------------------------

def send_media(chat_id, file_id, caption):

    try:

        bot.send_document(
            chat_id=chat_id,
            document=file_id,
            caption=caption
        )

    except Exception as e:

        print("Media send failed:", e)

# -----------------------------
# LAUNCH SEQUENCE
# -----------------------------

def launch_sequence(chat_id):

    entry = random.choice(SPACESHIP_ENTRY)
    announce = random.choice(AI_ANNOUNCE)

    send_media(chat_id, entry, "🚀 Miserbot Launch Sequence")

    send_media(chat_id, announce, "🤖 AI Station Online")

# -----------------------------
# DROP ENGINE
# -----------------------------

def play_drop(chat_id):

    drop = random.choice(DROPS)

    send_media(chat_id, drop, "🎧 Miserbot Drop")

# -----------------------------
# COMMANDS
# -----------------------------

def start(update, context):

    chat_id = update.effective_chat.id

    launch_sequence(chat_id)

    context.bot.send_message(

        chat_id,

        "🎵 Miserbot Radio Online\n\n"
        "Commands:\n"
        "/radio\n"
        "/drop\n"
        "/shop\n"
        "/mint"

    )

def radio(update, context):

    chat_id = update.effective_chat.id

    context.bot.send_message(chat_id, "📡 Radio Activated")

    play_drop(chat_id)

def drop(update, context):

    chat_id = update.effective_chat.id

    play_drop(chat_id)

def shop(update, context):

    context.bot.send_message(

        update.effective_chat.id,

        "💳 Support Miserbot\nhttps://buy.stripe.com/6oUeVf0Ml7Iv6Wg1PM5Rm00"

    )

def mint(update, context):

    context.bot.send_message(

        update.effective_chat.id,

        "🪙 NFT Drop Coming Soon"

    )

# -----------------------------
# AUDIO CAPTURE HANDLER
# -----------------------------

def capture_audio(update, context):

    message = update.message

    if message.audio:
        print("AUDIO FILE ID:", message.audio.file_id)

    if message.document:
        print("DOCUMENT FILE ID:", message.document.file_id)

    if message.voice:
        print("VOICE FILE ID:", message.voice.file_id)

# -----------------------------
# TELEGRAM DISPATCHER
# -----------------------------

dispatcher = Dispatcher(bot, None, workers=0)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("radio", radio))
dispatcher.add_handler(CommandHandler("drop", drop))
dispatcher.add_handler(CommandHandler("shop", shop))
dispatcher.add_handler(CommandHandler("mint", mint))

dispatcher.add_handler(MessageHandler(Filters.audio | Filters.document | Filters.voice, capture_audio))

# -----------------------------
# TELEGRAM WEBHOOK
# -----------------------------

@app.route("/webhook", methods=["POST"])

def telegram_webhook():

    update = Update.de_json(request.get_json(force=True), bot)

    dispatcher.process_update(update)

    return "ok"

# -----------------------------
# HEALTH CHECK
# -----------------------------

@app.route("/")

def home():

    return "Miserbot Engine Online"

# -----------------------------
# RUN SERVER
# -----------------------------

if __name__ == "__main__":

    print("🚀 MISERBOT ENGINE ONLINE")
    print("Drops:", len(DROPS))

    app.run(host="0.0.0.0", port=PORT)
