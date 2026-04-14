import os
import logging
import random
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ================================
# CONFIG
# ================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

STRIPE_SINGLE = "https://buy.stripe.com/6oUeVf0Ml7Iv6Wg1PM5Rm00"

OWNER_EMAIL = "miserbot.ai@gmail.com"

INTRO_ONE = "CQACAgEAAxkBAAEdHylp3aw-QZ4nfY6Ttgpdt_u1TzbcXAAC2AYAAgUd8UbUnzcrbr_LQDsE"
INTRO_TWO = "CQACAgEAAxkBAAIKK2ndsNWDw4vXepx1Bonz3aLl77ChAAL2BwACJxTxRmXAatDBwmOOOwQ"

# ================================
# DATABASE
# ================================

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS songs (
id SERIAL PRIMARY KEY,
title TEXT,
file_id TEXT
)
""")

conn.commit()

# ================================
# ORIGINAL SONG SEEDS
# ================================

SEED_SONGS = [

("Boom Boom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("MINI 14","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("Trapp Master","CQACAgEAAxkBAAO3adMZvCO7wgABX5gHZAgzbdkzjbTAAAL4CAACNWeYRsR5hniKcO1iOwQ"),
("Fear","CQACAgEAAxkBAAO1adMZkRh9q3v1hC9COux3YbCwZ4kAAvoIAAI1Z5hGyM8iHzH7apM7BA"),
("Summertime","CQACAgEAAxkBAAOzadMZuYPemhBhe_3R0yVh4Pr6ReMAAvkIAAI1Z5hGx9dnBse1e5M7BA"),

]

# seed songs
cur.execute("SELECT COUNT(*) FROM songs")
if cur.fetchone()[0] == 0:
    for title,file_id in SEED_SONGS:
        cur.execute(
        "INSERT INTO songs (title,file_id) VALUES (%s,%s)",
        (title,file_id)
        )
    conn.commit()

# ================================
# MENU
# ================================

def main_menu():

    keyboard = [

        [InlineKeyboardButton("🎧 Music Catalog",callback_data="catalog")],

        [InlineKeyboardButton("💎 Vault",callback_data="vault")],

        [InlineKeyboardButton("🛒 Buy Album $50",url=STRIPE_SINGLE)],

        [InlineKeyboardButton("🔥 Support Artist",url=STRIPE_SINGLE)],

        [InlineKeyboardButton("📡 Fan Lounge",callback_data="lounge")],

        [InlineKeyboardButton("📩 Contact",callback_data="contact")]

    ]

    return InlineKeyboardMarkup(keyboard)

# ================================
# START
# ================================

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    await update.message.reply_audio(INTRO_ONE)

    await update.message.reply_text(
        "🚀 Welcome to Miserbot\n\n"
        "The AI powered music vault.\n\n"
        "Press ENTER to begin.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ENTER",callback_data="enter")]
        ])
    )

# ================================
# ENTER SYSTEM
# ================================

async def enter(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.message.reply_audio(INTRO_TWO)

    await query.message.reply_text(
        "🎧 Miserbot Online\n\nChoose an option:",
        reply_markup=main_menu()
    )

# ================================
# CATALOG
# ================================

async def catalog(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    cur.execute("SELECT id,title FROM songs")
    songs = cur.fetchall()

    buttons = []

    for song in songs:
        buttons.append(
            [InlineKeyboardButton(song[1],callback_data=f"play_{song[0]}")]
        )

    await query.message.reply_text(
        "🎧 Select a track",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ================================
# PLAY SONG
# ================================

async def play_song(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    song_id = query.data.split("_")[1]

    cur.execute("SELECT file_id FROM songs WHERE id=%s",(song_id,))
    result = cur.fetchone()

    if result:

        await query.message.reply_audio(result[0])

# ================================
# VAULT
# ================================

async def vault(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(

        "💎 Miserbot Vault\n\n"
        "Exclusive content.\n"
        "Rare drops.\n"
        "Premium releases.\n\n"
        "Unlock via supporter tier.",

        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Unlock Vault",url=STRIPE_SINGLE)]
        ])

    )

# ================================
# LOUNGE
# ================================

async def lounge(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(

        "📡 Fan Lounge\n\n"
        "Community zone.\n"
        "Upcoming features:\n"
        "• Leaderboard\n"
        "• Fan radar\n"
        "• Live drops"

    )

# ================================
# CONTACT
# ================================

async def contact(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(

        "📩 Contact\n\n"
        f"{OWNER_EMAIL}"

    )

# ================================
# ROUTER
# ================================

async def router(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    data = query.data

    if data == "enter":

        await enter(update,context)

    elif data == "catalog":

        await catalog(update,context)

    elif data.startswith("play_"):

        await play_song(update,context)

    elif data == "vault":

        await vault(update,context)

    elif data == "lounge":

        await lounge(update,context)

    elif data == "contact":

        await contact(update,context)

# ================================
# MAIN
# ================================

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",start))

    app.add_handler(CallbackQueryHandler(router))

    print("MISERBOT ONLINE")

    app.run_polling()

if __name__ == "__main__":

    main()
