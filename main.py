import os
import logging
from flask import Flask, request

from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

bot = Bot(token=BOT_TOKEN)

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# -------------------------
# WORKING AUDIO ID
# -------------------------

TEST_DROP = "CQACAgEAAxkBAAIKG2ndokxMFgMYpZoF6EDcVEPkmneqAALxBwACJxTxRi3_dpJIdjsO0wQ"

# -------------------------
# PLAY AUDIO
# -------------------------

def play_audio(chat_id):

    try:

        bot.send_audio(
            chat_id=chat_id,
            audio=TEST_DROP,
            caption="🎧 Miserbot System Intro"
        )

    except Exception as e:

        print("Audio error:", e)

# -------------------------
# COMMANDS
# -------------------------

def start(update, context):

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🚀 Miserbot Online\n\nCommands:\n/drop\n/radio"
    )

def drop(update, context):

    play_audio(update.effective_chat.id)

def radio(update, context):

    play_audio(update.effective_chat.id)

# -------------------------
# CAPTURE NEW AUDIO IDS
# -------------------------

def capture_audio(update, context):

    message = update.message

    if message.audio:
        print("AUDIO FILE ID:", message.audio.file_id)

    if message.document:
        print("DOCUMENT FILE ID:", message.document.file_id)

# -------------------------
# TELEGRAM DISPATCHER
# -------------------------

dispatcher = Dispatcher(bot, None, workers=0)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("drop", drop))
dispatcher.add_handler(CommandHandler("radio", radio))

dispatcher.add_handler(MessageHandler(Filters.audio | Filters.document, capture_audio))

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
