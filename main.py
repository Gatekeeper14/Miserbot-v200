import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

DB = "fans.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def save_fan(user):

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO fans (telegram_id,username) VALUES (?,?)",
        (user.id, user.username)
    )

    conn.commit()
    conn.close()


menu = [
    ["🎵 Music", "💎 Support"],
    ["🎟 Rewards", "📺 Videos"],
    ["🌍 Social"]
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    save_fan(user)

    text = """
🛸 Incoming transmission…

Initializing MiserBot v200…

Alienware neural core online.

👽 Welcome to the Bazragod Universe
"""

    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(menu, resize_keyboard=True)
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message.text

    if msg == "🎵 Music":

        await update.message.reply_text(
"""
Bazragod Catalog

1 Save The Day
2 Boom Boom
3 Legacy
4 Mini 14
5 Stay Far
"""
        )

    elif msg == "💎 Support":

        await update.message.reply_text(
"""
Support Bazragod’s independent movement.

Suggested support:

$5 Supporter
$25 Super Fan
$100 VIP
"""
        )

    elif msg == "🎟 Rewards":

        await update.message.reply_text(
"""
Fan Rewards

Earn points by:

• buying songs
• sharing music
• inviting fans
"""
        )

    elif msg == "📺 Videos":

        await update.message.reply_text(
"""
Watch Bazragod Videos

https://youtube.com/@bazragodmusictravelandleis8835
"""
        )

    elif msg == "🌍 Social":

        await update.message.reply_text(
"""
Follow Bazragod

TikTok
https://www.tiktok.com/@bazragod_official

X
https://x.com/toligarch65693
"""
        )


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    message = " ".join(context.args)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    fans = cur.execute("SELECT telegram_id FROM fans").fetchall()

    for fan in fans:
        try:
            await context.bot.send_message(fan[0], message)
        except:
            pass

    conn.close()

    await update.message.reply_text("Broadcast sent")


def main():

    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT, menu_handler))

    print("MiserBot v200 online")

    app.run_polling()


if __name__ == "__main__":
    main()
