from telegram import Update
from telegram.ext import ContextTypes

from database import get_conn, release_conn


async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    invite_link = f"https://t.me/{context.bot.username}?start={user_id}"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM referrals
        WHERE referrer = %s
    """, (user_id,))

    count = cur.fetchone()[0]

    release_conn(conn)

    message = (
        "👥 Referral System\n\n"
        f"Your Invite Link:\n{invite_link}\n\n"
        f"Total Referrals: {count}\n\n"
        "Earn MiserCoins when friends join."
    )

    await update.message.reply_text(message)
