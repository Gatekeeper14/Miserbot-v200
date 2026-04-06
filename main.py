import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes

# Read the token from Railway variables
BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")

app = Flask(__name__)

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

@app.route("/")
def home():
    return "MiserBot Music Capture Active"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)

    if update.message:

        # If text message
        if update.message.text:
            print("TEXT RECEIVED:", update.message.text)

        # If audio message
        if update.message.audio:
            audio = update.message.audio
            file_id = audio.file_id
            title = audio.title if audio.title else "Unknown"

            print("AUDIO RECEIVED")
            print("TITLE:", title)
            print("FILE_ID:", file_id)

            await update.message.reply_text(
                f"🎵 Song received\n\nTitle: {title}\n\nFILE_ID:\n{file_id}"
            )

    return "ok"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
