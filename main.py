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

# ----------------------------------
# MISERBOT INTRO AUDIO
# ----------------------------------

MISERBOT_INTRO = "CQACAgEAAxkBAAEdHylp3aw-QZ4nfY6Ttgpdt_u1TzbcXAAC2AYAAgUd8UbUnzcrbr_LQDsE"

# ----------------------------------
# AUDIO PLAYER
# ----------------------------------

def play_intro(chat_id):

    try:

        bot.send_audio(
            chat_id=chat_id,
            audio=MISERBOT_INTRO,
            caption="🚀 Miserbot Launch Sequence Initiated"
        )

    except Exception as e:

        print("Audio error:", e)

# ----------------------------------
# COMMANDS
# ----------------------------------

def start(update, context):

    chat_id = update.effective_chat.id

    context.bot.send_message(
        chat_id=chat_id,
        text="🚀 Initializing Miserbot Systems..."
    )

    play_intro(chat_id)


def radio(update, context):

    chat_id = update.effective_chat.id

    context.bot.send_message(
        chat_id=chat_id,
        text="📡 Miserbot Radio Transmission"
    )

    play_intro(chat_id)


def drop(update, context):

    chat_id = update.effective_chat.id

    context.bot.send_message(
        chat_id=chat_id,
        text="💿 Miserbot Drop Channel Activated"
    )

    play_intro(chat_id)

# ----------------------------------
# CAPTURE NEW AUDIO IDS
# ----------------------------------

def capture_audio(update, context):

    msg = update.message

    if msg and msg.audio:

        print("AUDIO FILE ID:", msg.audio.file_id)

# ----------------------------------
# TELEGRAM DISPATCHER
# ----------------------------------

dispatcher = Dispatcher(bot, None, workers=0)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("radio", radio))
dispatcher.add_handler(CommandHandler("drop", drop))

dispatcher.add_handler(MessageHandler(Filters.audio, capture_audio))

# ----------------------------------
# WEBHOOK
# ----------------------------------

@app.route("/webhook", methods=["POST"])
def webhook():

    update = Update.de_json(request.get_json(force=True), bot)

    dispatcher.process_update(update)

    return "ok"

@app.route("/")
def home():

    return "🚀 Miserbot Engine Online"

# ----------------------------------
# SERVER START
# ----------------------------------

if __name__ == "__main__":

    print("🚀 MISERBOT ENGINE ONLINE")

    app.run(host="0.0.0.0", port=PORT)
