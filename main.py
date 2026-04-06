import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")

app = Flask(__name__)

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

@app.route("/")
def home():
    return "MiserBot running"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():

    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)

    if update.message:

        if update.message.audio:
            audio = update.message.audio
            file_id = audio.file_id
            title = audio.title if audio.title else "Unknown"

            print("AUDIO RECEIVED")
            print("TITLE:", title)
            print("FILE ID:", file_id)

            asyncio.run(
                telegram_app.bot.send_message(
                    chat_id=update.message.chat.id,
                    text=f"🎵 Song received\n\nTitle: {title}\n\nFILE_ID:\n{file_id}"
                )
            )

        elif update.message.text:
            print("TEXT RECEIVED:", update.message.text)

    return "ok"


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(host="0.0.0.0", port=port)
