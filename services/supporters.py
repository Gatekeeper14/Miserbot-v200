from telegram import Update
from telegram.ext import ContextTypes
from database import get_conn, release_conn


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, balance
        FROM misercoins
        ORDER BY balance DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    release_conn(conn)

    if not rows:
        await update.message.reply_text("🏆 Leaderboard is empty.")
        return

    message = "🏆 Top Miserbot Supporters\n\n"

    rank = 1
    for user_id, balance in rows:
        message += f"{rank}. User {user_id} — {balance} coins\n"
        rank += 1

    await update.message.reply_text(message)
