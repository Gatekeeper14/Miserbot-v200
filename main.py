import os
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
# TEST AUDIO ID
# -----------------------------

TEST_DROP = "CQACAgEAAxkBAAIKEmndmn-7gCxnjGdcGpCVHgKUN3-nAALtBwACJ_MR8FQ03jiOwQ"

# -----------------------------
# SAFE MEDIA SENDER
# -----------------------------

def send_audio(chat_id, file_id, caption):

    try:

        bot.send_document(
            chat_id=chat_id,
            document=file_id,
            caption=caption
        )

    except Exception as e:

        print("Media send failed:", e)

# -----------------------------
# COMMANDS
# -----------------------------

def start(update, context):

    chat_id = update.effective_chat.id

    context.bot.send_message(
        chat_id,
        "🚀 Miserbot Engine Online\n\n"
        "Commands:\n"
        "/drop\n"
        "/radio\n"
        "/shop"
    )

def drop(update, context):

    chat_id = update.effective_chat.id

    send_audio(chat_id, TEST_DROP, "🎧 Miserbot Test Drop")

def radio(update, context):

    chat_id = update.effective_chat.id

    send_audio(chat_id, TEST_DROP, "📡 Miserbot Radio Test")

def shop(update, context):

    context.bot.send_message(
        update.effective_chat.id,
        "💳 Support Miserbot\nhttps://buy.stripe.com/6oUeVf0Ml7Iv6Wg1PM5Rm00"
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
dispatcher.add_handler(CommandHandler("drop", drop))
dispatcher.add_handler(CommandHandler("radio", radio))
dispatcher.add_handler(CommandHandler("shop", shop))

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

    app.run(host="0.0.0.0", port=PORT)
