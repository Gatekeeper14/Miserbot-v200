from telegram import Update
from telegram.ext import ContextTypes


async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = (
        "🛒 Miserbot Store\n\n"
        "Available items:\n\n"
        "feature — $5000\n"
        "studio_bundle — $1200\n"
        "video_cameo — $1200\n"
        "small_club — $2500\n"
        "medium_club — $5000\n"
        "large_club — $15000\n"
        "fan_photo — $50\n"
        "backstage — $250\n"
        "donation — $1\n\n"
        "More items coming soon."
    )

    await update.message.reply_text(message)
