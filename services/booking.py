from telegram import Update
from telegram.ext import ContextTypes


async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = (
        "🎤 Live Events & Bookings\n\n"
        "Book Bazragod for:\n\n"
        "• Club Performances\n"
        "• Private Events\n"
        "• Video Cameos\n"
        "• Studio Sessions\n\n"
        "Booking Packages:\n\n"
        "small_club — $2500\n"
        "medium_club — $5000\n"
        "large_club — $15000\n\n"
        "Contact management for full booking details."
    )

    await update.message.reply_text(message)
