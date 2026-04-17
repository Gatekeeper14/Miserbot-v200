from telegram import Update
from telegram.ext import ContextTypes


async def vault(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = (
        "🔐 Miserbot Vault\n\n"
        "Exclusive content is stored inside the Vault.\n\n"
        "Unlock access by:\n"
        "• Supporting the ecosystem\n"
        "• Staking MiserCoins\n"
        "• Completing missions\n\n"
        "Vault drops will appear here."
    )

    await update.message.reply_text(message)
