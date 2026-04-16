import logging
import os

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler
)

from database import setup_tables

# HANDLERS
from handlers.start import start
from handlers.music import music
from handlers.economy import coins
from handlers.referral import referral

# SERVICES
from services.passport import passport
from services.missions import missions
from services.booking import events
from services.vault import vault
from services.staking import stake
from services.supporters import leaderboard
from services.radio import get_radio_message

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


async def radio(update, context):
    msg = get_radio_message()
    await update.message.reply_text(msg)


def main():

    # CREATE DATABASE TABLES
    setup_tables()

    # CREATE BOT
    application = ApplicationBuilder().token(TOKEN).build()

    # COMMAND HANDLERS
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("music", music))
    application.add_handler(CommandHandler("coins", coins))
    application.add_handler(CommandHandler("vault", vault))
    application.add_handler(CommandHandler("passport", passport))
    application.add_handler(CommandHandler("missions", missions))
    application.add_handler(CommandHandler("stake", stake))
    application.add_handler(CommandHandler("referral", referral))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("events", events))
    application.add_handler(CommandHandler("radio", radio))

    # RUN BOT
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
