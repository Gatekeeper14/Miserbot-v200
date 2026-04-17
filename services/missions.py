from telegram import Update
from telegram.ext import ContextTypes


async def missions(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = (
        "🎯 Miserbot Missions\n\n"
        "Complete tasks to earn MiserCoins.\n\n"
        "Available Missions:\n\n"
        "• Join Community Channel\n"
        "• Share Miserbot with friends\n"
        "• Listen to Radio\n"
        "• Support the ecosystem\n\n"
        "More missions coming soon."
    )

    await update.message.reply_text(message)
