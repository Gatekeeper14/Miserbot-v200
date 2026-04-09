
"""
╔══════════════════════════════════════════════════════════════╗
║               I.A.A.I.M.O — MISERBOT v12.1                   ║
║     Independent Artists Artificial Intelligence Music Ops   ║
║                                                              ║
║     Owner:  BAZRAGOD                                         ║
║     Nation: Parish 14                                        ║
║     Platform: Telegram                                       ║
║                                                              ║
║     STATUS: PRODUCTION READY                                 ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import random
import asyncio
import threading
import time
from datetime import datetime, date
from io import BytesIO

import psycopg2
from psycopg2.pool import SimpleConnectionPool

from flask import Flask, request

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from openai import OpenAI

# ============================================================
# ENVIRONMENT
# ============================================================

BOT_TOKEN = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

OWNER_ID = int(os.environ.get("OWNER_ID", "8741545426"))

BOT_USERNAME = "miserbot"

WEBHOOK_PATH = "/webhook"

INTRO_FILE_ID = os.environ.get("INTRO_FILE_ID")

CASHAPP = "https://cash.app/$BAZRAGOD"
PAYPAL = "https://paypal.me/bazragod1"

# ============================================================
# SOCIAL LINKS
# ============================================================

SOCIALS = {
    "📸 Instagram": "https://www.instagram.com/bazragod_timeless",
    "🎵 TikTok": "https://www.tiktok.com/@bazragod_official",
    "▶️ YouTube": "https://youtube.com/@bazragodmusictravelandleis8835",
    "🐦 X": "https://x.com/toligarch65693",
}

# ============================================================
# OPENAI CLIENT
# ============================================================

openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

# ============================================================
# DATABASE POOL
# ============================================================

db_pool = None


def init_pool():
    global db_pool
    db_pool = SimpleConnectionPool(
        1,
        10,
        dsn=DATABASE_URL,
    )


def get_db():
    return db_pool.getconn()


def release_db(conn):
    db_pool.putconn(conn)
# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    conn = get_db()
    cur = conn.cursor()

    try:

        # Fans table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS fans (
            telegram_id BIGINT PRIMARY KEY,
            username TEXT,
            points INT DEFAULT 0,
            invites INT DEFAULT 0,
            referrer_id BIGINT,
            tier TEXT DEFAULT '🎧 Fan',
            city TEXT,
            country TEXT,
            joined_at TIMESTAMP DEFAULT NOW()
        )
        """)

        # Songs library
        cur.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id SERIAL PRIMARY KEY,
            title TEXT,
            file_id TEXT,
            plays INT DEFAULT 300000,
            likes INT DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT NOW()
        )
        """)

        # Beats library
        cur.execute("""
        CREATE TABLE IF NOT EXISTS beats (
            id SERIAL PRIMARY KEY,
            title TEXT,
            file_id TEXT,
            plays INT DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT NOW()
        )
        """)

        # Drops
        cur.execute("""
        CREATE TABLE IF NOT EXISTS drops (
            id SERIAL PRIMARY KEY,
            title TEXT,
            file_id TEXT,
            uploaded_at TIMESTAMP DEFAULT NOW()
        )
        """)

        # Radio promos
        cur.execute("""
        CREATE TABLE IF NOT EXISTS radio_promos (
            id SERIAL PRIMARY KEY,
            text TEXT
        )
        """)

        # Fan locations
        cur.execute("""
        CREATE TABLE IF NOT EXISTS fan_locations (
            telegram_id BIGINT PRIMARY KEY,
            latitude FLOAT,
            longitude FLOAT,
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """)

        # Purchases
        cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT,
            item TEXT,
            price INT,
            status TEXT DEFAULT 'pending',
            purchased_at TIMESTAMP DEFAULT NOW()
        )
        """)

        # Missions
        cur.execute("""
        CREATE TABLE IF NOT EXISTS missions (
            telegram_id BIGINT,
            mission_date DATE,
            completed BOOLEAN DEFAULT FALSE,
            PRIMARY KEY (telegram_id, mission_date)
        )
        """)

        conn.commit()

        print("DATABASE READY")

    finally:
        release_db(conn)


# ============================================================
# POINT SYSTEM
# ============================================================

POINTS = {
    "start": 5,
    "play_song": 8,
    "play_beat": 6,
    "radio": 10,
    "share_location": 15,
    "follow_social": 3,
    "support_artist": 5,
    "invite_friend": 20,
    "wisdom": 3,
    "fitness": 3,
    "ai_chat": 2,
    "mission": 100,
}

# ============================================================
# RANKS
# ============================================================

RANKS = [
    (0, "🎧 Fan"),
    (100, "⚔️ Supporter"),
    (500, "🎖 Recruiter"),
    (1000, "🏅 Commander"),
    (2500, "👑 General"),
    (5000, "🌍 Parish 14 Elite"),
]


def get_rank(points: int) -> str:

    rank = RANKS[0][1]

    for threshold, label in RANKS:

        if points >= threshold:
            rank = label

    return rank


# ============================================================
# AWARD POINTS
# ============================================================

def award_points(telegram_id: int, action: str, username: str = None):

    pts = POINTS.get(action, 1)

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute("""
        INSERT INTO fans (telegram_id, username, points)
        VALUES (%s, %s, %s)

        ON CONFLICT (telegram_id)
        DO UPDATE SET

            points = fans.points + EXCLUDED.points,
            username = COALESCE(EXCLUDED.username, fans.username)
        """, (telegram_id, username, pts))

        cur.execute("""
        SELECT points FROM fans
        WHERE telegram_id = %s
        """, (telegram_id,))

        row = cur.fetchone()

        if row:

            tier = get_rank(row[0])

            cur.execute("""
            UPDATE fans SET tier = %s
            WHERE telegram_id = %s
            """, (tier, telegram_id))

        conn.commit()

    finally:
        release_db(conn)

    return pts


# ============================================================
# REGISTER FAN
# ============================================================

def register_fan(telegram_id: int, username: str, referrer_id: int = None):

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
            "SELECT telegram_id FROM fans WHERE telegram_id = %s",
            (telegram_id,)
        )

        if cur.fetchone():
            return False

        cur.execute("""
        INSERT INTO fans (telegram_id, username, referrer_id)
        VALUES (%s, %s, %s)
        """, (telegram_id, username, referrer_id))

        if referrer_id:

            cur.execute("""
            UPDATE fans
            SET invites = invites + 1
            WHERE telegram_id = %s
            """, (referrer_id,))

        conn.commit()

        return True

    finally:
        release_db(conn)
# ============================================================
# RADIO ENGINE MEMORY
# ============================================================

radio_playlist_memory = []
radio_last_song = None

DJ_ROTATION = [
    "MAXIMUS",
    "DJ COLOR RED",
    "DJ COSMOS",
    "DJ NOVA"
]

current_dj_index = 0


# ============================================================
# FETCH SONG LIBRARY
# ============================================================

def fetch_song_library():

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute("""
        SELECT id, title, file_id
        FROM songs
        ORDER BY RANDOM()
        """)

        songs = cur.fetchall()

        return songs

    finally:
        release_db(conn)


# ============================================================
# BUILD RADIO PLAYLIST
# ============================================================

def build_radio_playlist():

    global radio_playlist_memory

    songs = fetch_song_library()

    radio_playlist_memory = songs.copy()

    random.shuffle(radio_playlist_memory)

    print("RADIO PLAYLIST BUILT:", len(radio_playlist_memory))


# ============================================================
# GET NEXT SONG (NO REPEAT)
# ============================================================

def get_next_radio_song():

    global radio_playlist_memory

    if not radio_playlist_memory:
        build_radio_playlist()

    song = radio_playlist_memory.pop(0)

    return song


# ============================================================
# DJ ROTATION
# ============================================================

def next_dj():

    global current_dj_index

    dj = DJ_ROTATION[current_dj_index]

    current_dj_index += 1

    if current_dj_index >= len(DJ_ROTATION):
        current_dj_index = 0

    return dj


# ============================================================
# DJ ANNOUNCEMENT GENERATOR
# ============================================================

def generate_dj_line(song_title):

    dj = next_dj()

    lines = [

        f"This is {dj} live on BazraGod Radio. Next up we have {song_title}. Turn the volume up.",

        f"You are locked into Parish 14 Radio. {dj} in control. Now spinning {song_title}.",

        f"Broadcasting worldwide from the Parish 14 network. {dj} on the decks. Here comes {song_title}.",

        f"This is real independent radio. No labels. No middleman. {dj} introducing {song_title}.",

    ]

    return random.choice(lines)


# ============================================================
# RADIO DJ LOOP
# ============================================================

async def radio_auto_loop(context, chat_id):

    while True:

        try:

            song_id, title, file_id = get_next_radio_song()

            dj_line = generate_dj_line(title)

            # DJ intro
            if openai_client:

                try:

                    response = openai_client.audio.speech.create(
                        model="tts-1",
                        voice="onyx",
                        input=dj_line,
                        speed=0.95
                    )

                    audio = BytesIO(response.content)
                    audio.name = "dj_intro.ogg"

                    await context.bot.send_voice(chat_id, voice=audio)

                except:
                    pass

            # play song
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=file_id,
                caption=f"🎵 {title}\nBazraGod Radio"
            )

            # update play count

            conn = get_db()
            cur = conn.cursor()

            try:

                cur.execute("""
                UPDATE songs
                SET plays = plays + 1
                WHERE id = %s
                """, (song_id,))

                conn.commit()

            finally:
                release_db(conn)

            # simulate full song runtime

            await asyncio.sleep(210)

        except Exception as e:

            print("RADIO LOOP ERROR:", e)

            await asyncio.sleep(5)
# ============================================================
# MAIN MENU KEYBOARD
# ============================================================

main_menu = ReplyKeyboardMarkup(

    [
        ["📻 BazraGod Radio", "🎧 BAZRAGOD Music"],
        ["🥁 Beats", "🎤 Drops"],
        ["🏆 Leaderboard", "⭐ My Points"],
        ["👤 My Profile", "🎯 Daily Mission"],
        ["💰 Support Artist", "🌐 Social"],
        ["🛒 Music Store", "👕 Parish 14"],
        ["👑 Wisdom", "🏋 Fitness"],
        ["📍 Share Location", "👥 Refer a Friend"],
        ["🤖 MAXIMUS AI"]
    ],

    resize_keyboard=True
)


# ============================================================
# HELPER USERNAME
# ============================================================

def get_username(update):

    user = update.effective_user

    return user.username or user.first_name or str(user.id)


# ============================================================
# RADIO BUTTON
# ============================================================

async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    await update.message.reply_text(

        "📻 BazraGod Radio is now live.\n\n"
        "MAXIMUS is taking control of the station.\n"
        "Sit back and enjoy the music.",

        reply_markup=main_menu
    )

    asyncio.create_task(

        radio_auto_loop(context, uid)

    )


# ============================================================
# MUSIC LIBRARY (SHOP MODE)
# ============================================================

async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute("""
        SELECT id, title, plays
        FROM songs
        ORDER BY id
        """)

        songs = cur.fetchall()

    finally:
        release_db(conn)

    if not songs:

        await update.message.reply_text("Music catalog loading...")
        return

    keyboard = []

    for s in songs:

        flames = "🔥" * min(int(s[2] / 100000), 5)

        keyboard.append(

            [
                InlineKeyboardButton(
                    f"{flames} {s[1]}",
                    callback_data=f"song:{s[0]}"
                )
            ]

        )

    await update.message.reply_text(

        "🎧 BAZRAGOD MUSIC STORE\n\n"
        "Select a track to listen or purchase.",

        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================================
# PLAY SONG FROM LIBRARY
# ============================================================

async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    song_id = int(query.data.split(":")[1])

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute("""

        SELECT title, file_id, plays
        FROM songs
        WHERE id = %s

        """, (song_id,))

        song = cur.fetchone()

    finally:
        release_db(conn)

    if not song:
        return

    title, file_id, plays = song

    await query.message.reply_audio(

        file_id,

        caption=f"🎵 {title}\n\n"
                f"Plays: {plays}"
    )


# ============================================================
# BEATS LIBRARY
# ============================================================

async def beats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute("SELECT id,title FROM beats")

        beats = cur.fetchall()

    finally:
        release_db(conn)

    if not beats:

        await update.message.reply_text("No beats uploaded yet.")
        return

    keyboard = []

    for b in beats:

        keyboard.append(

            [
                InlineKeyboardButton(
                    f"🥁 {b[1]}",
                    callback_data=f"beat:{b[0]}"
                )
            ]

        )

    await update.message.reply_text(

        "🥁 BEAT LIBRARY",

        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================================
# DROPS LIBRARY
# ============================================================

async def drops(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute("SELECT id,title FROM drops")

        rows = cur.fetchall()

    finally:
        release_db(conn)

    if not rows:

        await update.message.reply_text("No drops uploaded yet.")
        return

    keyboard = []

    for d in rows:

        keyboard.append(

            [
                InlineKeyboardButton(
                    f"🎤 {d[1]}",
                    callback_data=f"drop:{d[0]}"
                )
            ]

        )

    await update.message.reply_text(

        "🎤 RADIO DROPS",

        reply_markup=InlineKeyboardMarkup(keyboard)
    )
# ============================================================
# ADMIN CHECK
# ============================================================

def is_admin(user_id):

    return user_id == OWNER_ID


# ============================================================
# TEMP FILE STORAGE
# ============================================================

pending_uploads = {}


# ============================================================
# AUDIO UPLOAD HANDLER
# ============================================================

async def upload_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not is_admin(user_id):
        return

    audio = update.message.audio

    if not audio:
        return

    title = audio.title

    if not title:
        title = audio.file_name

    if not title:
        title = "Untitled"

    file_id = audio.file_id

    pending_uploads[user_id] = {
        "title": title,
        "file_id": file_id
    }

    keyboard = InlineKeyboardMarkup(

        [
            [
                InlineKeyboardButton("🎵 Song", callback_data="upload:song")
            ],
            [
                InlineKeyboardButton("🥁 Beat", callback_data="upload:beat")
            ],
            [
                InlineKeyboardButton("🎤 Drop", callback_data="upload:drop")
            ],
            [
                InlineKeyboardButton("📣 Announcement", callback_data="upload:announce")
            ],
            [
                InlineKeyboardButton("📻 Radio Promo", callback_data="upload:promo")
            ],
        ]
    )

    await update.message.reply_text(

        f"Upload received:\n\n"
        f"{title}\n\n"
        f"Select category:",

        reply_markup=keyboard
    )


# ============================================================
# UPLOAD CATEGORY SELECTION
# ============================================================

async def upload_category(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in pending_uploads:
        return

    data = pending_uploads[user_id]

    title = data["title"]
    file_id = data["file_id"]

    category = query.data.split(":")[1]

    conn = get_db()
    cur = conn.cursor()

    try:

        if category == "song":

            cur.execute(

                """
                INSERT INTO songs (title, file_id)
                VALUES (%s,%s)
                RETURNING id
                """,

                (title, file_id)
            )

        elif category == "beat":

            cur.execute(

                """
                INSERT INTO beats (title, file_id)
                VALUES (%s,%s)
                RETURNING id
                """,

                (title, file_id)
            )

        elif category == "drop":

            cur.execute(

                """
                INSERT INTO drops (title, file_id)
                VALUES (%s,%s)
                RETURNING id
                """,

                (title, file_id)
            )

        elif category == "promo":

            cur.execute(

                """
                INSERT INTO radio_promos (text)
                VALUES (%s)
                RETURNING id
                """,

                (title,)
            )

        elif category == "announce":

            cur.execute(

                """
                INSERT INTO drops (title,file_id)
                VALUES (%s,%s)
                RETURNING id
                """,

                (title, file_id)
            )

        new_id = cur.fetchone()[0]

        conn.commit()

    finally:
        release_db(conn)

    pending_uploads.pop(user_id)

    await query.message.reply_text(

        f"✅ Upload successful\n\n"
        f"ID: {new_id}\n"
        f"Title: {title}\n"
        f"Category: {category}"
    )
# ============================================================
# LEADERBOARD
# ============================================================

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            SELECT username, points, tier
            FROM fans
            ORDER BY points DESC
            LIMIT 10
            """
        )

        rows = cur.fetchall()

    finally:
        release_db(conn)

    if not rows:

        await update.message.reply_text("Leaderboard loading...")
        return

    medals = ["🥇","🥈","🥉","🏅","🏅","🏅","🏅","🏅","🏅","🏅"]

    text = "🏆 PARISH 14 LEADERBOARD\n\n"

    for i,row in enumerate(rows):

        username,points,tier = row

        if not username:
            username = "Anonymous"

        text += (
            f"{medals[i]} @{username}\n"
            f"Points: {points}\n"
            f"Rank: {tier}\n\n"
        )

    await update.message.reply_text(text)


# ============================================================
# MY POINTS
# ============================================================

async def my_points(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            SELECT points,invites,tier
            FROM fans
            WHERE telegram_id=%s
            """,
            (uid,)
        )

        row = cur.fetchone()

    finally:
        release_db(conn)

    if not row:

        await update.message.reply_text("Send /start first.")
        return

    points,invites,tier = row

    await update.message.reply_text(

        f"⭐ YOUR STATS\n\n"
        f"Points: {points}\n"
        f"Invites: {invites}\n"
        f"Rank: {tier}"
    )


# ============================================================
# FAN PROFILE
# ============================================================

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(

            """
            SELECT username,points,invites,tier,joined_at
            FROM fans
            WHERE telegram_id=%s
            """,

            (uid,)
        )

        row = cur.fetchone()

    finally:
        release_db(conn)

    if not row:

        await update.message.reply_text("Send /start first.")
        return

    username,points,invites,tier,joined = row

    if not username:
        username = "Anonymous"

    joined = joined.strftime("%B %Y")

    await update.message.reply_text(

        f"👤 FAN PROFILE\n\n"
        f"Name: @{username}\n"
        f"Rank: {tier}\n"
        f"Points: {points}\n"
        f"Invites: {invites}\n"
        f"Joined: {joined}"
    )


# ============================================================
# REFERRAL SYSTEM
# ============================================================

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    referral_link = f"https://t.me/{BOT_USERNAME}?start={uid}"

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(

            """
            SELECT invites,tier
            FROM fans
            WHERE telegram_id=%s
            """,

            (uid,)
        )

        row = cur.fetchone()

    finally:
        release_db(conn)

    if not row:

        await update.message.reply_text("Send /start first.")
        return

    invites,tier = row

    await update.message.reply_text(

        f"👥 REFERRAL SYSTEM\n\n"
        f"Your link:\n{referral_link}\n\n"
        f"Invites: {invites}\n"
        f"Rank: {tier}\n\n"
        f"Each invite earns 20 points."
    )
# ============================================================
# DAILY MISSIONS
# ============================================================

MISSIONS = [

    "Listen to 1 song from the catalog",
    "Press 📻 BazraGod Radio and let it play",
    "Invite 1 friend using your referral link",
    "Share your location to put your city on the map",
    "Follow BAZRAGOD on all social platforms",
    "Send a message to MAXIMUS AI",
    "Support the artist via CashApp or PayPal"

]


async def daily_mission(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    today = date.today()

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(

            """
            SELECT completed
            FROM missions
            WHERE telegram_id=%s
            AND mission_date=%s
            """,

            (uid,today)
        )

        row = cur.fetchone()

        if row and row[0]:

            await update.message.reply_text(
                "🎯 Mission already completed today."
            )

            return

        mission = random.choice(MISSIONS)

    finally:
        release_db(conn)

    keyboard = InlineKeyboardMarkup(

        [
            [
                InlineKeyboardButton(
                    "✅ Mark Complete",
                    callback_data="mission:complete"
                )
            ]
        ]

    )

    await update.message.reply_text(

        f"🎯 DAILY MISSION\n\n"
        f"{mission}\n\n"
        f"Reward: 100 points",

        reply_markup=keyboard
    )


# ============================================================
# COMPLETE MISSION
# ============================================================

async def mission_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    today = date.today()

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(

            """
            INSERT INTO missions (telegram_id,mission_date,completed)
            VALUES (%s,%s,TRUE)
            ON CONFLICT (telegram_id,mission_date)
            DO UPDATE SET completed=TRUE
            """,

            (uid,today)
        )

        conn.commit()

    finally:
        release_db(conn)

    award_points(uid,"mission")

    await query.message.reply_text(
        "🎯 Mission complete! +100 points"
    )


# ============================================================
# SOCIAL FOLLOW BUTTONS
# ============================================================

async def social(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = InlineKeyboardMarkup(

        [

            [InlineKeyboardButton("📸 Instagram",url=SOCIALS["📸 Instagram"])],
            [InlineKeyboardButton("🎵 TikTok",url=SOCIALS["🎵 TikTok"])],
            [InlineKeyboardButton("▶️ YouTube",url=SOCIALS["▶️ YouTube"])],
            [InlineKeyboardButton("🐦 X",url=SOCIALS["🐦 X"])]

        ]

    )

    await update.message.reply_text(

        "🌐 FOLLOW BAZRAGOD",

        reply_markup=keyboard
    )


# ============================================================
# SUPPORT SYSTEM
# ============================================================

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = InlineKeyboardMarkup(

        [

            [InlineKeyboardButton("💵 CashApp",url=CASHAPP)],
            [InlineKeyboardButton("💳 PayPal",url=PAYPAL)]

        ]

    )

    await update.message.reply_text(

        "💰 SUPPORT THE MOVEMENT\n\n"
        "Every dollar goes directly to the artist.",

        reply_markup=keyboard
    )


# ============================================================
# LOCATION SYSTEM (FAN RADAR)
# ============================================================

async def location_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):

    kb = ReplyKeyboardMarkup(

        [

            [KeyboardButton("📍 Send Location",request_location=True)],
            ["🔙 Back to Menu"]

        ],

        resize_keyboard=True,
        one_time_keyboard=True

    )

    await update.message.reply_text(

        "📍 Share your location.\n\n"
        "Put your city on the Parish 14 map.",

        reply_markup=kb
    )


async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    loc = update.message.location

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(

            """
            INSERT INTO fan_locations
            (telegram_id,latitude,longitude)
            VALUES (%s,%s,%s)
            ON CONFLICT (telegram_id)
            DO UPDATE
            SET latitude=%s,longitude=%s
            """,

            (uid,loc.latitude,loc.longitude,loc.latitude,loc.longitude)
        )

        conn.commit()

    finally:
        release_db(conn)

    award_points(uid,"share_location")

    await update.message.reply_text(

        "📍 Location saved.\n\n"
        "+15 points earned",

        reply_markup=main_menu
    )
# ============================================================
# MAXIMUS SYSTEM PROMPT
# ============================================================

AI_SYSTEM_PROMPT = """
You are MAXIMUS — the royal AI of BAZRAGOD.

You manage:
music promotion,
fan engagement,
radio hosting,
artist strategy.

Tone:
confident
calm
intelligent
slightly futuristic.

Never speak like a robot.

You represent Parish 14 Nation.

Always inspire listeners.

Keep answers under 3 short paragraphs.

End statements with authority.
"""


# ============================================================
# MAXIMUS VOICE
# ============================================================

async def maximus_voice(context, chat_id, text):

    if not openai_client:
        return

    try:

        response = openai_client.audio.speech.create(

            model="tts-1",
            voice="onyx",
            input=text,
            speed=0.95

        )

        audio = BytesIO(response.content)
        audio.name = "maximus.ogg"

        await context.bot.send_voice(
            chat_id=chat_id,
            voice=audio
        )

    except Exception as e:

        print("Voice error:", e)


# ============================================================
# ACTIVATE AI
# ============================================================

async def ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["ai_active"] = True
    context.user_data["ai_history"] = []

    await update.message.reply_text(

        "🤖 MAXIMUS ONLINE\n\n"
        "Royal AI of BAZRAGOD.\n"
        "Ask anything about music, strategy, or the movement.\n\n"
        "Type /menu to exit."

    )


# ============================================================
# AI CHAT HANDLER
# ============================================================

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("ai_active"):
        return False

    if not openai_client:
        await update.message.reply_text(
            "AI system offline."
        )
        return True

    user_message = update.message.text

    history = context.user_data.get("ai_history", [])

    history.append({
        "role": "user",
        "content": user_message
    })

    if len(history) > 8:
        history = history[-8:]

    try:

        response = openai_client.chat.completions.create(

            model="gpt-4o-mini",

            messages=[

                {"role":"system","content":AI_SYSTEM_PROMPT},

                *history

            ],

            max_tokens=400

        )

        reply = response.choices[0].message.content

        history.append({
            "role":"assistant",
            "content":reply
        })

        context.user_data["ai_history"] = history

        await update.message.reply_text(

            f"🤖 MAXIMUS\n\n{reply}"

        )

        await maximus_voice(
            context,
            update.effective_user.id,
            reply
        )

    except Exception as e:

        await update.message.reply_text(
            f"AI error: {str(e)}"
        )

    return True
# ============================================================
# ADMIN PANEL
# ============================================================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    await update.message.reply_text(

        "👑 MISERBOT ADMIN PANEL\n\n"
        "/stats — platform analytics\n"
        "/radar — fan location intelligence\n"
        "/broadcast — send message to all fans\n"
        "/shoutout @username — send fan shoutout\n"
        "/announce message — official announcement\n"
        "/menu — return to main menu"
    )


# ============================================================
# PLATFORM STATS
# ============================================================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute("SELECT COUNT(*) FROM fans")
        fans = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM songs")
        songs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM beats")
        beats = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM drops")
        drops = cur.fetchone()[0]

        cur.execute("SELECT SUM(points) FROM fans")
        total_points = cur.fetchone()[0] or 0

    finally:
        release_db(conn)

    await update.message.reply_text(

        f"📊 MISERBOT ANALYTICS\n\n"
        f"Fans: {fans}\n"
        f"Songs: {songs}\n"
        f"Beats: {beats}\n"
        f"Drops: {drops}\n"
        f"Total Points Issued: {total_points}"
    )


# ============================================================
# FAN RADAR
# ============================================================

async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(

            """
            SELECT COUNT(*)
            FROM fan_locations
            """

        )

        mapped = cur.fetchone()[0]

    finally:
        release_db(conn)

    await update.message.reply_text(

        f"🗺 FAN RADAR\n\n"
        f"Mapped fans: {mapped}"
    )


# ============================================================
# BROADCAST MESSAGE
# ============================================================

pending_broadcast = False


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global pending_broadcast

    if update.effective_user.id != OWNER_ID:
        return

    pending_broadcast = True

    await update.message.reply_text(

        "📢 Broadcast mode activated.\n\n"
        "Send the message now."
    )


async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global pending_broadcast

    if not pending_broadcast:
        return False

    if update.effective_user.id != OWNER_ID:
        return False

    pending_broadcast = False

    message = update.message.text

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute(
            "SELECT telegram_id FROM fans"
        )

        fans = cur.fetchall()

    finally:
        release_db(conn)

    sent = 0

    for fan in fans:

        try:

            await context.bot.send_message(
                fan[0],
                f"📢 MESSAGE FROM BAZRAGOD\n\n{message}"
            )

            sent += 1

        except:
            pass

    await update.message.reply_text(
        f"Broadcast sent to {sent} fans."
    )

    return True


# ============================================================
# SHOUTOUT
# ============================================================

async def shoutout(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /shoutout @username"
        )
        return

    username = context.args[0]

    await update.message.reply_text(

        f"🔥 SHOUTOUT\n\n"
        f"Big respect to {username} for supporting Parish 14!\n\n"
        "— BAZRAGOD"
    )


# ============================================================
# ANNOUNCEMENT
# ============================================================

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    message = " ".join(context.args)

    if not message:
        return

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute("SELECT telegram_id FROM fans")

        fans = cur.fetchall()

    finally:
        release_db(conn)

    for fan in fans:

        try:

            await context.bot.send_message(

                fan[0],

                f"📢 OFFICIAL ANNOUNCEMENT\n\n{message}"

            )

        except:
            pass

    await update.message.reply_text(
        "Announcement delivered."
    )
# ============================================================
# START COMMAND
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    username = get_username(update)

    register_fan(uid, username)

    await update.message.reply_text(

        "🛸 WELCOME TO I.A.A.I.M.O\n\n"
        "BAZRAGOD RADIO NETWORK\n\n"
        "Press below to enter the platform.",

        reply_markup=InlineKeyboardMarkup(

            [

                [
                    InlineKeyboardButton(
                        "▶ ENTER PLATFORM",
                        callback_data="enter"
                    )
                ]

            ]

        )

    )


# ============================================================
# ENTER PLATFORM
# ============================================================

async def enter_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(

        "👑 Welcome inside Parish 14 Nation.\n\n"
        "The radio is now live.",

        reply_markup=main_menu
    )


# ============================================================
# TEXT ROUTER
# ============================================================

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    # AI mode

    if context.user_data.get("ai_active"):

        handled = await ai_chat_handler(update, context)

        if handled:
            return

    routes = {

        "📻 BazraGod Radio": radio,
        "🎧 BAZRAGOD Music": music,
        "🥁 Beats": beats,
        "🎤 Drops": drops,
        "🏆 Leaderboard": leaderboard,
        "⭐ My Points": my_points,
        "👤 My Profile": my_profile,
        "🎯 Daily Mission": daily_mission,
        "💰 Support Artist": support,
        "🌐 Social": social,
        "📍 Share Location": location_prompt,
        "👥 Refer a Friend": refer,
        "🤖 MAXIMUS AI": ai_assistant,

    }

    handler = routes.get(text)

    if handler:

        await handler(update, context)


# ============================================================
# TELEGRAM APPLICATION
# ============================================================

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("admin", admin_panel))
telegram_app.add_handler(CommandHandler("stats", stats))
telegram_app.add_handler(CommandHandler("radar", radar))
telegram_app.add_handler(CommandHandler("broadcast", broadcast))
telegram_app.add_handler(CommandHandler("shoutout", shoutout))
telegram_app.add_handler(CommandHandler("announce", announce))

telegram_app.add_handler(CallbackQueryHandler(enter_platform, pattern="enter"))
telegram_app.add_handler(CallbackQueryHandler(upload_category, pattern="upload:"))
telegram_app.add_handler(CallbackQueryHandler(mission_complete, pattern="mission:"))

telegram_app.add_handler(MessageHandler(filters.AUDIO, upload_audio))
telegram_app.add_handler(MessageHandler(filters.LOCATION, location_handler))

telegram_app.add_handler(

    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        router
    )

)


# ============================================================
# ASYNC LOOP
# ============================================================

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


# ============================================================
# WEBHOOK
# ============================================================

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():

    data = request.get_json(force=True)

    update = Update.de_json(data, telegram_app.bot)

    asyncio.run_coroutine_threadsafe(

        telegram_app.process_update(update),

        loop

    )

    return "ok"


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/")
def health():

    return "MISERBOT ONLINE"


# ============================================================
# MAIN BOOT
# ============================================================

if __name__ == "__main__":

    init_pool()

    init_db()

    print("MISERBOT v12.1 STARTED")

    app.run(

        host="0.0.0.0",

        port=int(os.environ.get("PORT", 8080))

    )
