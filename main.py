import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")

STRIPE_LINK = "https://buy.stripe.com/6oUeVf0Ml7Iv6Wg1PM5Rm00"


def start(update, context):

    keyboard = [
        [InlineKeyboardButton("ENTER MISERBOT", callback_data="enter")]
    ]

    update.message.reply_text(
        "🚀 Miserbot AI Music Platform\n\n"
        "Preview and purchase digital music directly inside Telegram.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def enter(update, context):

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


def preview(update, context):

    query = update.callback_query
    query.answer()

    query.message.reply_text(
        "🎧 Track preview available after purchase."
    )


def router(update, context):

    data = update.callback_query.data

    if data == "enter":
        enter(update, context)

    elif data == "preview":
        preview(update, context)


def main():

    updater = Updater(BOT_TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(router))

    updater.bot.delete_webhook()

    print("MISERBOT STRIPE REVIEW MODE ONLINE")

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
