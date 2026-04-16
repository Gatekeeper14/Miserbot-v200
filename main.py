from telegram.ext import Application,CommandHandler

from config import BOT_TOKEN
from database import init_db,setup_tables

from handlers.start import start
from handlers.music import music
from handlers.economy import coins
from handlers.referral import invite

def main():

    init_db()
    setup_tables()

    app=Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("music",music))
    app.add_handler(CommandHandler("coins",coins))
    app.add_handler(CommandHandler("invite",invite))

    print("MISERBOT ONLINE")

    app.run_polling()

if __name__=="__main__":
    main()
