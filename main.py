"""
╔══════════════════════════════════════════════════════════════╗
║        I.A.A.I.M.O — MISERBOT v10.2 CORE SYSTEM             ║
║        Independent Artists Artificial Intelligence          ║
║        Music Operations Platform                            ║
║        Owner: BAZRAGOD                                      ║
║        Nation: Parish 14                                    ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import random
import asyncio
import threading
from datetime import datetime, timedelta, date
from io import BytesIO

import psycopg2
from psycopg2.pool import SimpleConnectionPool

from flask import Flask, request

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from openai import OpenAI

# ╔══════════════════════════════════════════════════════════════╗
# CONFIG
# ╚══════════════════════════════════════════════════════════════╝

BOT_TOKEN      = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL   = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OWNER_ID       = int(os.environ.get("OWNER_ID", "8741545426"))

BOT_USERNAME   = "miserbot"

WEBHOOK_PATH   = "/webhook"

CASHAPP = "https://cash.app/$BAZRAGOD"
PAYPAL  = "https://paypal.me/bazragod1"

SUPPORT_TIER_PRICE = 19.99
CHARITY_THRESHOLD  = 500

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = Flask(__name__)

# ╔══════════════════════════════════════════════════════════════╗
# DATABASE POOL
# ╚══════════════════════════════════════════════════════════════╝

db_pool = None

def init_pool():
    global db_pool
    db_pool = SimpleConnectionPool(1, 10, dsn=DATABASE_URL)

def get_db():
    return db_pool.getconn()

def release_db(conn):
    db_pool.putconn(conn)

# ╔══════════════════════════════════════════════════════════════╗
# DATABASE INIT
# ╚══════════════════════════════════════════════════════════════╝

def init_db():

    conn = get_db()
    cur  = conn.cursor()

    try:

        cur.execute("""
        CREATE TABLE IF NOT EXISTS fans(
            telegram_id BIGINT PRIMARY KEY,
            username TEXT,
            points INT DEFAULT 0,
            invites INT DEFAULT 0,
            tier TEXT DEFAULT 'Fan',
            joined_at TIMESTAMP DEFAULT NOW()
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS songs(
            id SERIAL PRIMARY KEY,
            title TEXT,
            file_id TEXT,
            plays INT DEFAULT 30000,
            likes INT DEFAULT 0,
            donations INT DEFAULT 0
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS beats(
            id SERIAL PRIMARY KEY,
            title TEXT,
            file_id TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS drops(
            id SERIAL PRIMARY KEY,
            title TEXT,
            file_id TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS announcements(
            id SERIAL PRIMARY KEY,
            title TEXT,
            file_id TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS promos(
            id SERIAL PRIMARY KEY,
            title TEXT,
            file_id TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS dj_drops(
            id SERIAL PRIMARY KEY,
            dj TEXT,
            title TEXT,
            file_id TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS radio_sessions(
            telegram_id BIGINT,
            last_ping TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS fan_locations(
            telegram_id BIGINT PRIMARY KEY,
            city TEXT,
            country TEXT,
            latitude FLOAT,
            longitude FLOAT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS voice_wall(
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT,
            file_id TEXT,
            approved BOOLEAN DEFAULT FALSE
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases(
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT,
            item TEXT,
            price FLOAT,
            status TEXT DEFAULT 'pending'
        )
        """)

        conn.commit()

    finally:
        release_db(conn)

# ╔══════════════════════════════════════════════════════════════╗
# POINT SYSTEM
# ╚══════════════════════════════════════════════════════════════╝

POINTS = {
    "start":5,
    "play_song":8,
    "radio":10,
    "invite":20,
    "mission":100,
    "like":3
}

RANKS = [
    (0,"Fan"),
    (100,"Supporter"),
    (500,"Recruiter"),
    (1000,"Commander"),
    (2500,"General"),
    (5000,"Parish Elite")
]

def get_rank(points):

    rank = "Fan"

    for threshold, label in RANKS:
        if points >= threshold:
            rank = label

    return rank

def award_points(uid, action, username=None):

    pts = POINTS.get(action,1)

    conn = get_db()
    cur  = conn.cursor()

    try:

        cur.execute("""
        INSERT INTO fans (telegram_id, username, points)
        VALUES (%s,%s,%s)
        ON CONFLICT (telegram_id)
        DO UPDATE SET points = fans.points + %s
        """,(uid,username,pts,pts))

        cur.execute("SELECT points FROM fans WHERE telegram_id=%s",(uid,))
        points = cur.fetchone()[0]

        cur.execute("UPDATE fans SET tier=%s WHERE telegram_id=%s",
        (get_rank(points),uid))

        conn.commit()

    finally:
        release_db(conn)

    return pts

# ╔══════════════════════════════════════════════════════════════╗
# MAIN MENU
# ╚══════════════════════════════════════════════════════════════╝

main_menu = ReplyKeyboardMarkup(

[
["🎧 BAZRAGOD MUSIC","📻 BazraGod Radio"],
["🥁 Beats","🎤 Drops"],
["📊 Top Charts","🏆 Leaderboard"],
["⭐ My Points","👤 My Profile"],
["💰 Support Artist","🛒 Music Store"],
["👕 Parish 14 Merch","🌐 Social"],
["📍 Share Location","👥 Refer"],
["🤖 MAXIMUS AI"]
],

resize_keyboard=True

)

# ╔══════════════════════════════════════════════════════════════╗
# TELEGRAM APP
# ╚══════════════════════════════════════════════════════════════╝

telegram_app = Application.builder().token(BOT_TOKEN).build()
# ╔══════════════════════════════════════════════════════════════╗
# MUSIC ENGINE
# ╚══════════════════════════════════════════════════════════════╝

async def music_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur  = conn.cursor()

    try:
        cur.execute("SELECT id,title,plays,likes FROM songs ORDER BY id")
        songs = cur.fetchall()
    finally:
        release_db(conn)

    if not songs:
        await update.message.reply_text("Catalog loading...")
        return

    keyboard = []

    for s in songs:

        heat = "🔥" * min(5, int(s[3] / 10 + 1))

        label = f"{s[1]}  ({s[2]} plays) {heat}"

        keyboard.append([
            InlineKeyboardButton(label, callback_data=f"song:{s[0]}")
        ])

    await update.message.reply_text(
        "🎧 BAZRAGOD MUSIC CATALOG",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ╔══════════════════════════════════════════════════════════════╗
# PLAY SONG
# ╚══════════════════════════════════════════════════════════════╝

async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    song_id = int(query.data.split(":")[1])

    conn = get_db()
    cur  = conn.cursor()

    try:

        cur.execute(
        "SELECT title,file_id,plays,likes FROM songs WHERE id=%s",
        (song_id,)
        )

        song = cur.fetchone()

        cur.execute(
        "UPDATE songs SET plays = plays + 1 WHERE id=%s",
        (song_id,)
        )

        conn.commit()

    finally:
        release_db(conn)

    if not song:
        return

    title = song[0]
    file  = song[1]
    plays = song[2] + 1
    likes = song[3]

    heat = "🔥" * min(5, int(likes / 10 + 1))

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton("❤️ Like", callback_data=f"like:{song_id}"),
            InlineKeyboardButton("💰 Donate", callback_data=f"donate:{song_id}")
        ]

    ])

    await query.message.reply_audio(
        file,
        caption=f"🎵 {title}\n\n🔥 {heat}\n\n{plays} plays",
        reply_markup=keyboard
    )


# ╔══════════════════════════════════════════════════════════════╗
# LIKE SONG
# ╚══════════════════════════════════════════════════════════════╝

async def like_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    song_id = int(query.data.split(":")[1])

    conn = get_db()
    cur  = conn.cursor()

    try:

        cur.execute(
        "UPDATE songs SET likes = likes + 1 WHERE id=%s",
        (song_id,)
        )

        conn.commit()

    finally:
        release_db(conn)

    await query.message.reply_text("🔥 Like registered")


# ╔══════════════════════════════════════════════════════════════╗
# DONATION BUTTON
# ╚══════════════════════════════════════════════════════════════╗

async def donate_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    song_id = int(query.data.split(":")[1])

    keyboard = InlineKeyboardMarkup([

        [InlineKeyboardButton("💵 CashApp", url=CASHAPP)],
        [InlineKeyboardButton("💳 PayPal", url=PAYPAL)]

    ])

    await query.message.reply_text(

        "💰 SUPPORT THE ARTIST\n\n"
        "Every donation powers independent music.\n"
        "Parish 14 Nation.\n",

        reply_markup=keyboard
    )


# ╔══════════════════════════════════════════════════════════════╗
# TOP CHARTS
# ╚══════════════════════════════════════════════════════════════╗

async def top_charts(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur  = conn.cursor()

    try:

        cur.execute(
        "SELECT title,plays,likes FROM songs ORDER BY likes DESC LIMIT 10"
        )

        rows = cur.fetchall()

    finally:
        release_db(conn)

    text = "📊 PARISH 14 TOP CHARTS\n\n"

    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

    for i,r in enumerate(rows):

        heat = "🔥" * min(5, int(r[2] / 10 + 1))

        text += f"{medals[i]} {r[0]}\n{r[1]} plays {heat}\n\n"

    await update.message.reply_text(text)


# ╔══════════════════════════════════════════════════════════════╗
# UPLOAD CLASSIFIER
# ╚══════════════════════════════════════════════════════════════╗

async def upload_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    if uid != OWNER_ID:
        return

    audio = update.message.audio

    if not audio:
        return

    context.user_data["pending_upload"] = audio

    keyboard = InlineKeyboardMarkup([

        [InlineKeyboardButton("🎵 Song",callback_data="upload:song")],
        [InlineKeyboardButton("🥁 Beat",callback_data="upload:beat")],
        [InlineKeyboardButton("🎤 Drop",callback_data="upload:drop")],
        [InlineKeyboardButton("📣 Announcement",callback_data="upload:announcement")],
        [InlineKeyboardButton("📻 Radio Promo",callback_data="upload:promo")],
        [InlineKeyboardButton("🎙 DJ Maximus",callback_data="upload:maximus")],
        [InlineKeyboardButton("☀️ DJ Aurora",callback_data="upload:aurora")],
        [InlineKeyboardButton("🔴 DJ ColorRed",callback_data="upload:red")],
        [InlineKeyboardButton("🌑 DJ Eclipse",callback_data="upload:eclipse")]

    ])

    await update.message.reply_text(
        "Select category for upload:",
        reply_markup=keyboard
    )


async def upload_select(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    category = query.data.split(":")[1]

    audio = context.user_data.get("pending_upload")

    if not audio:
        return

    title   = audio.title or "Untitled"
    file_id = audio.file_id

    conn = get_db()
    cur  = conn.cursor()

    try:

        if category == "song":

            cur.execute(
            "INSERT INTO songs(title,file_id) VALUES(%s,%s)",
            (title,file_id)
            )

        elif category == "beat":

            cur.execute(
            "INSERT INTO beats(title,file_id) VALUES(%s,%s)",
            (title,file_id)
            )

        elif category == "drop":

            cur.execute(
            "INSERT INTO drops(title,file_id) VALUES(%s,%s)",
            (title,file_id)
            )

        elif category == "announcement":

            cur.execute(
            "INSERT INTO announcements(title,file_id) VALUES(%s,%s)",
            (title,file_id)
            )

        elif category == "promo":

            cur.execute(
            "INSERT INTO promos(title,file_id) VALUES(%s,%s)",
            (title,file_id)
            )

        else:

            cur.execute(
            "INSERT INTO dj_drops(dj,title,file_id) VALUES(%s,%s,%s)",
            (category,title,file_id)
            )

        conn.commit()

    finally:
        release_db(conn)

    await query.message.reply_text("✅ Upload stored in library")
# ╔══════════════════════════════════════════════════════════════╗
# RADIO ENGINE
# ╚══════════════════════════════════════════════════════════════╝

RADIO_MEMORY = {}
RADIO_LAST_ANNOUNCE = {}

DJ_ROTATION = [
    "MAXIMUS",
    "AURORA",
    "COLORRED",
    "ECLIPSE"
]

DJ_LINES = {

"MAXIMUS":[
"Welcome to BazraGod Radio. The sovereign frequency of Parish 14.",
"This is MAXIMUS at the command deck. Independent music lives here.",
"You are locked into I.A.A.I.M.O radio. No label. No middleman.",
],

"AURORA":[
"Good morning universe. DJ Aurora lighting up the frequency.",
"Sunrise energy across the Parish 14 network.",
"Positive vibrations only. Let the music guide the day."
],

"COLORRED":[
"DJ ColorRed live from the cosmic booth.",
"Turn the speakers up. We bringing the heat.",
"This is the rhythm of the streets and the stars."
],

"ECLIPSE":[
"Nightfall transmissions beginning.",
"DJ Eclipse controlling the shadows.",
"After dark energy on BazraGod Radio."
]

}


def select_dj():

    hour = datetime.utcnow().hour

    if 6 <= hour < 12:
        return "AURORA"

    if 12 <= hour < 18:
        return "COLORRED"

    if 18 <= hour < 24:
        return "MAXIMUS"

    return "ECLIPSE"


def get_random_song(conn, user_id):

    cur = conn.cursor()

    cur.execute("SELECT id,title,file_id FROM songs")
    songs = cur.fetchall()

    if not songs:
        return None

    memory = RADIO_MEMORY.get(user_id, [])

    available = [s for s in songs if s[0] not in memory]

    if not available:
        RADIO_MEMORY[user_id] = []
        available = songs

    song = random.choice(available)

    memory.append(song[0])

    RADIO_MEMORY[user_id] = memory

    return song


async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    conn = get_db()

    try:

        song = get_random_song(conn, user_id)

        if not song:
            await update.message.reply_text("Radio library empty.")
            return

        dj = select_dj()

        now = datetime.utcnow()

        last = RADIO_LAST_ANNOUNCE.get(user_id)

        announce = False

        if not last:
            announce = True

        else:
            if now - last > timedelta(minutes=15):
                announce = True

        if announce:

            RADIO_LAST_ANNOUNCE[user_id] = now

            line = random.choice(DJ_LINES[dj])

            await update.message.reply_text(
                f"📻 {dj} ON AIR\n\n{line}"
            )

        cur = conn.cursor()

        cur.execute(
        "UPDATE songs SET plays = plays + 1 WHERE id=%s",
        (song[0],)
        )

        conn.commit()

    finally:
        release_db(conn)

    await update.message.reply_audio(
        song[2],
        caption=f"📻 BazraGod Radio\n\n🎵 {song[1]}"
    )


# ╔══════════════════════════════════════════════════════════════╗
# RADIO ANNOUNCEMENTS
# ╚══════════════════════════════════════════════════════════════╝

async def radio_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()

    try:

        cur = conn.cursor()

        cur.execute(
        "SELECT file_id,title FROM promos ORDER BY RANDOM() LIMIT 1"
        )

        promo = cur.fetchone()

    finally:
        release_db(conn)

    if not promo:
        return

    await update.message.reply_audio(
        promo[0],
        caption=f"📣 {promo[1]}"
    )


async def radio_announcement(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()

    try:

        cur = conn.cursor()

        cur.execute(
        "SELECT file_id,title FROM announcements ORDER BY RANDOM() LIMIT 1"
        )

        item = cur.fetchone()

    finally:
        release_db(conn)

    if not item:
        return

    await update.message.reply_audio(
        item[0],
        caption=f"📣 Station Message"
    )


# ╔══════════════════════════════════════════════════════════════╗
# RADIO DJ DROPS
# ╚══════════════════════════════════════════════════════════════╝

async def radio_dj_drop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    dj = select_dj()

    conn = get_db()

    try:

        cur = conn.cursor()

        cur.execute(
        "SELECT file_id,title FROM dj_drops WHERE dj=%s ORDER BY RANDOM() LIMIT 1",
        (dj.lower(),)
        )

        drop = cur.fetchone()

    finally:
        release_db(conn)

    if not drop:
        return

    await update.message.reply_audio(
        drop[0],
        caption=f"🎙 {dj}"
    )
# ╔══════════════════════════════════════════════════════════════╗
# VIRAL HEAT ENGINE
# ╚══════════════════════════════════════════════════════════════╝

def calculate_heat(likes, donations, plays):

    score = (likes * 5) + (donations * 10) + (plays / 1000)

    if score < 10:
        return "🔥"

    if score < 50:
        return "🔥🔥"

    if score < 100:
        return "🔥🔥🔥"

    if score < 250:
        return "🔥🔥🔥🔥"

    return "🔥🔥🔥🔥🔥"


# ╔══════════════════════════════════════════════════════════════╗
# LIKE BUTTON
# ╚══════════════════════════════════════════════════════════════╝

async def like_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    song_id = int(query.data.split(":")[1])
    user_id = query.from_user.id

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
        "UPDATE songs SET likes = likes + 1 WHERE id=%s",
        (song_id,)
        )

        conn.commit()

    finally:
        release_db(conn)

    award_points(user_id, "like")

    await query.message.reply_text("❤️ Like registered")


# ╔══════════════════════════════════════════════════════════════╗
# DONATION BUTTON
# ╚══════════════════════════════════════════════════════════════╝

async def donate_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboardMarkup([

        [InlineKeyboardButton("💵 CashApp", url=CASHAPP)],
        [InlineKeyboardButton("💳 PayPal", url=PAYPAL)]

    ])

    await query.message.reply_text(

        "💰 SUPPORT THE ARTIST\n\n"
        "Independent music survives through the fans.\n"
        "Every donation powers Parish 14.\n",

        reply_markup=keyboard
    )


# ╔══════════════════════════════════════════════════════════════╗
# TRENDING BOARD
# ╚══════════════════════════════════════════════════════════════╝

async def trending(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
        "SELECT title,plays,likes,donations FROM songs"
        )

        songs = cur.fetchall()

    finally:
        release_db(conn)

    ranking = []

    for s in songs:

        heat = (s[1] / 1000) + (s[2] * 5) + (s[3] * 10)

        ranking.append((s[0],s[1],s[2],heat))

    ranking.sort(key=lambda x: x[3], reverse=True)

    text = "🔥 TRENDING ON PARISH 14\n\n"

    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

    for i,r in enumerate(ranking[:10]):

        heat_icon = calculate_heat(r[2],0,r[1])

        text += f"{medals[i]} {r[0]}\n{r[1]} plays {heat_icon}\n\n"

    await update.message.reply_text(text)


# ╔══════════════════════════════════════════════════════════════╗
# SONG STATS PANEL
# ╚══════════════════════════════════════════════════════════════╝

async def song_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
        "SELECT title,plays,likes,donations FROM songs ORDER BY plays DESC LIMIT 10"
        )

        songs = cur.fetchall()

    finally:
        release_db(conn)

    text = "📊 SONG STATISTICS\n\n"

    for s in songs:

        heat = calculate_heat(s[2],s[3],s[1])

        text += (
        f"🎵 {s[0]}\n"
        f"Plays: {s[1]}\n"
        f"Likes: {s[2]}\n"
        f"Donations: {s[3]}\n"
        f"Heat: {heat}\n\n"
        )

    await update.message.reply_text(text)


# ╔══════════════════════════════════════════════════════════════╗
# CHARITY TRIGGER
# ╚══════════════════════════════════════════════════════════════╝

async def charity_tracker(context):

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
        "SELECT SUM(donations) FROM songs"
        )

        total = cur.fetchone()[0] or 0

        if total >= CHARITY_THRESHOLD:

            await context.bot.send_message(
                OWNER_ID,
                "💝 Charity threshold reached. $500 milestone."
            )

            cur.execute(
            "UPDATE songs SET donations = 0"
            )

            conn.commit()

    finally:
        release_db(conn)
# ╔══════════════════════════════════════════════════════════════╗
# FAN PROFILE
# ╚══════════════════════════════════════════════════════════════╝

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
        "SELECT username,points,invites,tier,joined_at FROM fans WHERE telegram_id=%s",
        (uid,)
        )

        fan = cur.fetchone()

    finally:
        release_db(conn)

    if not fan:

        await update.message.reply_text("Use /start first.")
        return

    name = fan[0] or "Anonymous"
    pts = fan[1]
    invites = fan[2]
    tier = fan[3]
    joined = fan[4].strftime("%B %Y")

    await update.message.reply_text(

        f"👤 FAN PROFILE\n\n"
        f"Name: {name}\n"
        f"Tier: {tier}\n"
        f"Points: {pts}\n"
        f"Invites: {invites}\n"
        f"Joined: {joined}"

    )


# ╔══════════════════════════════════════════════════════════════╗
# LEADERBOARD
# ╚══════════════════════════════════════════════════════════════╝

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
        "SELECT username,points,tier FROM fans ORDER BY points DESC LIMIT 10"
        )

        fans = cur.fetchall()

    finally:
        release_db(conn)

    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

    text = "🏆 PARISH 14 LEADERBOARD\n\n"

    for i,f in enumerate(fans):

        name = f"@{f[0]}" if f[0] else "Anonymous"

        text += f"{medals[i]} {name}\n{f[1]} pts • {f[2]}\n\n"

    await update.message.reply_text(text)


# ╔══════════════════════════════════════════════════════════════╗
# MY POINTS
# ╚══════════════════════════════════════════════════════════════╝

async def my_points(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
        "SELECT points,tier FROM fans WHERE telegram_id=%s",
        (uid,)
        )

        fan = cur.fetchone()

    finally:
        release_db(conn)

    if not fan:

        await update.message.reply_text("Send /start first.")
        return

    await update.message.reply_text(

        f"⭐ YOUR STATS\n\n"
        f"Points: {fan[0]}\n"
        f"Tier: {fan[1]}\n"

    )


# ╔══════════════════════════════════════════════════════════════╗
# REFERRAL SYSTEM
# ╚══════════════════════════════════════════════════════════════╝

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    link = f"https://t.me/{BOT_USERNAME}?start={uid}"

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
        "SELECT invites,tier FROM fans WHERE telegram_id=%s",
        (uid,)
        )

        fan = cur.fetchone()

    finally:
        release_db(conn)

    invites = fan[0] if fan else 0
    tier = fan[1] if fan else "Fan"

    await update.message.reply_text(

        f"👥 REFERRAL SYSTEM\n\n"
        f"Your invite link:\n{link}\n\n"
        f"Invites: {invites}\n"
        f"Tier: {tier}\n\n"
        f"Each invite earns +{POINTS['invite']} points."

    )


# ╔══════════════════════════════════════════════════════════════╗
# DAILY MISSIONS
# ╚══════════════════════════════════════════════════════════════╝

MISSIONS = [

"Listen to a song",
"Open the radio",
"Invite one friend",
"Like a song",
"Share your location"

]


async def daily_mission(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    mission = random.choice(MISSIONS)

    keyboard = InlineKeyboardMarkup([

        [InlineKeyboardButton(
        "✅ Complete Mission",
        callback_data=f"mission:{uid}"
        )]

    ])

    await update.message.reply_text(

        f"🎯 DAILY MISSION\n\n"
        f"{mission}\n\n"
        f"Reward: +{POINTS['mission']} points",

        reply_markup=keyboard

    )


async def mission_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = int(query.data.split(":")[1])

    award_points(uid,"mission")

    await query.message.reply_text(

        f"🎯 Mission Complete\n\n"
        f"+{POINTS['mission']} points added."

    )


# ╔══════════════════════════════════════════════════════════════╗
# FAN RADAR
# ╚══════════════════════════════════════════════════════════════╝

async def fan_radar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(

        "SELECT country,COUNT(*) FROM fan_locations "
        "GROUP BY country ORDER BY COUNT(*) DESC LIMIT 10"

        )

        rows = cur.fetchall()

    finally:
        release_db(conn)

    if not rows:

        await update.message.reply_text("No fan locations yet.")
        return

    text = "🌍 FAN RADAR\n\n"

    for r in rows:

        text += f"{r[0]} — {r[1]} fans\n"

    await update.message.reply_text(text)
# ╔══════════════════════════════════════════════════════════════╗
# MAXIMUS AI SYSTEM
# ╚══════════════════════════════════════════════════════════════╝

AI_SYSTEM_PROMPT = """
You are MAXIMUS — the sovereign AI of BAZRAGOD.

You serve the Parish 14 Nation.

Roles:
• Music manager
• Radio DJ
• Fan commander
• Cultural strategist

Tone:
Confident
Calm
Powerful
Inspirational

You protect the brand and uplift the fans.

Always speak like a leader addressing a nation.
Keep responses short and impactful.
"""


# ╔══════════════════════════════════════════════════════════════╗
# ACTIVATE MAXIMUS
# ╚══════════════════════════════════════════════════════════════╝

async def maximus_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not openai_client:

        await update.message.reply_text(
        "MAXIMUS AI is offline."
        )
        return

    context.user_data["ai_active"] = True

    await update.message.reply_text(

        "🤖 MAXIMUS ONLINE\n\n"
        "Ask me anything about music, strategy, or the nation."

    )


# ╔══════════════════════════════════════════════════════════════╗
# AI CHAT HANDLER
# ╚══════════════════════════════════════════════════════════════╝

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("ai_active"):
        return False

    if not openai_client:
        return False

    user_msg = update.message.text

    try:

        response = openai_client.chat.completions.create(

            model="gpt-4o-mini",

            messages=[

                {"role":"system","content":AI_SYSTEM_PROMPT},
                {"role":"user","content":user_msg}

            ],

            max_tokens=200

        )

        reply = response.choices[0].message.content

        await update.message.reply_text(

            f"🤖 MAXIMUS\n\n{reply}"

        )

    except Exception as e:

        await update.message.reply_text(
        f"AI error: {str(e)}"
        )

    return True


# ╔══════════════════════════════════════════════════════════════╗
# MOOD RADIO
# ╚══════════════════════════════════════════════════════════════╗

async def mood_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "🎧 MOOD RADIO\n\n"
        "Tell me your mood.\n"
        "Example:\n"
        "happy\n"
        "focused\n"
        "aggressive\n"
        "late night"

    )

    context.user_data["mood_mode"] = True


async def mood_select(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("mood_mode"):
        return False

    mood = update.message.text.lower()

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
        "SELECT id,title,file_id FROM songs ORDER BY RANDOM() LIMIT 1"
        )

        song = cur.fetchone()

    finally:
        release_db(conn)

    context.user_data["mood_mode"] = False

    if not song:
        return True

    await update.message.reply_text(

        f"🎧 Mood detected: {mood}\n"
        f"MAXIMUS selecting a track..."

    )

    await update.message.reply_audio(

        song[2],
        caption=f"🎵 {song[1]}"

    )

    return True


# ╔══════════════════════════════════════════════════════════════╗
# LYRIC CIPHER
# ╚══════════════════════════════════════════════════════════════╗

async def lyric_cipher(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "⚔️ LYRIC CIPHER\n\n"
        "Drop your verse.\n"
        "MAXIMUS will respond with bars."

    )

    context.user_data["cipher_mode"] = True


async def cipher_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("cipher_mode"):
        return False

    if not openai_client:
        return False

    verse = update.message.text

    try:

        response = openai_client.chat.completions.create(

            model="gpt-4o-mini",

            messages=[

                {
                "role":"system",
                "content":
                "You are a lyrical AI responding in the style of BAZRAGOD with powerful confident bars."
                },

                {"role":"user","content":verse}

            ],

            max_tokens=150

        )

        bars = response.choices[0].message.content

        await update.message.reply_text(

            f"⚔️ MAXIMUS BARS\n\n{bars}"

        )

    except Exception as e:

        await update.message.reply_text(
        f"Cipher error: {str(e)}"
        )

    context.user_data["cipher_mode"] = False

    return True
# ╔══════════════════════════════════════════════════════════════╗
# VOICE WALL SYSTEM
# ╚══════════════════════════════════════════════════════════════╝

async def voice_wall(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "🎙 VOICE WALL\n\n"
        "Send a voice message shoutout.\n"
        "If approved it will play on BazraGod Radio."

    )

    context.user_data["voice_mode"] = True


async def capture_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("voice_mode"):
        return False

    voice = update.message.voice

    if not voice:
        return False

    uid = update.effective_user.id

    file_id = voice.file_id

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(

        "INSERT INTO voice_wall(telegram_id,file_id) VALUES(%s,%s) RETURNING id",

        (uid,file_id)

        )

        voice_id = cur.fetchone()[0]

        conn.commit()

    finally:
        release_db(conn)

    context.user_data["voice_mode"] = False

    await update.message.reply_text(

        "🎧 Voice received.\n"
        "Pending approval."

    )

    try:

        await context.bot.send_message(

            OWNER_ID,

            f"New voice shoutout waiting approval.\n\n/approve_voice {voice_id}"

        )

    except:
        pass

    return True


# ╔══════════════════════════════════════════════════════════════╗
# APPROVE VOICE
# ╚══════════════════════════════════════════════════════════════╝

async def approve_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    args = context.args

    if not args:
        await update.message.reply_text("Usage: /approve_voice ID")
        return

    voice_id = int(args[0])

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(

        "UPDATE voice_wall SET approved=TRUE WHERE id=%s RETURNING file_id",

        (voice_id,)

        )

        voice = cur.fetchone()

        conn.commit()

    finally:
        release_db(conn)

    if not voice:

        await update.message.reply_text("Voice not found.")
        return

    await update.message.reply_text(

        "✅ Voice approved and added to radio."

    )


# ╔══════════════════════════════════════════════════════════════╗
# RADIO FAN VOICES
# ╚══════════════════════════════════════════════════════════════╝

async def radio_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(

        "SELECT file_id FROM voice_wall "
        "WHERE approved=TRUE ORDER BY RANDOM() LIMIT 1"

        )

        voice = cur.fetchone()

    finally:
        release_db(conn)

    if not voice:
        return

    await update.message.reply_voice(

        voice[0],

        caption="🎙 Parish 14 Fan Shoutout"

    )
# ╔══════════════════════════════════════════════════════════════╗
# ADMIN PANEL
# ╚══════════════════════════════════════════════════════════════╝

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    await update.message.reply_text(

        "👑 MISERBOT ADMIN PANEL\n\n"
        "/stats — platform analytics\n"
        "/radar — fan location intelligence\n"
        "/orders — pending purchases\n"
        "/weekly — weekly intelligence report\n"
        "/broadcast — send message to all fans\n"
        "/approve_voice ID — approve voice shoutout\n"

    )


# ╔══════════════════════════════════════════════════════════════╗
# PLATFORM STATS
# ╚══════════════════════════════════════════════════════════════╝

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute("SELECT COUNT(*) FROM fans")
        fans = cur.fetchone()[0]

        cur.execute("SELECT SUM(points) FROM fans")
        points = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM songs")
        songs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM beats")
        beats = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM drops")
        drops = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM voice_wall WHERE approved=TRUE")
        voices = cur.fetchone()[0]

    finally:
        release_db(conn)

    await update.message.reply_text(

        f"📊 PLATFORM STATS\n\n"
        f"Fans: {fans}\n"
        f"Points issued: {points}\n"
        f"Songs: {songs}\n"
        f"Beats: {beats}\n"
        f"Drops: {drops}\n"
        f"Voice shoutouts: {voices}"

    )


# ╔══════════════════════════════════════════════════════════════╗
# TOUR RADAR
# ╚══════════════════════════════════════════════════════════════╝

async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(

        "SELECT country,COUNT(*) FROM fan_locations "
        "GROUP BY country ORDER BY COUNT(*) DESC LIMIT 10"

        )

        rows = cur.fetchall()

    finally:
        release_db(conn)

    if not rows:

        await update.message.reply_text("No fan locations yet.")
        return

    text = "🌍 TOUR INTELLIGENCE\n\n"

    for r in rows:

        text += f"{r[0]} — {r[1]} fans\n"

    await update.message.reply_text(text)


# ╔══════════════════════════════════════════════════════════════╗
# ORDERS DASHBOARD
# ╚══════════════════════════════════════════════════════════════╝

async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(

        "SELECT id,telegram_id,item,price FROM purchases "
        "WHERE status='pending'"

        )

        rows = cur.fetchall()

    finally:
        release_db(conn)

    if not rows:

        await update.message.reply_text("No pending orders.")
        return

    text = "🛒 PENDING ORDERS\n\n"

    for r in rows:

        text += f"Order {r[0]} — {r[2]} (${r[3]})\nUser {r[1]}\n\n"

    await update.message.reply_text(text)


# ╔══════════════════════════════════════════════════════════════╗
# WEEKLY INTELLIGENCE REPORT
# ╚══════════════════════════════════════════════════════════════╝

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute("SELECT COUNT(*) FROM fans")
        fans = cur.fetchone()[0]

        cur.execute(
        "SELECT username,points FROM fans ORDER BY points DESC LIMIT 1"
        )

        top = cur.fetchone()

        cur.execute(
        "SELECT title,plays FROM songs ORDER BY plays DESC LIMIT 1"
        )

        song = cur.fetchone()

    finally:
        release_db(conn)

    top_fan = f"@{top[0]} ({top[1]} pts)" if top else "None"
    top_song = f"{song[0]} ({song[1]} plays)" if song else "None"

    await update.message.reply_text(

        "📡 WEEKLY INTEL REPORT\n\n"
        f"Total fans: {fans}\n"
        f"Top fan: {top_fan}\n"
        f"Top song: {top_song}"

    )


# ╔══════════════════════════════════════════════════════════════╗
# BROADCAST SYSTEM
# ╚══════════════════════════════════════════════════════════════╝

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    context.user_data["broadcast_mode"] = True

    await update.message.reply_text(

        "📢 Broadcast mode enabled.\n\n"
        "Send the message to broadcast."

    )


async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("broadcast_mode"):
        return False

    message = update.message.text

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute("SELECT telegram_id FROM fans")
        fans = cur.fetchall()

    finally:
        release_db(conn)

    sent = 0

    for f in fans:

        try:

            await context.bot.send_message(f[0], message)

            sent += 1

        except:
            pass

    context.user_data["broadcast_mode"] = False

    await update.message.reply_text(

        f"Broadcast sent to {sent} fans."

    )

    return True
# ╔══════════════════════════════════════════════════════════════╗
# TEXT ROUTER
# ╚══════════════════════════════════════════════════════════════╝

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    # AI CHAT
    if await ai_chat(update, context):
        return

    # MOOD RADIO
    if await mood_select(update, context):
        return

    # LYRIC CIPHER
    if await cipher_reply(update, context):
        return

    # BROADCAST MODE
    if await broadcast_send(update, context):
        return

    routes = {

        "🎧 BAZRAGOD MUSIC": music_menu,

        "📻 BazraGod Radio": radio,

        "📊 Top Charts": trending,

        "🏆 Leaderboard": leaderboard,

        "⭐ My Points": my_points,

        "👤 My Profile": my_profile,

        "👥 Refer": refer,

        "🎯 Daily Mission": daily_mission,

        "🌍 Fan Radar": fan_radar,

        "🎙 Voice Wall": voice_wall,

        "🤖 MAXIMUS AI": maximus_ai,

        "🎧 Mood Radio": mood_radio,

        "⚔️ Lyric Cipher": lyric_cipher,

    }

    handler = routes.get(text)

    if handler:

        await handler(update, context)



# ╔══════════════════════════════════════════════════════════════╗
# COMMAND HANDLERS
# ╚══════════════════════════════════════════════════════════════╝

telegram_app.add_handler(CommandHandler("admin", admin_panel))
telegram_app.add_handler(CommandHandler("stats", stats))
telegram_app.add_handler(CommandHandler("radar", radar))
telegram_app.add_handler(CommandHandler("orders", orders))
telegram_app.add_handler(CommandHandler("weekly", weekly))
telegram_app.add_handler(CommandHandler("broadcast", broadcast))
telegram_app.add_handler(CommandHandler("approve_voice", approve_voice))


# ╔══════════════════════════════════════════════════════════════╗
# CALLBACK HANDLERS
# ╚══════════════════════════════════════════════════════════════╝

telegram_app.add_handler(CallbackQueryHandler(play_song, pattern="^song:"))
telegram_app.add_handler(CallbackQueryHandler(like_song, pattern="^like:"))
telegram_app.add_handler(CallbackQueryHandler(donate_song, pattern="^donate:"))
telegram_app.add_handler(CallbackQueryHandler(mission_complete, pattern="^mission:"))
telegram_app.add_handler(CallbackQueryHandler(upload_select, pattern="^upload:"))


# ╔══════════════════════════════════════════════════════════════╗
# MESSAGE HANDLERS
# ╚══════════════════════════════════════════════════════════════╝

telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, router)
)

telegram_app.add_handler(
    MessageHandler(filters.AUDIO, upload_audio)
)

telegram_app.add_handler(
    MessageHandler(filters.VOICE, capture_voice)
)
# ╔══════════════════════════════════════════════════════════════╗
# ASYNC BOT ENGINE
# ╚══════════════════════════════════════════════════════════════╗

loop = asyncio.new_event_loop()

def start_bot():

    asyncio.set_event_loop(loop)

    loop.run_until_complete(
        telegram_app.initialize()
    )

    loop.run_until_complete(
        telegram_app.start()
    )

    loop.run_forever()


threading.Thread(
    target=start_bot,
    daemon=True
).start()


# ╔══════════════════════════════════════════════════════════════╗
# WEBHOOK ENDPOINT
# ╚══════════════════════════════════════════════════════════════╝

@app.route(WEBHOOK_PATH, methods=["POST"])
def telegram_webhook():

    data = request.get_json(force=True)

    update = Update.de_json(
        data,
        telegram_app.bot
    )

    asyncio.run_coroutine_threadsafe(
        telegram_app.process_update(update),
        loop
    )

    return "ok"


# ╔══════════════════════════════════════════════════════════════╗
# HEALTH CHECK
# ╚══════════════════════════════════════════════════════════════╝

@app.route("/")
def health():

    return "MISERBOT ONLINE — PARISH 14 NETWORK"


# ╔══════════════════════════════════════════════════════════════╗
# MAIN STARTUP
# ╚══════════════════════════════════════════════════════════════╗

if __name__ == "__main__":

    init_pool()
    init_db()

    print("══════════════════════════════════════")
    print(" MISERBOT v10 SYSTEM BOOT")
    print(" Parish 14 Network")
    print(" Status: ONLINE")
    print("══════════════════════════════════════")

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT",8080))
    )
