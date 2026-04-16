import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

MINI_APP_URL = "https://miserbot-site.vercel.app"
RADIO_LINK = "https://t.me/bazragodradio"
LOUNGE_LINK = "https://t.me/parish14lounge"
STORE_LINK = "https://buy.stripe.com/6oUeVf0Ml7Iv6Wg1PM5Rm00"

user_coins = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(name)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    web_app = WebAppInfo(url=MINI_APP_URL)

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("🚀 Open Bazragod Network", web_app=web_app)],
            ["🛒 Store", "📻 Radio"],
            ["💬 Lounge", "🪙 Coins"],
            ["👥 Invite"]
        ],
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🚀 Welcome to Bazragod Network\n\nMusic • Store • Radio • Community",
        reply_markup=keyboard
    )


async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        f"🛒 Miser Store\n\nBuy the bundle here:\n{STORE_LINK}"
    )


async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        f"📻 Bazragod Radio\n\n{RADIO_LINK}"
    )


async def lounge(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        f"💬 Join the Parish Lounge\n\n{LOUNGE_LINK}"
    )


async def coins(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    user_coins[user] = user_coins.get(user, 0) + 1

    await update.message.reply_text(
        f"🪙 Miser Coin earned\n\nTotal: {user_coins[user]}"
    )


async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):

    bot_username = (await context.bot.get_me()).username
    user_id = update.effective_user.id

    invite_link = f"https://t.me/{bot_username}?start={user_id}"

    await update.message.reply_text(
        f"👥 Invite friends\n\n{invite_link}"
    )


async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🛒 Store":
        await store(update, context)

    elif text == "📻 Radio":
        await radio(update, context)

    elif text == "💬 Lounge":
        await lounge(update, context)

    elif text == "🪙 Coins":
        await coins(update, context)

    elif text == "👥 Invite":
        await invite(update, context)


def main():

    logger.info("🚀 MISERBOT STARTING")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("invite", invite))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

    logger.info("🚀 MISERBOT RUNNING")

    app.run_polling()


if name == "main":
    main()
