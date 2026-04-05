import os
import random
import psycopg2
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ─────────────────────────
# ENV VARIABLES
# ─────────────────────────

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
DATABASE_URL = os.environ.get("DATABASE_URL")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

# ─────────────────────────
# DATABASE CONNECTION
# ─────────────────────────

def get_db():
    return psycopg2.connect(DATABASE_URL)

# ─────────────────────────
# INIT DATABASE
# ─────────────────────────

def init_db():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans(
        telegram_id BIGINT PRIMARY KEY,
        username TEXT,
        xp INTEGER DEFAULT 0,
        joined TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS songs(
        id SERIAL PRIMARY KEY,
        title TEXT,
        plays INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS donations(
        id SERIAL PRIMARY KEY,
        fan_id BIGINT,
        amount NUMERIC,
        created TIMESTAMP
    )
    """)

    conn.commit()
    cur.close()
    conn.close()

# ─────────────────────────
# FAN SYSTEM
# ─────────────────────────

def add_fan(user):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO fans (telegram_id, username, joined)
    VALUES (%s,%s,%s)
    ON CONFLICT (telegram_id) DO NOTHING
    """, (user.id, user.username, datetime.utcnow()))

    conn.commit()
    cur.close()
    conn.close()

def add_xp(user_id, amount):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE fans SET xp = xp + %s WHERE telegram_id = %s",
        (amount, user_id)
    )

    conn.commit()
    cur.close()
    conn.close()

# ─────────────────────────
# FAN MENU
# ─────────────────────────

def fan_menu():

    return ReplyKeyboardMarkup(
        [
            ["🎵 Music", "🏆 Fans"],
            ["📡 Radar", "🌍 Map"],
            ["🛍 PARISH 14", "💰 Support"]
        ],
        resize_keyboard=True
    )

# ─────────────────────────
# START COMMAND
# ─────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    add_fan(user)

    msg = f"""
👑 Welcome to the Kingdom of BAZRAGOD

You have entered MiserBot.

🎵 Stream exclusive music
🛍 Access PARISH 14 merch
💰 Support the artist
🌍 Join the global fan kingdom
"""

    await update.message.reply_text(msg, reply_markup=fan_menu())

# ─────────────────────────
# MUSIC SYSTEM
# ─────────────────────────

async def music(update: Update, ctx: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT title, plays FROM songs")
    songs = cur.fetchall()

    cur.close()
    conn.close()

    if not songs:
        await update.message.reply_text("🎵 Music catalog coming soon.")
        return

    text = "🎵 BAZRAGOD Catalog\n\n"

    for s in songs:
        text += f"{s[0]} — {s[1]} plays\n"

    add_xp(update.effective_user.id, 5)

    await update.message.reply_text(text)

# ─────────────────────────
# FAN LEADERBOARD
# ─────────────────────────

async def fans(update: Update, ctx: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT username, xp
    FROM fans
    ORDER BY xp DESC
    LIMIT 5
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    text = "🏆 Top Supporters\n\n"

    for r in rows:
        text += f"{r[0]} — {r[1]} XP\n"

    await update.message.reply_text(text)

# ─────────────────────────
# RADAR
# ─────────────────────────

async def radar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):

    city = update.message.text.replace("📡 Radar", "").strip()

    if not city:
        await update.message.reply_text("Example: Radar Atlanta")
        return

    if not OPENAI_KEY:
        await update.message.reply_text(
            f"📡 Radar for {city}\n\nStudios\nPromoters\nRadio\nVenues"
        )
        return

    try:
        import openai
        openai.api_key = OPENAI_KEY

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"user","content":f"Top music contacts in {city}"}
            ]
        )

        await update.message.reply_text(response.choices[0].message.content)

    except:
        await update.message.reply_text("Radar temporarily unavailable.")

# ─────────────────────────
# PARISH 14 STORE
# ─────────────────────────

async def store(update: Update, ctx: ContextTypes.DEFAULT_TYPE):

    text = """
🛍 PARISH 14

Royal Crown Hoodie
Black Cathedral Tee
Gold Emblem Cap

Official merchandise coming soon.
"""

    await update.message.reply_text(text)

# ─────────────────────────
# DONATIONS
# ─────────────────────────

async def support(update: Update, ctx: ContextTypes.DEFAULT_TYPE):

    text = """
👑 Support BAZRAGOD

Suggested support:

$5
$10
$25
Custom amount

Your support helps build the kingdom.
"""

    await update.message.reply_text(text)

# ─────────────────────────
# STOIC WISDOM
# ─────────────────────────

STOIC_QUOTES = [
    "Waste no more time arguing what a good man should be. Be one. — Marcus Aurelius",
    "He who conquers himself is the mightiest warrior. — Confucius",
    "Fortune favors the bold.",
]

async def wisdom(update: Update, ctx: ContextTypes.DEFAULT_TYPE):

    quote = random.choice(STOIC_QUOTES)

    await update.message.reply_text(f"🧠 Royal Wisdom\n\n{quote}")

# ─────────────────────────
# BROADCAST (OWNER)
# ─────────────────────────

async def broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    msg = " ".join(ctx.args)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT telegram_id FROM fans")
    fans = cur.fetchall()

    cur.close()
    conn.close()

    for f in fans:
        try:
            await ctx.bot.send_message(chat_id=f[0], text=msg)
        except:
            pass

    await update.message.reply_text("Broadcast sent.")

# ─────────────────────────
# MESSAGE ROUTER
# ─────────────────────────

async def router(update: Update, ctx: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if "🎵 Music" in text:
        await music(update, ctx)

    elif "🏆 Fans" in text:
        await fans(update, ctx)

    elif "📡 Radar" in text:
        await radar(update, ctx)

    elif "🛍 PARISH 14" in text:
        await store(update, ctx)

    elif "💰 Support" in text:
        await support(update, ctx)

    else:
        await update.message.reply_text("👑 Command not recognized.")

# ─────────────────────────
# MAIN
# ─────────────────────────

def main():

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wisdom", wisdom))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

    print("👑 MiserBot v600 running.")
    app.run_polling()

if __name__ == "__main__":
    main()
