from telegram import Update
from telegram.ext import ContextTypes
from database import get_conn, release_conn


async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT title, artist, price
        FROM songs
        ORDER BY created_at DESC
        LIMIT 20
    """)

    songs = cur.fetchall()
    release_conn(conn)

    if not songs:
        await update.message.reply_text(
            "🎧 Music Hub\n\n"
            "No songs uploaded yet."
        )
        return

    msg = "🎧 Music Hub\n\n"

    for title, artist, price in songs:
        msg += f"{title} — {artist} (${price})\n"

    await update.message.reply_text(msg)
