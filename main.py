import logging

from telegram.ext import Application, CommandHandler

from config import BOT_TOKEN
from database import init_db, setup_tables

from handlers.start import start
from handlers.music import music
from handlers.economy import coins
from handlers.referral import invite

from services.booking import get_packages
from services.passport import create_passport
from services.vault import unlock_vault
from services.radio import get_radio_message
from services.supporters import top_supporters


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


async def store(update, context):

    packages = get_packages()

    msg = "🛒 Store\n\n"

    for name, price in packages.items():
        msg += f"{name} - ${price}\n"

    await update.message.reply_text(msg)


async def passport(update, context):

    pid = create_passport(update.effective_user.id)

    await update.message.reply_text(
        f"Your Passport ID: {pid}"
    )


async def events(update, context):

    await update.message.reply_text(
        "Events system coming soon."
    )


async def radio(update, context):

    msg = get_radio_message()

    await update.message.reply_text(msg)


async def supervault(update, context):

    unlock_vault(update.effective_user.id)

    await update.message.reply_text(
        "🔒 Super Vault\n\n"
        "Exclusive content available to Super Fans.\n\n"
        "Unlock price: $500"
    )


async def leaderboard(update, context):

    users = top_supporters()

    if not users:
        await update.message.reply_text("No supporters yet.")
        return

    msg = "🏆 Top Supporters\n\n"

    rank = 1

    for user in users:

        msg += f"{rank}. {user[0]} — {user[1]} coins\n"
        rank += 1

    await update.message.reply_text(msg)


def main():

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable not set")

    logger.info("Starting Miserbot")

    init_db()
    setup_tables()

    app = Application.builder().token(BOT_TOKEN).build()

    # core
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

    logger.info("Handlers loaded")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
