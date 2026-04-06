import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Flask(__name__)

telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

@app.route("/")
def home():
    return "MiserBot Music System Active"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)

    if update.message:

        # TEXT MESSAGE
        if update.message.text:
            print("TEXT:", update.message.text)

        # AUDIO MESSAGE
        if update.message.audio:
            file_id = update.message.audio.file_id
            title = update.message.audio.title
            print("AUDIO RECEIVED")
            print("TITLE:", title)
            print("FILE ID:", file_id)

            await update.message.reply_text(
                f"🎵 Song received\n\nTitle: {title}\n\nFile ID:\n{file_id}"
            )

    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
