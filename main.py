from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

main_menu = ReplyKeyboardMarkup(
    [
        ["🎵 Music", "🌍 Radar"],
        ["✈️ Travel", "🏆 Fans"]
    ],
    resize_keyboard=True
)

music_menu = ReplyKeyboardMarkup(
    [
        ["🎵 Music Drops"],
        ["💎 Support Mission"],
        ["🏆 Top Fans"],
        ["🎁 Fan Rewards"],
        ["⬅️ Back"]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛸 MiserBot v200 activated\n\nWelcome to the command system.",
        reply_markup=main_menu
    )

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🎵 Music":
        await update.message.reply_text(
            "VIP Artist Hub",
            reply_markup=music_menu
        )

    elif text == "🎵 Music Drops":
        await update.message.reply_text(
            "Bazragod Catalog\n\n"
            "1️⃣ Legacy\n"
            "2️⃣ Save The Day\n"
            "3️⃣ Boom Boom\n"
            "4️⃣ Tonight\n"
            "5️⃣ Mini 14\n\n"
            "Tap a number to download."
        )

    elif text == "💎 Support Mission":
        await update.message.reply_text(
            "Support Bazragod's independent journey.\n\n"
            "$5 Support\n"
            "$25 Support\n"
            "$100 Support\n"
            "$500 Patron\n"
            "$10,000 Executive Support"
        )

    elif text == "🏆 Top Fans":
        await update.message.reply_text(
            "Top Supporters\n\n"
            "1️⃣ Coming Soon\n"
            "2️⃣ Coming Soon\n"
            "3️⃣ Coming Soon"
        )

    elif text == "🎁 Fan Rewards":
        await update.message.reply_text(
            "Fan Missions\n\n"
            "Invite friends\n"
            "Share music\n"
            "Earn rewards."
        )

    elif text == "⬅️ Back":
        await update.message.reply_text(
            "Main Menu",
            reply_markup=main_menu
        )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_menu))

    print("🚀 MiserBot v200 running")
    app.run_polling()

if __name__ == "__main__":
    main()
