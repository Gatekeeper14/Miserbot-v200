import logging

from telegram.ext import (
    Application,
    CommandHandler
)

from config import BOT_TOKEN
from database import init_db, setup_tables

# handlers
from handlers.start import start
from handlers.music import music
from handlers.economy import coins
from handlers.referral import invite

# services
from services.vault import unlock_vault
from services.passport import create_passport
from services.booking import get_packages

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


async def vault(update, context):
    unlock_vault(update.effective_user.id)
    await update.message.reply_text("Vault unlocked.")


async def passport(update, context):
    passport_id = create_passport(update.effective_user.id)
    await update.message.reply_text(f"Your Passport ID: {passport_id}")


async def store(update, context):
    packages = get_packages()

    msg = "Store:\n\n"

    for k, v in packages.items():
        msg += f"{k} - ${v}\n"

    await update.message.reply_text(msg)


async def events(update, context):
    await update.message.reply_text(
        "Events system coming soon."
    )


def main():

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable not set")

    logger.info("Starting Miserbot")

    init_db()
    setup_tables()

    app = Application.builder().token(BOT_TOKEN).build()

    # core commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("music", music))
    app.add_handler(CommandHandler("coins", coins))
    app.add_handler(CommandHandler("invite", invite))

    # ecosystem commands
    app.add_handler(CommandHandler("vault", vault))
    app.add_handler(CommandHandler("passport", passport))
    app.add_handler(CommandHandler("store", store))
    app.add_handler(CommandHandler("events", events))

    logger.info("Handlers loaded")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
