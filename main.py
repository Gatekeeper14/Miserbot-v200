import logging

from telegram.ext import (
    Application,
    CommandHandler,
)

from config import BOT_TOKEN
from database import init_db, setup_tables

# handlers
from handlers.start import start
from handlers.music import music
from handlers.economy import coins
from handlers.referral import invite

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def main():

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable not set")

    logger.info("Starting Miserbot...")

    # initialize database connection pool
    init_db()

    # create tables if missing
    setup_tables()

    # build telegram app
    app = Application.builder().token(BOT_TOKEN).build()

    # register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("music", music))
    app.add_handler(CommandHandler("coins", coins))
    app.add_handler(CommandHandler("invite", invite))

    logger.info("Handlers loaded")

    # run polling (Railway safe)
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=None
    )


if __name__ == "__main__":
    main()
