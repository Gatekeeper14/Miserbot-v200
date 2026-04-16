from telegram import Update
from telegram.ext import ContextTypes
import random

from database import get_conn, release_conn


async def passport(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT passport_id
        FROM passports
        WHERE user_id = %s
    """, (user_id,))

    result = cur.fetchone()

    if result:

        passport_id = result[0]

    else:

        passport_id = f"P14-{random.randint(100000,999999)}"

        cur.execute("""
            INSERT INTO passports(user_id, passport_id)
            VALUES(%s,%s)
        """, (user_id, passport_id))

        conn.commit()

    release_conn(conn)

    message = (
        "🪪 Miserbot Passport\n\n"
        f"Your Passport ID: {passport_id}\n\n"
        "You are now a verified citizen of the Miserbot ecosystem."
    )

    await update.message.reply_text(message)
