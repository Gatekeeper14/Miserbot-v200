import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# ------------------------------
# AUDIO IDS
# ------------------------------

INTRO_1 = "CQACAgEAAxkBAAIKK2ndsNWDw4vXepx1Bonz3aLl77ChAAL2BwACJxTxRmXAatDBwmOOOwQ"

INTRO_2 = "CQACAgEAAxkBAAIKLWndsrqyp_ur3KtH0U80a5hnv1_JAAL4BwACJxTxRj1RYRoqPLiXOwQ"

SONG_1 = "CQACAgEAAxkBAAIKOWnduI045Aq_xsrkjN7bU3N4QfM7AAL7BwACJxTxRtzJDxdQd9M1OwQ"


# ------------------------------
# PLAYLIST
# ------------------------------

PLAYLIST = [

INTRO_1,
INTRO_2,
SONG_1,
INTRO_2

]

playlist_index = 0


# ------------------------------
# START
# ------------------------------

def start(update, context):

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🚀 Miserbot System Ready"
    )


# ------------------------------
# RADIO / PLAY NEXT
# ------------------------------

def radio(update, context):

    global playlist_index

    chat_id = update.effective_chat.id

    audio_id = PLAYLIST[playlist_index]

    context.bot.send_audio(
        chat_id=chat_id,
        audio=audio_id
    )

    playlist_index += 1

    if playlist_index >= len(PLAYLIST):

        playlist_index = 0


# ------------------------------
# DISPATCHER
# ------------------------------

dispatcher = Dispatcher(bot, None, workers=0)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("radio", radio))


# ------------------------------
# WEBHOOK
# ------------------------------

@app.route("/webhook", methods=["POST"])
def telegram_webhook():

    update = Update.de_json(request.get_json(force=True), bot)

    dispatcher.process_update(update)

    return "ok"


@app.route("/")
def home():

    return "Miserbot Engine Running"


# ------------------------------
# SERVER
# ------------------------------

if __name__ == "__main__":

    print("🚀 MISERBOT ENGINE ONLINE")

    app.run(host="0.0.0.0", port=8080)
