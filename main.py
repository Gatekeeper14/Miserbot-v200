import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import BOT_TOKEN
from database import init_db, setup_tables

# handlers
from handlers.start import start
from handlers.music import music
from handlers.economy import coins
from handlers.referral import invite

# services
from services.radio import get_radio_message
from services.supporters import top_supporters
from services.vault import unlock_vault
from services.passport import create_passport
from services.booking import get_packages


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# STORE
async def store(update, context):

    packages = get_packages()

    msg = "🛒 Store\n\n"

    for name, price in packages.items():
        msg += f"{name} - ${price}\n"

    await update.message.reply_text(msg)


# PASSPORT
async def passport(update, context):

    pid = create_passport(update.effective_user.id)

    await update.message.reply_text(
        f"Your Passport ID: {pid}"
    )


# EVENTS
async def events(update, context):

    await update.message.reply_text(
        "Events system coming soon."
    )


# RADIO
async def radio(update, context):

    msg = get_radio_message()

    await update.message.reply_text(msg)


# SUPER VAULT
async def supervault(update, context):

    unlock_vault(update.effective_user.id)

    await update.message.reply_text(
        "🔒 Super Vault\n\n"
        "Exclusive unreleased content.\n\n"
        "Unlock price: $500 Super Fan Bundle."
    )


# LEADERBOARD
async def leaderboard(update, context):

    users = top_supporters()

    if not users:
        await update.message.reply_text("No supporters yet.")
        return

    msg = "🏆 Top Supporters\n\n"

    rank = 1

    for u in users:
        msg += f"{rank}. {u[0]} — {u[1]} coins\n"
        rank += 1

    await update.message.reply_text(msg)


# MENU ROUTER (buttons)
async def menu_router(update, context):

    text = update.message.text.lower()

    if text == "music":
        await music(update, context)

    elif text == "store":
        await store(update, context)

    elif text == "misercoins":
        await coins(update, context)

    elif text == "leaderboard":
        await leaderboard(update, context)

    elif text == "lounge":
        await update.message.reply_text(
            "Community Lounge:\nhttps://t.me/parish14lounge"
        )

    elif text == "support":
        await update.message.reply_text(
            "Support Artist\n\n"
            "CashApp\nhttps://cash.app/$BAZRAGOD\n\n"
            "PayPal\nhttps://paypal.me/bazragod1"
        )


def main():

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set")

    logger.info("Starting Miserbot")

    init_db()
    setup_tables()

    app = Application.builder().token(BOT_TOKEN).build()

    # core commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("music", music))
    app.add_handler(CommandHandler("coins", coins))
    app.add_handler(CommandHandler("invite", invite))

    # ecosystem
    app.add_handler(CommandHandler("store", store))
    app.add_handler(CommandHandler("passport", passport))
    app.add_handler(CommandHandler("events", events))
    app.add_handler(CommandHandler("radio", radio))
    app.add_handler(CommandHandler("supervault", supervault))
    app.add_handler(CommandHandler("leaderboard", leaderboard))

    # menu buttons
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_router))

    logger.info("Handlers loaded")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
