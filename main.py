import os
import time
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# --------------------------------------------------
# MISERBOT INTRO AUDIO
# --------------------------------------------------

INTRO_1 = "CQACAgEAAxkBAAIKK2ndsNWDw4vXepx1Bonz3aLl77ChAAL2BwACJxTxRmXAatDBwmOOOwQ"
INTRO_2 = "CQACAgEAAxkBAAIKLWndsrqyp_ur3KtH0U80a5hnv1_JAAL4BwACJxTxRj1RYRoqPLiXOwQ"


# --------------------------------------------------
# START COMMAND
# --------------------------------------------------

def start(update, context):

    chat_id = update.effective_chat.id

    context.bot.send_message(
        chat_id=chat_id,
        text="🚀 Initializing Miserbot Systems..."
    )

    try:

        context.bot.send_audio(
            chat_id=chat_id,
            audio=INTRO_1,
            caption="🚀 Miserbot Launch Sequence"
        )

        time.sleep(2)

        context.bot.send_audio(
            chat_id=chat_id,
            audio=INTRO_2,
            caption="🎙 Miserbot Creator Transmission"
        )

    except Exception as e:

        print("INTRO ERROR:", e)


# --------------------------------------------------
# RADIO COMMAND
# --------------------------------------------------

def radio(update, context):

    context.bot.send_audio(
        chat_id=update.effective_chat.id,
        audio=INTRO_1,
        caption="📡 Miserbot Radio Test"
    )


# --------------------------------------------------
# DROP COMMAND
# --------------------------------------------------

def drop(update, context):

    context.bot.send_audio(
        chat_id=update.effective_chat.id,
        audio=INTRO_2,
        caption="💿 Miserbot Drop Test"
    )


# --------------------------------------------------
# CAPTURE NEW AUDIO IDS
# --------------------------------------------------

def capture_audio(update, context):

    if update.message.audio:

        print("NEW AUDIO:", update.message.audio.file_id)


# --------------------------------------------------
# TELEGRAM DISPATCHER
# --------------------------------------------------

dispatcher = Dispatcher(bot, None, workers=0)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("radio", radio))
dispatcher.add_handler(CommandHandler("drop", drop))

dispatcher.add_handler(MessageHandler(Filters.audio, capture_audio))


# --------------------------------------------------
# WEBHOOK
# --------------------------------------------------

@app.route("/webhook", methods=["POST"])
def telegram_webhook():

    update = Update.de_json(request.get_json(force=True), bot)

    dispatcher.process_update(update)

    return "ok"


@app.route("/")
def home():

    return "🚀 Miserbot Engine Online"


# --------------------------------------------------
# SERVER START
# --------------------------------------------------

if __name__ == "__main__":

    print("🚀 MISERBOT ENGINE ONLINE")

    app.run(host="0.0.0.0", port=8080)
