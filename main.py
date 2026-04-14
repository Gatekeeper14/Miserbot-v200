import os
import logging
from flask import Flask, request

from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

# -------------------------
# ENVIRONMENT
# -------------------------

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

bot = Bot(token=BOT_TOKEN)

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# -------------------------
# TEST AUDIO (CONFIRMED ID)
# -------------------------

TEST_DROP = "CQACAgEAAxkBAAIKEmndmn-7gCxnjGdcGpCVHgKUN3-nAALtBwACJ_MR8FQ03jiOwQ"

# -------------------------
# SEND AUDIO FUNCTION
# -------------------------

def send_drop(chat_id):

    try:

        bot.send_audio(
            chat_id=chat_id,
            audio=TEST_DROP,
            caption="🎧 Miserbot Test Drop"
        )

    except Exception as e:

        print("Audio send failed:", e)

# -------------------------
# COMMANDS
# -------------------------

def start(update, context):

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🚀 Miserbot Engine Online\n\nTry /drop"
    )

def drop(update, context):

    send_drop(update.effective_chat.id)

def radio(update, context):

    send_drop(update.effective_chat.id)

# -------------------------
# UNIVERSAL MESSAGE LOGGER
# -------------------------

def capture_everything(update, context):

    message = update.message

    if not message:
        return

    print("FULL UPDATE:", update.to_dict())

    if message.audio:
        print("AUDIO FILE ID:", message.audio.file_id)

    if message.document:
        print("DOCUMENT FILE ID:", message.document.file_id)

    if message.voice:
        print("VOICE FILE ID:", message.voice.file_id)

    if message.video:
        print("VIDEO FILE ID:", message.video.file_id)

# -------------------------
# TELEGRAM DISPATCHER
# -------------------------

dispatcher = Dispatcher(bot, None, workers=0)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("drop", drop))
dispatcher.add_handler(CommandHandler("radio", radio))

# THIS CAPTURES ALL MESSAGES
dispatcher.add_handler(MessageHandler(Filters.all, capture_everything))

# -------------------------
# TELEGRAM WEBHOOK
# -------------------------

@app.route("/webhook", methods=["POST"])
def telegram_webhook():

    update = Update.de_json(request.get_json(force=True), bot)

    dispatcher.process_update(update)

    return "ok"

# -------------------------
# HEALTH CHECK
# -------------------------

@app.route("/")
def home():

    return "Miserbot Running"

# -------------------------
# START SERVER
# -------------------------

if __name__ == "__main__":

    print("🚀 MISERBOT ENGINE ONLINE")

    app.run(host="0.0.0.0", port=PORT)
