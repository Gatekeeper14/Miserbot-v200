import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")

INTRO_AUDIO = "CQACAgEAAxkBAAEdHylp3aw-QZ4nfY6Ttgpdt_u1TzbcXAAC2AYAAgUd8UbUnzcrbr_LQDsE"

bot = Bot(BOT_TOKEN)

app = Flask(__name__)

def start(update, context):

    chat_id = update.effective_chat.id

    bot.send_message(chat_id, "🚀 Initializing Miserbot Systems...")

    bot.send_audio(
        chat_id=chat_id,
        audio=INTRO_AUDIO,
        caption="🚀 Miserbot Launch Sequence"
    )


dispatcher = Dispatcher(bot, None, workers=0)

dispatcher.add_handler(CommandHandler("start", start))


@app.route("/webhook", methods=["POST"])
def webhook():

    update = Update.de_json(request.get_json(force=True), bot)

    dispatcher.process_update(update)

    return "ok"


@app.route("/")
def home():

    return "Miserbot Engine Running"


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=8080)
