from telegram import ReplyKeyboardMarkup
from config import INTRO_FILE_ID,FIRST_MESSAGE_FILE_ID

menu=ReplyKeyboardMarkup(
[
["🎧 Music","🛒 Store"],
["💰 MiserCoins","🏆 Leaderboard"],
["💬 Lounge","⚙️ Support"]
],
resize_keyboard=True
)

async def start(update,context):

    if INTRO_FILE_ID:
        await update.message.reply_voice(INTRO_FILE_ID)

    if FIRST_MESSAGE_FILE_ID:
        await update.message.reply_voice(FIRST_MESSAGE_FILE_ID)

    await update.message.reply_text(
        "Welcome to Miserbot ecosystem.",
        reply_markup=menu
    )
