from telegram import ReplyKeyboardMarkup
from config import INTRO_FILE_ID, FIRST_MESSAGE_FILE_ID

menu = ReplyKeyboardMarkup(
    [
        ["🎧 Music", "🛒 Store"],
        ["💰 MiserCoins", "🏆 Leaderboard"],
        ["💬 Lounge", "⚙️ Support"]
    ],
    resize_keyboard=True
)


async def start(update, context):

    # play intro audio if configured
    if INTRO_FILE_ID and INTRO_FILE_ID.strip() != "":
        try:
            await update.message.reply_voice(INTRO_FILE_ID)
        except Exception as e:
            print(f"Intro audio error: {e}")

    # play second intro message if configured
    if FIRST_MESSAGE_FILE_ID and FIRST_MESSAGE_FILE_ID.strip() != "":
        try:
            await update.message.reply_voice(FIRST_MESSAGE_FILE_ID)
        except Exception as e:
            print(f"First message audio error: {e}")

    # main welcome message
    await update.message.reply_text(
        "🚀 Welcome to Miserbot\n\n"
        "The official ecosystem of Parish 14.\n\n"
        "🎧 Music\n"
        "🛒 Store\n"
        "💰 MiserCoins\n"
        "🏆 Leaderboards\n"
        "💬 Community Lounge\n\n"
        "Use the menu below to explore.",
        reply_markup=menu
    )
