import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")

# INTRO AUDIO
INTRO_ONE = "CQACAgEAAxkBAAEdHylp3aw-QZ4nfY6Ttgpdt_u1TzbcXAAC2AYAAgUd8UbUnzcrbr_LQDsE"

INTRO_TWO = "CQACAgEAAxkBAAIKK2ndsNWDw4vXepx1Bonz3aLl77ChAAL2BwACJxTxRmXAatDBwmOOOwQ"

# STRIPE PRODUCT LINK
STRIPE_LINK = "https://buy.stripe.com/test"

# START
def start(update, context):

    context.bot.send_audio(
        chat_id=update.effective_chat.id,
        audio=INTRO_ONE
    )

    keyboard = [
        [InlineKeyboardButton("ENTER MISERBOT", callback_data="enter")]
    ]

    update.message.reply_text(
        "🚀 Initializing Miserbot Systems...",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ENTER SYSTEM
def enter(update, context):

    query = update.callback_query
    query.answer()

    context.bot.send_audio(
        chat_id=query.message.chat_id,
        audio=INTRO_TWO
    )

    keyboard = [
        [InlineKeyboardButton("🎧 Preview Track", callback_data="preview")],
        [InlineKeyboardButton("💰 Purchase Track", url=STRIPE_LINK)]
    ]

    query.message.reply_text(
        "Welcome to Miserbot.\n\nPreview the track or purchase full access.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# PREVIEW BUTTON
def preview(update, context):

    query = update.callback_query
    query.answer()

    query.message.reply_text(
        "Track preview system active."
    )


# ROUTER
def router(update, context):

    data = update.callback_query.data

    if data == "enter":
        enter(update, context)

    elif data == "preview":
        preview(update, context)


# MAIN
def main():

    updater = Updater(BOT_TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(router))

    # remove webhook conflict
    updater.bot.delete_webhook()

    print("MISERBOT STRIPE REVIEW MODE ONLINE")

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
