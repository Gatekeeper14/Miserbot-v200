import os
import logging

from telegram.ext import ApplicationBuilder, CommandHandler

# DATABASE
from database import setup_tables

# HANDLERS
from handlers.start import start
from handlers.music import music
from handlers.economy import coins
from handlers.referral import referral
from handlers.store import store

# SERVICES
from services.passport import passport
from services.vault import vault
from services.missions import missions
from services.booking import events
from services.supporters import leaderboard


TOKEN = os.getenv("BOT_TOKEN")


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


def main():

    # Ensure database tables exist
    setup_tables()

    application = ApplicationBuilder().token(TOKEN).build()

    # CORE COMMANDS
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("music", music))
    application.add_handler(CommandHandler("store", store))
    application.add_handler(CommandHandler("coins", coins))

    # ECOSYSTEM
    application.add_handler(CommandHandler("passport", passport))
    application.add_handler(CommandHandler("vault", vault))
    application.add_handler(CommandHandler("missions", missions))
    application.add_handler(CommandHandler("events", events))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("referral", referral))

    # START BOT
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
