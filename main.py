import os
import psycopg2
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

STRIPE_LINK = "https://buy.stripe.com/6oUeVf0Ml7Iv6Wg1PM5Rm00"

INTRO_ONE = "CQACAgEAAxkBAAEdHylp3aw-QZ4nfY6Ttgpdt_u1TzbcXAAC2AYAAgUd8UbUnzcrbr_LQDsE"
INTRO_TWO = "CQACAgEAAxkBAAIKK2ndsNWDw4vXepx1Bonz3aLl77ChAAL2BwACJxTxRmXAatDBwmOOOwQ"

OWNER_EMAIL = "miserbot.ai@gmail.com"

# DATABASE
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS songs(
id SERIAL PRIMARY KEY,
title TEXT,
file_id TEXT
)
""")
conn.commit()

# SONG SEEDS
SEED_SONGS = [

("Boom Boom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("MINI 14","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("Trapp Master","CQACAgEAAxkBAAO3adMZvCO7wgABX5gHZAgzbdkzjbTAAAL4CAACNWeYRsR5hniKcO1iOwQ"),
("Fear","CQACAgEAAxkBAAO1adMZkRh9q3v1hC9COux3YbCwZ4kAAvoIAAI1Z5hGyM8iHzH7apM7BA"),
("Summertime","CQACAgEAAxkBAAOzadMZuYPemhBhe_3R0yVh4Pr6ReMAAvkIAAI1Z5hGx9dnBse1e5M7BA")

]

cur.execute("SELECT COUNT(*) FROM songs")

if cur.fetchone()[0] == 0:

    for title,file_id in SEED_SONGS:
        cur.execute(
            "INSERT INTO songs(title,file_id) VALUES(%s,%s)",
            (title,file_id)
        )

    conn.commit()

# MENU
def main_menu():

    keyboard = [

        [InlineKeyboardButton("🎧 Music Catalog", callback_data="catalog")],
        [InlineKeyboardButton("💎 Vault", callback_data="vault")],
        [InlineKeyboardButton("🛒 Buy Album", url=STRIPE_LINK)],
        [InlineKeyboardButton("🔥 Support Artist", url=STRIPE_LINK)],
        [InlineKeyboardButton("📡 Fan Lounge", callback_data="lounge")],
        [InlineKeyboardButton("📩 Contact", callback_data="contact")]

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
        "🚀 Welcome to Miserbot\n\nPress ENTER to begin.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ENTER
def enter(update, context):

    query = update.callback_query
    query.answer()

    context.bot.send_audio(
        chat_id=query.message.chat_id,
        audio=INTRO_TWO
    )

    query.message.reply_text(
        "🎧 Miserbot Online",
        reply_markup=main_menu()
    )

# CATALOG
def catalog(update, context):

    query = update.callback_query
    query.answer()

    cur.execute("SELECT id,title FROM songs")
    songs = cur.fetchall()

    buttons = []

    for s in songs:
        buttons.append(
            [InlineKeyboardButton(s[1], callback_data=f"song_{s[0]}")]
        )

    query.message.reply_text(
        "🎧 Choose a track",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# PLAY SONG
def play_song(update, context):

    query = update.callback_query
    query.answer()

    song_id = query.data.split("_")[1]

    cur.execute("SELECT file_id FROM songs WHERE id=%s", (song_id,))
    song = cur.fetchone()

    if song:

        context.bot.send_audio(
            chat_id=query.message.chat_id,
            audio=song[0]
        )

# VAULT
def vault(update, context):

    query = update.callback_query
    query.answer()

    query.message.reply_text(
        "💎 Miserbot Vault\n\nUnlock exclusive content.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Unlock Vault", url=STRIPE_LINK)]
        ])
    )

# LOUNGE
def lounge(update, context):

    query = update.callback_query
    query.answer()

    query.message.reply_text(
        "📡 Fan Lounge\nCommunity features coming soon."
    )

# CONTACT
def contact(update, context):

    query = update.callback_query
    query.answer()

    query.message.reply_text(
        f"Contact: {OWNER_EMAIL}"
    )

# ROUTER
def router(update, context):

    data = update.callback_query.data

    if data == "enter":
        enter(update, context)

    elif data == "catalog":
        catalog(update, context)

    elif data.startswith("song_"):
        play_song(update, context)

    elif data == "vault":
        vault(update, context)

    elif data == "lounge":
        lounge(update, context)

    elif data == "contact":
        contact(update, context)

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
