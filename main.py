import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load bot token from Railway variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Mini App URL (Vercel site)
MINI_APP_URL = "https://miserbot-site.vercel.app"

# Stripe payment link
STRIPE_LINK = "https://buy.stripe.com/6oUeVf0Ml7Iv6Wg1PM5Rm00"

logging.basicConfig(
format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
level=logging.INFO
)

logger = logging.getLogger(name)

# Fan coin storage
user_coins = {}
leaderboard = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    web_app = WebAppInfo(MINI_APP_URL)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("🚀 Open Bazragod Network", web_app=web_app)],
            ["🎧 Music", "💎 Vault"],
            ["🛒 Store", "📻 Radio"],
            ["🪙 Miser Coins", "🏆 Leaderboard"],
            ["🎟 Events", "🪪 Passport"]
        ],
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🚀 Welcome to Bazragod Network\n\n"
        "Use the buttons below to explore music, radio, store and fan features.",
        reply_markup=keyboard
    )


async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        f"🛒 Purchase music or support the network:\n\n{STRIPE_LINK}"
    )


async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🎧 Music player is available inside the Mini App.\n\n"
        "Press 🚀 Open Bazragod Network."
    )


async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📻 Radio stream is available inside the Mini App."
    )


async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in user_coins:
        user_coins[user] = 0

    user_coins[user] += 1

    leaderboard[user] = user_coins[user]

    await update.message.reply_text(
        f"🪙 Miser Coin mined!\n\nTotal coins: {user_coins[user]}"
    )


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not leaderboard:
        await update.message.reply_text("🏆 Leaderboard is empty.")
        return

    sorted_board = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

    text = "🏆 Top Fans\n\n"

    rank = 1

    for user, coins in sorted_board[:10]:
        text += f"{rank}. {coins} coins\n"
        rank += 1

    await update.message.reply_text(text)


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🛒 Store":
        await store(update, context)

    elif text == "🎧 Music":
        await music(update, context)

    elif text == "📻 Radio":
        await radio(update, context)

    elif text == "🪙 Miser Coins":
        await mine(update, context)

    elif text == "🏆 Leaderboard":
        await show_leaderboard(update, context)

    elif text == "💎 Vault":
        await update.message.reply_text(
            "💎 Superfan Vault is available inside the Mini App."
        )

    elif text == "🎟 Events":
        await update.message.reply_text(
            "🎟 Upcoming events will appear here."
        )

    elif text == "🪪 Passport":
        await update.message.reply_text(
            "🪪 Digital fan passport system coming soon."
        )


def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    print("🚀 Miserbot is alive")

    app.run_polling()


if name == "main":
    main()
