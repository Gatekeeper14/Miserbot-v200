import os
import random
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
BOT_USERNAME = "miserbot"

WEBHOOK_PATH = "/webhook"

INTRO_FILE_ID = "CQACAgEAAxkBAAICN2nUZHzzXlQszP-a08nJiSctUeOhAAL-BQACEbKpRg3vpxJvYve3OwQ"

ADMIN_ID = 8741545426

app = Flask(__name__)

telegram_app = Application.builder().token(BOT_TOKEN).build()

# MUSIC CATALOG
SONGS = [
("Chibonge Remix Rap Version","CQACAgEAAxkBAAOtadMWVB7xX8ss7Nkp6neA0L7gbU0AAvQIAAI1Z5hGYMUV7Mozbyw7BA"),
("Natural Pussy (Tie Mi)","CQACAgEAAxkBAAO1adMZtjgiRqYxrOFbE3KOCNxVcxQAAvgIAAI1Z5hGm8QmWqNIojg7BA"),
("Fraid Ah Yuh","CQACAgEAAxkBAAO3adMZ_P5y2OoXlyY0XpO_fiPiahMAAvkIAAI1Z5hGgMZ1tOmyhjA7BA"),
("Mini 14 Raw","CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
("Boom Boom","CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
("Summertime","CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA"),
("Mini 14 HD Mix","CQACAgEAAxkBAAPBadMcgWIUbXd6lfNjIt8C_SMhpz8AAv4IAAI1Z5hGrA8jfr5073A7BA"),
("Carry Guh Bring Come","CQACAgEAAxkBAAPFadMdgVBA0MIwyLNyU8mO5-djfawAAgQJAAI1Z5hGYmzehzRMIZY7BA"),
("Trapp","CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
("Gunman","CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
]

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["🎵 Music","📻 Radio"],
        ["💰 Support Artist","🌐 Social"],
        ["👑 Wisdom","🏋 Fitness"]
    ]

    await update.message.reply_text(
        "👑 Welcome to I.A.A.I.M.O\n\nPress Music to explore the catalog.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# MUSIC MENU
async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):

    buttons = []

    for i, song in enumerate(SONGS):
        buttons.append([InlineKeyboardButton(song[0], callback_data=f"song:{i}")])

    await update.message.reply_text(
        "🎧 BAZRAGOD MUSIC CATALOG",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# PLAY SONG
async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    idx = int(query.data.split(":")[1])
    song = SONGS[idx]

    await query.message.reply_audio(
        audio=song[1],
        caption=f"🎵 {song[0]}\n\nBAZRAGOD"
    )

# SIMPLE RADIO (random track)
async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    song = random.choice(SONGS)

    await update.message.reply_audio(
        audio=song[1],
        caption=f"📻 BAZRAGOD RADIO\n\nNow Playing:\n{song[0]}"
    )

# SOCIAL
async def social(update: Update, context: ContextTypes.DEFAULT_TYPE):

    buttons = [
        [InlineKeyboardButton("Instagram", url="https://www.instagram.com/bazragod_timeless")],
        [InlineKeyboardButton("TikTok", url="https://www.tiktok.com/@bazragod_official")],
        [InlineKeyboardButton("YouTube", url="https://youtube.com/@bazragodmusictravelandleis8835")],
        [InlineKeyboardButton("X", url="https://x.com/toligarch65693")]
    ]

    await update.message.reply_text(
        "🌐 Follow BAZRAGOD everywhere:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# SUPPORT
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    buttons = [
        [InlineKeyboardButton("CashApp", url="https://cash.app/$BAZRAGOD")],
        [InlineKeyboardButton("PayPal", url="https://paypal.me/bazragod1")]
    ]

    await update.message.reply_text(
        "💰 Support the artist directly:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ROUTER
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🎵 Music":
        await music(update, context)

    elif text == "📻 Radio":
        await radio(update, context)

    elif text == "💰 Support Artist":
        await support(update, context)

    elif text == "🌐 Social":
        await social(update, context)

# HANDLERS
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(play_song, pattern="song:"))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

# WEBHOOK
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():

    update = Update.de_json(request.get_json(force=True), telegram_app.bot)

    asyncio.get_event_loop().create_task(
        telegram_app.process_update(update)
    )

    return "ok"

# HEALTH CHECK
@app.route("/health")
def health():
    return "MISERBOT ONLINE", 200

# START SERVER
if __name__ == "__main__":

    telegram_app.initialize()
    telegram_app.start()

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )
