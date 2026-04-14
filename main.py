import os
import json
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")

bot = Bot(BOT_TOKEN)

app = Flask(__name__)

# -------------------------
# STORAGE FILE
# -------------------------

AUDIO_DB = "audio_db.json"

if not os.path.exists(AUDIO_DB):
    with open(AUDIO_DB, "w") as f:
        json.dump({"intro": None, "radio": [], "drops": []}, f)


def load_db():
    with open(AUDIO_DB) as f:
        return json.load(f)


def save_db(data):
    with open(AUDIO_DB, "w") as f:
        json.dump(data, f)


# -------------------------
# START COMMAND
# -------------------------

def start(update, context):

    db = load_db()
    chat_id = update.effective_chat.id

    context.bot.send_message(
        chat_id=chat_id,
        text="🚀 Initializing Miserbot Systems..."
    )

    if db["intro"]:

        context.bot.send_audio(
            chat_id=chat_id,
            audio=db["intro"],
            caption="🚀 Miserbot Launch Intro"
        )


# -------------------------
# RADIO COMMAND
# -------------------------

def radio(update, context):

    db = load_db()
    chat_id = update.effective_chat.id

    if db["radio"]:

        context.bot.send_audio(
            chat_id=chat_id,
            audio=db["radio"][0],
            caption="📡 Miserbot Radio Transmission"
        )

    else:

        context.bot.send_message(chat_id, "No radio tracks yet.")


# -------------------------
# DROP COMMAND
# -------------------------

def drop(update, context):

    db = load_db()
    chat_id = update.effective_chat.id

    if db["drops"]:

        context.bot.send_audio(
            chat_id=chat_id,
            audio=db["drops"][0],
            caption="💿 Miserbot Drop"
        )

    else:

        context.bot.send_message(chat_id, "No drops yet.")


# -------------------------
# AUDIO CAPTURE SYSTEM
# -------------------------

def capture_audio(update, context):

    db = load_db()

    file_id = update.message.audio.file_id

    print("NEW AUDIO:", file_id)

    if not db["intro"]:

        db["intro"] = file_id
        context.bot.send_message(update.effective_chat.id, "Intro audio stored.")

    else:

        db["radio"].append(file_id)
        context.bot.send_message(update.effective_chat.id, "Radio track added.")

    save_db(db)


# -------------------------
# DISPATCHER
# -------------------------

dispatcher = Dispatcher(bot, None, workers=0)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("radio", radio))
dispatcher.add_handler(CommandHandler("drop", drop))

dispatcher.add_handler(MessageHandler(Filters.audio, capture_audio))

# -------------------------
# WEBHOOK
# -------------------------

@app.route("/webhook", methods=["POST"])
def webhook():

    update = Update.de_json(request.get_json(force=True), bot)

    dispatcher.process_update(update)

    return "ok"


@app.route("/")
def home():

    return "🚀 Miserbot Engine Running"


if __name__ == "__main__":

    print("🚀 MISERBOT ENGINE ONLINE")

    app.run(host="0.0.0.0", port=8080)
