import os
import logging
from telegram.ext import Updater, CommandHandler
from telegram import ReplyKeyboardMarkup

# ==========================
# LOGGING
# ==========================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

print("🚀 MISERBOT V200 STARTING...")

# ==========================
# TOKEN
# ==========================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ BOT_TOKEN missing")
    exit()

print("✅ Bot token loaded")

# ==========================
# KEYBOARD UI
# ==========================
keyboard = [
    ["🎧 Music", "🛒 Store"],
    ["📻 Radio", "💎 Vault"],
    ["🪙 Miser Coins", "🏆 Leaderboard"],
    ["🪪 Passport", "🎟 Events"]
]

reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ==========================
# COMMANDS
# ==========================

def start(update, context):
    print("📥 /start command received")

    update.message.reply_text(
        "🚀 *Welcome to Miserbot*\n\n"
        "Bazragod Network\n\n"
        "Choose a section below:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


def music(update, context):
    print("🎧 music opened")

    update.message.reply_text(
        "🎧 *Music Hub*\n\n"
        "Latest drops coming soon.\n"
        "Exclusive tracks will appear here.",
        parse_mode="Markdown"
    )


def store(update, context):
    print("🛒 store opened")

    update.message.reply_text(
        "🛒 *Miser Store*\n\n"
        "Songs and beats will be available for purchase soon.",
        parse_mode="Markdown"
    )


def radio(update, context):
    print("📻 radio opened")

    update.message.reply_text(
        "📻 *Bazragod Radio*\n\n"
        "Streaming system coming soon.",
        parse_mode="Markdown"
    )


def vault(update, context):
    print("💎 vault opened")

    update.message.reply_text(
        "💎 *Superfan Vault*\n\n"
        "Exclusive album vault coming soon.",
        parse_mode="Markdown"
    )


def coins(update, context):
    print("🪙 coins opened")

    update.message.reply_text(
        "🪙 *Miser Coin Mining*\n\n"
        "Support the music and earn fan points.",
        parse_mode="Markdown"
    )


def leaderboard(update, context):
    print("🏆 leaderboard opened")

    update.message.reply_text(
        "🏆 *Top Supporters*\n\n"
        "Leaderboard system coming soon.",
        parse_mode="Markdown"
    )


def passport(update, context):
    print("🪪 passport opened")

    update.message.reply_text(
        "🪪 *Fan Passport*\n\n"
        "Digital fan passport system coming soon.",
        parse_mode="Markdown"
    )


def events(update, context):
    print("🎟 events opened")

    update.message.reply_text(
        "🎟 *Events & Booking*\n\n"
        "Show bookings and fan events coming soon.",
        parse_mode="Markdown"
    )


# ==========================
# MAIN
# ==========================

def main():

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # COMMAND HANDLERS
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("music", music))
    dp.add_handler(CommandHandler("store", store))
    dp.add_handler(CommandHandler("radio", radio))
    dp.add_handler(CommandHandler("vault", vault))
    dp.add_handler(CommandHandler("coins", coins))
    dp.add_handler(CommandHandler("leaderboard", leaderboard))
    dp.add_handler(CommandHandler("passport", passport))
    dp.add_handler(CommandHandler("events", events))

    print("🤖 Miserbot is alive 🚀")

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
