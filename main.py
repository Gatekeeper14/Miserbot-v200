import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext

# ===============================
# CONFIG
# ===============================

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")

STRIPE_LINK = "https://buy.stripe.com/6oUeVf0Ml7Iv6Wg1PM5Rm00"

# ===============================
# AUDIO LIBRARY
# ===============================

library = {
    "intro": [],
    "track": [],
    "drop": [],
    "beat": []
}

# ===============================
# START COMMAND
# ===============================

def start(update: Update, context: CallbackContext):

    keyboard = [
        [InlineKeyboardButton("🚀 ENTER MISERBOT", callback_data="enter")]
    ]

    update.message.reply_text(
        "🚀 Miserbot AI Music Platform\n\n"
        "Preview and purchase digital music directly inside Telegram.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===============================
# ENTER MISERBOT
# ===============================

def enter(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("🎧 Preview Track", callback_data="preview")],
        [InlineKeyboardButton("💳 Buy Track", url=STRIPE_LINK)]
    ]

    query.message.reply_text(
        "Welcome to Miserbot.\n\n"
        "This platform allows fans to preview and purchase exclusive music.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===============================
# PREVIEW TRACK
# ===============================

def preview(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    if library["track"]:
        file_id = library["track"][0]["file"]

        context.bot.send_audio(
            chat_id=query.message.chat_id,
            audio=file_id,
            caption="🎧 Track Preview"
        )

    else:
        query.message.reply_text("🎧 Track preview available after purchase.")

# ===============================
# STORE AUDIO FILES
# ===============================

def store_audio(update: Update, context: CallbackContext):

    audio = update.message.audio

    if not audio:
        return

    name = audio.file_name.lower()
    file_id = audio.file_id

    if name.startswith("intro"):
        key = "intro"

    elif name.startswith("song"):
        key = "track"

    elif name.startswith("drop"):
        key = "drop"

    elif name.startswith("beat"):
        key = "beat"

    else:
        return

    library[key].append({
        "file": file_id,
        "name": audio.file_name
    })

    count = len(library[key])

    update.message.reply_text(
        f"Stored {key.upper()}_{str(count).zfill(3)} — {audio.file_name}"
    )

# ===============================
# MAIN
# ===============================

def main():

    updater = Updater(BOT_TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(enter, pattern="enter"))
    dp.add_handler(CallbackQueryHandler(preview, pattern="preview"))

    dp.add_handler(MessageHandler(Filters.audio, store_audio))
    dp.add_handler(MessageHandler(Filters.document.audio, store_audio))

    print("🚀 MISERBOT ENGINE ONLINE")

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
