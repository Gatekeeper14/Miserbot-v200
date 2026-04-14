import os
import psycopg2
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# STRIPE PAYMENT LINK
STRIPE_LINK = "https://buy.stripe.com/6oUeVf0Ml7Iv6Wg1PM5Rm00"

# INTRO AUDIO
INTRO_ONE = "CQACAgEAAxkBAAEdHylp3aw-QZ4nfY6Ttgpdt_u1TzbcXAAC2AYAAgUd8UbUnzcrbr_LQDsE"
INTRO_TWO = "CQACAgEAAxkBAAIKK2ndsNWDw4vXepx1Bonz3aLl77ChAAL2BwACJxTxRmXAatDBwmOOOwQ"

# TEST SONG
TEST_SONG = "CQACAgEAAxkBAAIKOWnduI045Aq_xsrkjN7bU3N4QfM7AAL7BwACJxTxRtzJDxdQd9M1OwQ"

# DATABASE
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS purchases(
id SERIAL PRIMARY KEY,
user_id TEXT
)
""")

conn.commit()

# MAIN MENU
def menu():

    keyboard = [

        [InlineKeyboardButton("🎧 Play Demo Song", callback_data="play_song")],

        [InlineKeyboardButton("💰 Buy Song $5", url=STRIPE_LINK)],

        [InlineKeyboardButton("💎 Vault", callback_data="vault")],

        [InlineKeyboardButton("📡 Fan Lounge", callback_data="lounge")],

    ]

    return InlineKeyboardMarkup(keyboard)

# START
def start(update, context):

    context.bot.send_audio(
        chat_id=update.effective_chat.id,
        audio=INTRO_ONE
    )

    keyboard = [[InlineKeyboardButton("ENTER", callback_data="enter")]]

    update.message.reply_text(
        "🚀 Welcome to Miserbot\n\nAI powered music vault.\nPress ENTER.",
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

    query.message.reply_text(
        "🎧 Miserbot Online",
        reply_markup=menu()
    )

# PLAY SONG
def play_song(update, context):

    query = update.callback_query
    query.answer()

    context.bot.send_audio(
        chat_id=query.message.chat_id,
        audio=TEST_SONG
    )

# VAULT
def vault(update, context):

    query = update.callback_query
    query.answer()

    query.message.reply_text(
        "💎 Exclusive vault coming soon."
    )

# LOUNGE
def lounge(update, context):

    query = update.callback_query
    query.answer()

    query.message.reply_text(
        "📡 Fan lounge online."
    )

# ROUTER
def router(update, context):

    data = update.callback_query.data

    if data == "enter":
        enter(update, context)

    elif data == "play_song":
        play_song(update, context)

    elif data == "vault":
        vault(update, context)

    elif data == "lounge":
        lounge(update, context)

# MAIN
def main():

    updater = Updater(BOT_TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(router))

    print("MISERBOT ONLINE")

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
