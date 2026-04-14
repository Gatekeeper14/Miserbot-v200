import os
import psycopg2
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# ================================
# ENV VARIABLES
# ================================

BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# ================================
# STRIPE PAYMENT LINK
# ================================

STRIPE_LINK = "https://buy.stripe.com/test_purchase_link"

# ================================
# AUDIO FILE IDS
# ================================

INTRO_ONE = "CQACAgEAAxkBAAEdHylp3aw-QZ4nfY6Ttgpdt_u1TzbcXAAC2AYAAgUd8UbUnzcrbr_LQDsE"

INTRO_TWO = "CQACAgEAAxkBAAIKK2ndsNWDw4vXepx1Bonz3aLl77ChAAL2BwACJxTxRmXAatDBwmOOOwQ"

DEMO_SONG = "CQACAgEAAxkBAAIKOWnduI045Aq_xsrkjN7bU3N4QfM7AAL7BwACJxTxRtzJDxdQd9M1OwQ"

# ================================
# DATABASE INIT
# ================================

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS purchases(
id SERIAL PRIMARY KEY,
user_id TEXT
)
""")

conn.commit()

# ================================
# MENU
# ================================

def main_menu():

    keyboard = [

        [InlineKeyboardButton("🎧 Play Demo Song", callback_data="play_song")],

        [InlineKeyboardButton("💰 Buy Song $5", url=STRIPE_LINK)],

        [InlineKeyboardButton("💎 Vault", callback_data="vault")],

        [InlineKeyboardButton("📡 Fan Lounge", callback_data="lounge")]

    ]

    return InlineKeyboardMarkup(keyboard)

# ================================
# START COMMAND
# ================================

def start(update, context):

    chat_id = update.effective_chat.id

    context.bot.send_audio(
        chat_id=chat_id,
        audio=INTRO_ONE
    )

    keyboard = [

        [InlineKeyboardButton("ENTER MISERBOT", callback_data="enter")]

    ]

    update.message.reply_text(
        "🚀 Initializing Miserbot Systems...",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================================
# ENTER SYSTEM
# ================================

def enter(update, context):

    query = update.callback_query
    query.answer()

    chat_id = query.message.chat_id

    context.bot.send_audio(
        chat_id=chat_id,
        audio=INTRO_TWO
    )

    query.message.reply_text(
        "🎧 Miserbot Engine Online",
        reply_markup=main_menu()
    )

# ================================
# PLAY SONG
# ================================

def play_song(update, context):

    query = update.callback_query
    query.answer()

    chat_id = query.message.chat_id

    context.bot.send_audio(
        chat_id=chat_id,
        audio=DEMO_SONG
    )

# ================================
# VAULT
# ================================

def vault(update, context):

    query = update.callback_query
    query.answer()

    query.message.reply_text(
        "💎 Miserbot Vault Coming Soon."
    )

# ================================
# FAN LOUNGE
# ================================

def lounge(update, context):

    query = update.callback_query
    query.answer()

    query.message.reply_text(
        "📡 Fan Lounge Online."
    )

# ================================
# ROUTER
# ================================

def router(update, context):

    query = update.callback_query

    data = query.data

    if data == "enter":

        enter(update, context)

    elif data == "play_song":

        play_song(update, context)

    elif data == "vault":

        vault(update, context)

    elif data == "lounge":

        lounge(update, context)

# ================================
# MAIN
# ================================

def main():

    updater = Updater(BOT_TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(CallbackQueryHandler(router))

    print("🚀 MISERBOT ENGINE ONLINE")

    updater.start_polling()

    updater.idle()

# ================================

if __name__ == "__main__":

    main()
