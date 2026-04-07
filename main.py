"""
╔══════════════════════════════════════════════════════════════╗
║           I.A.A.I.M.O — MASTER SYSTEM v5000                 ║
║   Independent Artists Artificial Intelligence Music Ops      ║
║   Bot:     Miserbot                                          ║
║   Owner:   BAZRAGOD                                          ║
║   Nation:  Parish 14                                         ║
║   Mission: Global Artist Independence                        ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import random
import asyncio
import threading
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from io import BytesIO
from datetime import datetime, date
from openai import OpenAI
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

# ╔══════════════════════════════════════════════════════════════╗
# ║                        CONFIG                                ║
# ╚══════════════════════════════════════════════════════════════╝

BOT_TOKEN    = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
OPENAI_KEY   = os.environ.get("OPENAI_API_KEY")
ADMIN_ID     = 8741545426
BOT_USERNAME = "miserbot"
WEBHOOK_PATH = "/webhook"

INTRO_FILE_ID = os.environ.get(
    "INTRO_FILE_ID",
    "CQACAgEAAxkBAAICN2nUZHzzXlQszP-a08nJiSctUeOhAAL-BQACEbKpRg3vpxJvYve3OwQ"
)

CASHAPP = "https://cash.app/$BAZRAGOD"
PAYPAL  = "https://paypal.me/bazragod1"

SOCIALS = {
    "📸 Instagram": "https://www.instagram.com/bazragod_timeless",
    "🎵 TikTok":    "https://www.tiktok.com/@bazragod_official",
    "▶️ YouTube":   "https://youtube.com/@bazragodmusictravelandleis8835",
    "🐦 X":         "https://x.com/toligarch65693",
}

# ╔══════════════════════════════════════════════════════════════╗
# ║                  CONNECTION POOL (FIX 1)                     ║
# ╚══════════════════════════════════════════════════════════════╝

db_pool = None

def init_pool():
    global db_pool
    db_pool = SimpleConnectionPool(1, 10, dsn=DATABASE_URL)
    print("Connection pool initialized")

def get_db():
    return db_pool.getconn()

def release_db(conn):
    db_pool.putconn(conn)

# ╔══════════════════════════════════════════════════════════════╗
# ║                     POINTS TABLE                             ║
# ╚══════════════════════════════════════════════════════════════╝

POINTS = {
    "start":          5,
    "play_song":      8,
    "play_beat":      6,
    "radio":         10,
    "share_location":15,
    "follow_social":  3,
    "support_artist": 5,
    "invite_friend": 20,
    "wisdom":         3,
    "fitness":        3,
    "ai_chat":        2,
    "buy_music":     50,
    "mission":      100,
}

# ╔══════════════════════════════════════════════════════════════╗
# ║                    RANK SYSTEM                               ║
# ╚══════════════════════════════════════════════════════════════╝

RANKS = [
    (0,    "🎧 Fan"),
    (100,  "⚔️  Supporter"),
    (500,  "🎖  Recruiter"),
    (1000, "🏅  Commander"),
    (2500, "👑  General"),
    (5000, "🛸  Parish 14 Elite"),
]

REFERRAL_TIERS = {
    5:  "⚔️  Supporter",
    10: "🎖  Recruiter",
    25: "🏅  Commander",
    50: "👑  General",
}

def get_rank(points: int) -> str:
    rank = RANKS[0][1]
    for threshold, label in RANKS:
        if points >= threshold:
            rank = label
    return rank

# ╔══════════════════════════════════════════════════════════════╗
# ║                  MUSIC STORE PRICES                          ║
# ╚══════════════════════════════════════════════════════════════╝

STORE_ITEMS = {
    "single":    ("Single Song Download",    5),
    "bundle":    ("Bundle — 7 Songs",       20),
    "exclusive": ("Exclusive Album — VIP", 500),
}

MERCH_ITEMS = {
    "tshirt":   ("Parish 14 T-Shirt",   50),
    "pullover": ("Parish 14 Pullover", 150),
}

# ╔══════════════════════════════════════════════════════════════╗
# ║                  DAILY MISSIONS                              ║
# ╚══════════════════════════════════════════════════════════════╝

MISSIONS = [
    "Listen to 1 song from the catalog",
    "Press 📻 Radio and let it play",
    "Invite 1 friend using your referral link",
    "Share your location to put your city on the map",
    "Follow BAZRAGOD on all social platforms",
    "Check the leaderboard and see your rank",
    "Send a message to MAXIMUS AI",
    "Support the artist via CashApp or PayPal",
]

# ╔══════════════════════════════════════════════════════════════╗
# ║            RADIO ENGINE (FIX 3 — PROMO SLOT)                ║
# ╚══════════════════════════════════════════════════════════════╝

RADIO_CYCLE   = ["song", "song", "drop", "song", "beat", "promo"]
radio_position = 0

RADIO_PROMOS = [
    "Parish 14 merch available now. Rep the nation.",
    "Support independent music. Hit the Support button.",
    "Invite friends to climb the leaderboard. Parish 14 grows stronger.",
    "New BAZRAGOD music in the catalog. Go listen.",
    "Share your location. Put your city on the fan map.",
    "I.A.A.I.M.O — no label, no middleman, just BAZRAGOD.",
]

# ╔══════════════════════════════════════════════════════════════╗
# ║                   SEED CATALOG                               ║
# ╚══════════════════════════════════════════════════════════════╝

SEED_SONGS = [
    ("Chibonge Remix Rap Version",   "CQACAgEAAxkBAAOtadMWVB7xX8ss7Nkp6neA0L7gbU0AAvQIAAI1Z5hGYMUV7Mozbyw7BA"),
    ("Natural Pussy (Tie Mi)",       "CQACAgEAAxkBAAO1adMZtjgiRqYxrOFbE3KOCNxVcxQAAvgIAAI1Z5hGm8QmWqNIojg7BA"),
    ("Fraid Ah Yuh (Feat. Dami D)",  "CQACAgEAAxkBAAO3adMZ_P5y2OoXlyY0XpO_fiPiahMAAvkIAAI1Z5hGgMZ1tOmyhjA7BA"),
    ("Mini 14 (Raw)",                "CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
    ("Boom Boom",                    "CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
    ("Summertime",                   "CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA"),
    ("Mini 14 HD Mix",               "CQACAgEAAxkBAAPBadMcgWIUbXd6lfNjIt8C_SMhpz8AAv4IAAI1Z5hGrA8jfr5073A7BA"),
    ("Carry Guh Bring Come",         "CQACAgEAAxkBAAPFadMdgVBA0MIwyLNyU8mO5-djfawAAgQJAAI1Z5hGYmzehzRMIZY7BA"),
    ("Trapp (Master)",               "CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
    ("Gunman",                       "CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
    ("Impeccable",                   "CQACAgEAAxkBAAPRadMgsX9xJh3boHp64jA1-sVPC80AAgsJAAI1Z5hGIlCi8cg5E_k7BA"),
    ("Fear",                         "CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA"),
    ("Bubble Fi Mi",                 "CQACAgEAAxkBAAPPadMgBMh10TStncJQXpkyD0mJYM8AAgoJAAI1Z5hG10QJbSDmTyM7BA"),
    ("Big Fat Matic",                "CQACAgEAAxkBAAPNadMfiOZJNeE3Eihp-r-olvpfzWIAAgkJAAI1Z5hGaNvyiVRhwEw7BA"),
    ("Mi Alone",                     "CQACAgEAAxkBAAPJadMeaMExYAvnDv8gswXyUgOMwpsAAgcJAAI1Z5hGxeKB46IBYZg7BA"),
    ("Real Gold",                    "CQACAgEAAxkBAAO9adMbBDzajJrOcGNb6gVyZmjEXTYAAvwIAAI1Z5hGr3nvGz4AAYjbOwQ"),
    ("Facebook Lust",                "CQACAgEAAxkBAAOzadMY-pj_rWBB5wrRP6Nfymv4q6EAAvcIAAI1Z5hG4SGuftZqhPY7BA"),
    ("BAZRAGOD & Sara Charismata",   "CQACAgEAAxkBAAICWGnUbUMJb5_1Baajef0VQFq0HMCaAAIFBgACEbKpRluYDh3M8F57OwQ"),
]

QUOTES = [
    "He who conquers himself is the mightiest warrior.",
    "Never outshine the master.",
    "Discipline equals freedom.",
    "Appear weak when you are strong.",
    "The obstacle is the way.",
    "Silence is the most powerful scream.",
    "Move in silence. Only speak when it is time to say checkmate.",
    "A lion does not concern himself with the opinions of sheep.",
    "Kings are not born — they are made through discipline.",
    "Your network is your net worth. Build it wisely.",
    "The man who has no inner life is a slave to his surroundings.",
    "Do not pray for an easy life. Pray for the strength to endure a difficult one.",
]

FITNESS_MSG = """🏋 BAZRAGOD FITNESS PROTOCOL

Morning Circuit
• 50 Pushups
• 50 Squats
• 50 Situps
• 2km Run

Meal Plan
• Eggs and Rice
• Grilled Chicken
• Fresh Fruit
• Water only

No excuses. Repeat daily. 👑"""

AI_SYSTEM_PROMPT = """You are MAXIMUS — the Royal AI of BAZRAGOD,
founder of I.A.A.I.M.O.

Roles: Artist Manager, Publicist, Tour Strategist,
Fan Engagement Agent, Radio DJ, Music Business Advisor.

Personality: Sovereign, direct, loyal to BAZRAGOD.
Jamaican cultural pride. Black and Gold aesthetic.
Inspire fans. Protect the brand.

BAZRAGOD is independent — no label, no middleman.
He controls his music, fans, payments, and data.
His platform lives entirely inside Telegram.
Catalog has 18 tracks. Nation: Parish 14.

Keep responses concise for Telegram — max 3 paragraphs.
End every response with a power statement."""

# ╔══════════════════════════════════════════════════════════════╗
# ║               FLASK + OPENAI INIT                            ║
# ╚══════════════════════════════════════════════════════════════╝

flask_app      = Flask(__name__)
openai_client  = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None
pending_broadcasts: dict = {}

# ╔══════════════════════════════════════════════════════════════╗
# ║                     DATABASE                                 ║
# ╚══════════════════════════════════════════════════════════════╝

def init_db():
    conn = get_db()
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS fans (
            telegram_id  BIGINT PRIMARY KEY,
            username     TEXT,
            points       INT DEFAULT 0,
            invites      INT DEFAULT 0,
            referrer_id  BIGINT,
            tier         TEXT DEFAULT '🎧 Fan',
            city         TEXT,
            country      TEXT,
            joined_at    TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id          SERIAL PRIMARY KEY,
            title       TEXT,
            file_id     TEXT,
            uploaded_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS beats (
            id          SERIAL PRIMARY KEY,
            title       TEXT,
            file_id     TEXT,
            uploaded_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS drops (
            id          SERIAL PRIMARY KEY,
            title       TEXT,
            file_id     TEXT,
            uploaded_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # FIX 4 — radio promos table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS radio_promos (
            id   SERIAL PRIMARY KEY,
            text TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS fan_locations (
            telegram_id BIGINT PRIMARY KEY,
            city        TEXT,
            country     TEXT,
            latitude    FLOAT,
            longitude   FLOAT,
            updated_at  TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS point_log (
            id          SERIAL PRIMARY KEY,
            telegram_id BIGINT,
            action      TEXT,
            pts         INT,
            logged_at   TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS missions (
            telegram_id  BIGINT,
            mission_date DATE,
            completed    BOOLEAN DEFAULT FALSE,
            PRIMARY KEY  (telegram_id, mission_date)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id           SERIAL PRIMARY KEY,
            telegram_id  BIGINT,
            item         TEXT,
            price        INT,
            status       TEXT DEFAULT 'pending',
            purchased_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # Seed songs if empty
    cur.execute("SELECT COUNT(*) FROM songs")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO songs (title, file_id) VALUES (%s, %s)",
            SEED_SONGS,
        )
        print(f"Seeded {len(SEED_SONGS)} songs")

    conn.commit()
    release_db(conn)
    print("I.A.A.I.M.O DATABASE READY")

# ╔══════════════════════════════════════════════════════════════╗
# ║                   POINTS ENGINE                              ║
# ╚══════════════════════════════════════════════════════════════╝

def award_points(telegram_id: int, action: str, username: str = None) -> int:
    pts  = POINTS.get(action, 1)
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO fans (telegram_id, username, points)
            VALUES (%s, %s, %s)
            ON CONFLICT (telegram_id) DO UPDATE
            SET points   = fans.points + EXCLUDED.points,
                username = COALESCE(EXCLUDED.username, fans.username)
        """, (telegram_id, username, pts))

        cur.execute(
            "INSERT INTO point_log (telegram_id, action, pts) VALUES (%s, %s, %s)",
            (telegram_id, action, pts),
        )

        cur.execute(
            "SELECT points FROM fans WHERE telegram_id = %s",
            (telegram_id,),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE fans SET tier = %s WHERE telegram_id = %s",
                (get_rank(row[0]), telegram_id),
            )

        conn.commit()
    finally:
        release_db(conn)
    return pts


def register_fan(telegram_id: int, username: str, referrer_id: int = None) -> bool:
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT telegram_id FROM fans WHERE telegram_id = %s",
            (telegram_id,),
        )
        if cur.fetchone():
            return False

        cur.execute("""
            INSERT INTO fans (telegram_id, username, referrer_id)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (telegram_id, username, referrer_id))

        if referrer_id:
            cur.execute(
                "UPDATE fans SET invites = invites + 1 WHERE telegram_id = %s",
                (referrer_id,),
            )

        conn.commit()
        return True
    finally:
        release_db(conn)

# ╔══════════════════════════════════════════════════════════════╗
# ║                       MENUS                                  ║
# ╚══════════════════════════════════════════════════════════════╝

main_menu = ReplyKeyboardMarkup(
    [
        ["🎵 Music",          "📻 Radio"],
        ["🥁 Beats",          "🎤 Drops"],
        ["🏆 Leaderboard",    "⭐ My Points"],
        ["👤 My Profile",     "🎯 Daily Mission"],
        ["💰 Support Artist", "🌐 Social"],
        ["🛒 Music Store",    "👕 Parish 14 Merch"],
        ["👑 Wisdom",         "🏋 Fitness"],
        ["📍 Share Location", "👥 Refer a Friend"],
        ["🤖 AI Assistant"],
    ],
    resize_keyboard=True,
)

def get_username(update: Update) -> str:
    u = update.effective_user
    return u.username or u.first_name or str(u.id)

def is_admin(uid: int) -> bool:
    return uid == ADMIN_ID

# ╔══════════════════════════════════════════════════════════════╗
# ║         MAXIMUS VOICE ENGINE (FIX 5 — SAFE)                 ║
# ╚══════════════════════════════════════════════════════════════╝

async def maximus_speak(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
):
    if not openai_client:
        return
    try:
        response   = openai_client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=text,
            speed=0.95,
        )
        audio_file = BytesIO(response.content)
        audio_file.name = "maximus.ogg"
        await context.bot.send_voice(chat_id=chat_id, voice=audio_file)
    except Exception as e:
        print(f"MAXIMUS voice error: {e}")

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 1 — UFO LAUNCH + INTRO                        ║
# ╚══════════════════════════════════════════════════════════════╝

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    args = context.args

    referrer = None
    if args and args[0].isdigit():
        referrer = int(args[0])
        if referrer == uid:
            referrer = None

    is_new = register_fan(uid, name, referrer)
    pts    = award_points(uid, "start", name)

    if is_new and referrer:
        try:
            await context.bot.send_message(
                referrer,
                f"👥 A new soldier joined using your link!\n"
                f"+{POINTS['invite_friend']} points credited 🔥",
            )
            award_points(referrer, "invite_friend")
        except Exception:
            pass

    ufo = (
        "⠀⠀⠀⠀⠀✦ ⠀⠀⠀⠀✦⠀⠀⠀⠀⠀⠀✦\n"
        "⠀⠀✦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀✦⠀⠀⠀⠀\n"
        "⠀⠀⠀⠀⠀⠀⠀🛸⠀⠀⠀⠀⠀⠀⠀⠀\n"
        "⠀⠀⠀⠀✦⠀⠀⠀⠀⠀⠀⠀✦⠀⠀⠀\n\n"
        "▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄\n"
        "  B A Z R A G O D\n"
        "  I . A . A . I . M . O\n"
        "  PARISH 14 COMMAND\n"
        "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀\n\n"
        "Initiating entry sequence...\n"
        "Stand by. 🛸"
    )
    await update.message.reply_text(ufo)

    if INTRO_FILE_ID:
        await update.message.reply_text(
            "👑 Before you enter —\n\n"
            "Press play. This message is for real fans only. 🎙️"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "▶️  Press Play — Hear The Vision",
                callback_data="intro:play",
            )
        ]])
        await update.message.reply_voice(
            INTRO_FILE_ID,
            caption="🎙️ BAZRAGOD — The Vision\nI.A.A.I.M.O",
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(
            f"🛸 WELCOME TO I.A.A.I.M.O\n\n"
            f"Parish 14 Nation\n\n"
            f"+{pts} points awarded 🔥",
            reply_markup=main_menu,
        )


async def intro_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT points, tier FROM fans WHERE telegram_id = %s",
            (uid,),
        )
        row = cur.fetchone()
    finally:
        release_db(conn)

    pts  = row[0] if row else 0
    tier = row[1] if row else "🎧 Fan"

    await query.message.reply_text(
        f"🛸 YOU ARE NOW INSIDE\n\n"
        f"I.A.A.I.M.O — Parish 14 Nation.\n"
        f"No labels. No middlemen. Just the movement.\n\n"
        f"Rank:   {tier}\n"
        f"Points: {pts}\n\n"
        f"You are part of history in the making. 🔥\n"
        f"The platform is yours. 👑",
        reply_markup=main_menu,
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 4 — MUSIC CATALOG                             ║
# ╚══════════════════════════════════════════════════════════════╝

async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    award_points(uid, "play_song", name)

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, title FROM songs ORDER BY id")
        songs = cur.fetchall()
    finally:
        release_db(conn)

    if not songs:
        await update.message.reply_text("Catalog loading... check back soon.")
        return

    keyboard = [
        [InlineKeyboardButton(f"▶  {s[1]}", callback_data=f"song:{s[0]}")]
        for s in songs
    ]
    await update.message.reply_text(
        f"🎧 BAZRAGOD CATALOG\n"
        f"Parish 14 Nation — {len(songs)} tracks\n\n"
        f"Select a track 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def play_song_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # FIX 2 — safe callback parsing
    try:
        song_id = int(query.data.split(":")[1])
    except Exception:
        return

    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT title, file_id FROM songs WHERE id = %s",
            (song_id,),
        )
        song = cur.fetchone()
    finally:
        release_db(conn)

    if song:
        pts = award_points(uid, "play_song", name)
        await query.message.reply_audio(
            song[1],
            caption=f"🎵 {song[0]}\nBAZRAGOD\n\n+{pts} pts 🏆",
        )

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 5 — BEATS LIBRARY                             ║
# ╚══════════════════════════════════════════════════════════════╝

async def beats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, title FROM beats ORDER BY id")
        rows = cur.fetchall()
    finally:
        release_db(conn)

    if not rows:
        await update.message.reply_text("No beats uploaded yet. Heat incoming 🎹")
        return

    keyboard = [
        [InlineKeyboardButton(f"🥁  {r[1]}", callback_data=f"beat:{r[0]}")]
        for r in rows
    ]
    await update.message.reply_text(
        f"🥁 BAZRAGOD BEATS — {len(rows)} available",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def play_beat_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        beat_id = int(query.data.split(":")[1])
    except Exception:
        return

    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT title, file_id FROM beats WHERE id = %s",
            (beat_id,),
        )
        beat = cur.fetchone()
    finally:
        release_db(conn)

    if beat:
        pts = award_points(uid, "play_beat", name)
        await query.message.reply_audio(
            beat[1],
            caption=f"🥁 {beat[0]}\n\n+{pts} pts",
        )

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 6 — RADIO DROPS                               ║
# ╚══════════════════════════════════════════════════════════════╝

async def drops_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, title FROM drops ORDER BY id")
        rows = cur.fetchall()
    finally:
        release_db(conn)

    if not rows:
        await update.message.reply_text("No drops yet. Stay tuned 🔥")
        return

    keyboard = [
        [InlineKeyboardButton(f"🎤  {r[1]}", callback_data=f"drop:{r[0]}")]
        for r in rows
    ]
    await update.message.reply_text(
        f"🎤 RADIO DROPS — {len(rows)} available",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def play_drop_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        drop_id = int(query.data.split(":")[1])
    except Exception:
        return

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT title, file_id FROM drops WHERE id = %s",
            (drop_id,),
        )
        drop = cur.fetchone()
    finally:
        release_db(conn)

    if drop:
        await query.message.reply_audio(drop[1], caption=f"🎤 {drop[0]}")

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 7 — RADIO ENGINE (FIX 3+4+6)                 ║
# ╚══════════════════════════════════════════════════════════════╝

async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global radio_position

    uid  = update.effective_user.id
    name = get_username(update)
    now  = datetime.now().strftime("%I:%M %p")
    pts  = award_points(uid, "radio", name)

    slot = RADIO_CYCLE[radio_position % len(RADIO_CYCLE)]
    radio_position += 1

    if slot == "promo":
        # Pull from DB first, fall back to hardcoded
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute(
                "SELECT text FROM radio_promos ORDER BY RANDOM() LIMIT 1"
            )
            row = cur.fetchone()
        finally:
            release_db(conn)

        promo_text = row[0] if row else random.choice(RADIO_PROMOS)
        dj_text    = f"BazraGod Radio — {now}. {promo_text}"
        await maximus_speak(context, uid, dj_text)
        await update.message.reply_text(
            f"📻 BazraGod Radio — {now}\n\n🎙️ {promo_text}\n\n+{pts} pts"
        )
        return

    if slot == "drop":
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute(
                "SELECT title, file_id FROM drops ORDER BY RANDOM() LIMIT 1"
            )
            item = cur.fetchone()
        finally:
            release_db(conn)

        if item:
            dj_text = (
                f"BazraGod Radio — {now}. "
                f"Special drop incoming. {item[0]}. "
                f"Parish 14 Nation stay locked in."
            )
            await maximus_speak(context, uid, dj_text)
            await update.message.reply_audio(
                item[1],
                caption=f"📻 BazraGod Radio — {now}\n\n🎤 DROP: {item[0]}\n\n+{pts} pts",
            )
            return

    if slot == "beat":
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute(
                "SELECT title, file_id FROM beats ORDER BY RANDOM() LIMIT 1"
            )
            item = cur.fetchone()
        finally:
            release_db(conn)

        if item:
            dj_text = (
                f"BazraGod Radio. Time is {now}. "
                f"This beat is called {item[0]}. Feel it."
            )
            await maximus_speak(context, uid, dj_text)
            await update.message.reply_audio(
                item[1],
                caption=f"📻 BazraGod Radio — {now}\n\n🥁 BEAT: {item[0]}\n\n+{pts} pts",
            )
            return

    # Default — play song
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT title, file_id FROM songs ORDER BY RANDOM() LIMIT 1"
        )
        song = cur.fetchone()
    finally:
        release_db(conn)

    if not song:
        await update.message.reply_text("Radio loading... no songs found.")
        return

    dj_lines = [
        f"You are now listening to BazraGod Radio. {now}. Next up — {song[0]}. Stay locked in.",
        f"This is I.A.A.I.M.O Radio. We running {song[0]}. No label. No middleman. Just BAZRAGOD.",
        f"BazraGod Radio — {now}. Parish 14 Nation worldwide. {song[0]}. Turn it up.",
        f"Straight from the sovereign himself. {now} on BazraGod Radio. {song[0]}. Feel it.",
    ]
    await maximus_speak(context, uid, random.choice(dj_lines))
    await update.message.reply_audio(
        song[1],
        caption=f"📻 BazraGod Radio — {now}\n\n🎵 {song[0]}\n\n+{pts} pts 🔥",
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 9 — FAN PROFILE                               ║
# ╚══════════════════════════════════════════════════════════════╝

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT username, points, invites, tier, city, country, joined_at "
            "FROM fans WHERE telegram_id = %s",
            (uid,),
        )
        row = cur.fetchone()

        cur.execute(
            "SELECT COUNT(*) FROM fans WHERE points > "
            "COALESCE((SELECT points FROM fans WHERE telegram_id = %s), 0)",
            (uid,),
        )
        rank_pos = cur.fetchone()[0] + 1
    finally:
        release_db(conn)

    if not row:
        await update.message.reply_text("Profile not found. Send /start first.")
        return

    username, points, invites, tier, city, country, joined_at = row
    display  = f"@{username}" if username else name
    location = f"{city}, {country}" if city else "Not shared yet"
    joined   = joined_at.strftime("%B %Y") if joined_at else "Unknown"

    next_rank_msg = ""
    for threshold, label in RANKS:
        if points < threshold:
            next_rank_msg = f"\n🎯 {threshold - points} pts to reach {label}"
            break

    await update.message.reply_text(
        f"👤 FAN PROFILE\n"
        f"{'═' * 22}\n"
        f"Name:    {display}\n"
        f"Rank:    {tier}\n"
        f"Points:  {points}\n"
        f"#:       #{rank_pos} on leaderboard\n"
        f"Invites: {invites}\n"
        f"City:    {location}\n"
        f"Joined:  {joined}\n"
        f"{'═' * 22}"
        f"{next_rank_msg}"
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 10 — POINTS + LEADERBOARD                     ║
# ╚══════════════════════════════════════════════════════════════╝

async def my_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT points, invites, tier FROM fans WHERE telegram_id = %s",
            (uid,),
        )
        row = cur.fetchone()
        cur.execute(
            "SELECT COUNT(*) FROM fans WHERE points > "
            "COALESCE((SELECT points FROM fans WHERE telegram_id = %s), 0)",
            (uid,),
        )
        rank = cur.fetchone()[0] + 1
    finally:
        release_db(conn)

    pts, invites, tier = row if row else (0, 0, "🎧 Fan")

    next_tier_msg = ""
    for threshold, label in sorted(REFERRAL_TIERS.items()):
        if invites < threshold:
            next_tier_msg = f"Invite {threshold - invites} more to reach {label}"
            break

    await update.message.reply_text(
        f"⭐ YOUR STATS\n"
        f"{'═' * 22}\n"
        f"Points:  {pts}\n"
        f"Rank:    #{rank}\n"
        f"Tier:    {tier}\n"
        f"Invites: {invites}\n"
        f"{'═' * 22}\n"
        f"{next_tier_msg}\n\n"
        f"Keep grinding to climb 👑"
    )


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT username, points, invites, tier
            FROM fans
            ORDER BY points DESC
            LIMIT 10
        """)
        rows = cur.fetchall()
    finally:
        release_db(conn)

    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    text   = "🏆 PARISH 14 LEADERBOARD\n\n"

    for i, (username, points, invites, tier) in enumerate(rows):
        label = f"@{username}" if username else "Anonymous"
        text += f"{medals[i]} {label}\n   {points} pts — {tier}\n\n"

    await update.message.reply_text(text)

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 14 — DAILY MISSION                            ║
# ╚══════════════════════════════════════════════════════════════╝

async def daily_mission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid   = update.effective_user.id
    today = date.today()

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT completed FROM missions WHERE telegram_id = %s AND mission_date = %s",
            (uid, today),
        )
        row = cur.fetchone()

        if not row:
            cur.execute(
                "INSERT INTO missions (telegram_id, mission_date) VALUES (%s, %s) "
                "ON CONFLICT DO NOTHING",
                (uid, today),
            )
            conn.commit()
    finally:
        release_db(conn)

    if row and row[0]:
        await update.message.reply_text(
            f"🎯 DAILY MISSION\n\n"
            f"✅ Mission complete for today!\n\n"
            f"Come back tomorrow for a new mission.\n"
            f"+{POINTS['mission']} pts already earned 👑"
        )
        return

    mission_text = random.choice(MISSIONS)
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "✅ Mark Mission Complete",
            callback_data=f"mission:complete:{uid}",
        )
    ]])

    await update.message.reply_text(
        f"🎯 DAILY MISSION\n"
        f"{'═' * 22}\n\n"
        f"{mission_text}\n\n"
        f"Reward: +{POINTS['mission']} pts\n\n"
        f"Complete your mission then tap below 👇",
        reply_markup=keyboard,
    )


async def mission_complete_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        uid = int(query.data.split(":")[2])
    except Exception:
        return

    if query.from_user.id != uid:
        return

    today = date.today()
    conn  = get_db()
    cur   = conn.cursor()
    try:
        cur.execute(
            "SELECT completed FROM missions WHERE telegram_id = %s AND mission_date = %s",
            (uid, today),
        )
        row = cur.fetchone()

        if row and row[0]:
            await query.message.reply_text("✅ Already completed today!")
            return

        cur.execute("""
            INSERT INTO missions (telegram_id, mission_date, completed)
            VALUES (%s, %s, TRUE)
            ON CONFLICT (telegram_id, mission_date) DO UPDATE SET completed = TRUE
        """, (uid, today))
        conn.commit()
    finally:
        release_db(conn)

    name = query.from_user.username or query.from_user.first_name
    pts  = award_points(uid, "mission", name)

    await query.message.reply_text(
        f"🎯 MISSION COMPLETE!\n\n"
        f"+{pts} points awarded 🔥\n\n"
        f"Come back tomorrow. Parish 14 never stops. 👑"
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 15 — MUSIC STORE                              ║
# ╚══════════════════════════════════════════════════════════════╝

async def music_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"🎵 {STORE_ITEMS['single'][0]} — ${STORE_ITEMS['single'][1]}",
            callback_data="store:single",
        )],
        [InlineKeyboardButton(
            f"📦 {STORE_ITEMS['bundle'][0]} — ${STORE_ITEMS['bundle'][1]}",
            callback_data="store:bundle",
        )],
        [InlineKeyboardButton(
            f"👑 {STORE_ITEMS['exclusive'][0]} — ${STORE_ITEMS['exclusive'][1]}",
            callback_data="store:exclusive",
        )],
    ])
    await update.message.reply_text(
        f"🛒 BAZRAGOD MUSIC STORE\n"
        f"{'═' * 22}\n\n"
        f"Direct from the artist.\n"
        f"No streaming cuts. No label fees.\n"
        f"Every dollar funds the music.\n\n"
        f"Select your purchase 👇",
        reply_markup=keyboard,
    )


async def store_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        item_key = query.data.split(":")[1]
    except Exception:
        return

    if item_key not in STORE_ITEMS:
        return

    item_name, price = STORE_ITEMS[item_key]
    uid = query.from_user.id

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO purchases (telegram_id, item, price) VALUES (%s, %s, %s) RETURNING id",
            (uid, item_name, price),
        )
        purchase_id = cur.fetchone()[0]
        conn.commit()
    finally:
        release_db(conn)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 Pay via CashApp", url=CASHAPP)],
        [InlineKeyboardButton("💳 Pay via PayPal",  url=PAYPAL)],
    ])

    await query.message.reply_text(
        f"🛒 ORDER #{purchase_id}\n"
        f"{'═' * 22}\n\n"
        f"Item:  {item_name}\n"
        f"Price: ${price}\n\n"
        f"Send payment then message admin with proof.\n"
        f"Your download will be unlocked. 🔐",
        reply_markup=keyboard,
    )

    try:
        name = query.from_user.username or query.from_user.first_name
        await context.bot.send_message(
            ADMIN_ID,
            f"💰 NEW PURCHASE\n\n"
            f"Order: #{purchase_id}\n"
            f"Fan:   @{name} ({uid})\n"
            f"Item:  {item_name}\n"
            f"Price: ${price}",
        )
    except Exception:
        pass

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 17 — MERCH STORE                              ║
# ╚══════════════════════════════════════════════════════════════╝

async def merch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"👕 {MERCH_ITEMS['tshirt'][0]} — ${MERCH_ITEMS['tshirt'][1]}",
            callback_data="merch:tshirt",
        )],
        [InlineKeyboardButton(
            f"🧥 {MERCH_ITEMS['pullover'][0]} — ${MERCH_ITEMS['pullover'][1]}",
            callback_data="merch:pullover",
        )],
    ])
    await update.message.reply_text(
        f"👕 PARISH 14 MERCH\n"
        f"{'═' * 22}\n\n"
        f"Official BAZRAGOD clothing.\n"
        f"Wear the nation. Represent the movement.\n\n"
        f"Select your item 👇",
        reply_markup=keyboard,
    )


async def merch_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        item_key = query.data.split(":")[1]
    except Exception:
        return

    if item_key not in MERCH_ITEMS:
        return

    item_name, price = MERCH_ITEMS[item_key]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 Pay via CashApp", url=CASHAPP)],
        [InlineKeyboardButton("💳 Pay via PayPal",  url=PAYPAL)],
    ])

    await query.message.reply_text(
        f"👕 PARISH 14 ORDER\n"
        f"{'═' * 22}\n\n"
        f"Item:  {item_name}\n"
        f"Price: ${price}\n\n"
        f"After payment send admin:\n"
        f"• Your size\n"
        f"• Shipping address\n"
        f"• Payment confirmation\n\n"
        f"Parish 14 Nation. 👑",
        reply_markup=keyboard,
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 18 — SUPPORT                                  ║
# ╚══════════════════════════════════════════════════════════════╝

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    pts  = award_points(uid, "support_artist", name)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 CashApp", url=CASHAPP)],
        [InlineKeyboardButton("💳 PayPal",  url=PAYPAL)],
    ])
    await update.message.reply_text(
        f"💰 SUPPORT BAZRAGOD\n"
        f"{'═' * 22}\n\n"
        f"No label takes a cut here.\n"
        f"Every dollar goes directly to the music.\n\n"
        f"+{pts} pts for showing love 👑",
        reply_markup=keyboard,
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 19 — SOCIAL HUB                               ║
# ╚══════════════════════════════════════════════════════════════╝

async def social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    pts  = award_points(uid, "follow_social", name)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(platform, url=url)]
        for platform, url in SOCIALS.items()
    ])
    await update.message.reply_text(
        f"🌐 BAZRAGOD SOCIAL\n\n"
        f"Follow on every platform 🔥\n\n"
        f"+{pts} pts",
        reply_markup=keyboard,
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 20 — LOCATION INTELLIGENCE                    ║
# ╚══════════════════════════════════════════════════════════════╝

async def share_location_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup(
        [
            [KeyboardButton("📍 Send My Location", request_location=True)],
            ["🔙 Back to Menu"],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        f"📍 SHARE YOUR LOCATION\n\n"
        f"Put your city on the Parish 14 fan map.\n"
        f"Help plan shows near you.\n"
        f"Earn +{POINTS['share_location']} pts 🌍",
        reply_markup=kb,
    )


async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    loc  = update.message.location

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO fan_locations (telegram_id, latitude, longitude, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (telegram_id) DO UPDATE
            SET latitude   = EXCLUDED.latitude,
                longitude  = EXCLUDED.longitude,
                updated_at = NOW()
        """, (uid, loc.latitude, loc.longitude))
        conn.commit()
    finally:
        release_db(conn)

    pts = award_points(uid, "share_location", name)
    await update.message.reply_text(
        f"📍 Location recorded!\n\n"
        f"+{pts} pts — your city is on the map 🌍\n\n"
        f"BAZRAGOD sees where his army stands. 👑",
        reply_markup=main_menu,
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 13 — REFERRAL SYSTEM                          ║
# ╚══════════════════════════════════════════════════════════════╝

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT invites, tier FROM fans WHERE telegram_id = %s",
            (uid,),
        )
        row = cur.fetchone()
    finally:
        release_db(conn)

    invites = row[0] if row else 0
    tier    = row[1] if row else "🎧 Fan"

    tiers_text = "\n".join(
        [f"  {v} — {k} invites" for k, v in REFERRAL_TIERS.items()]
    )

    await update.message.reply_text(
        f"👥 REFERRAL SYSTEM\n"
        f"{'═' * 22}\n\n"
        f"Your link:\n{link}\n\n"
        f"Invites: {invites}\n"
        f"Tier:    {tier}\n\n"
        f"Tier Rewards:\n{tiers_text}\n\n"
        f"Every invite = +{POINTS['invite_friend']} pts 🔥\n"
        f"Build the Parish 14 army. 👑"
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 22 — AI ASSISTANT (MAXIMUS)                   ║
# ╚══════════════════════════════════════════════════════════════╝

async def ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not openai_client:
        await update.message.reply_text(
            "🤖 MAXIMUS is offline.\nOPENAI_API_KEY not configured."
        )
        return

    uid  = update.effective_user.id
    name = get_username(update)

    context.user_data["ai_active"]  = True
    context.user_data["ai_history"] = context.user_data.get("ai_history", [])

    pts = award_points(uid, "ai_chat", name)
    await update.message.reply_text(
        f"🤖 MAXIMUS ONLINE\n"
        f"{'═' * 22}\n\n"
        f"Royal AI of BAZRAGOD.\n"
        f"Manager. Publicist. Radio DJ. Strategist.\n\n"
        f"Ask me anything.\n"
        f"Type /menu to return to main menu.\n\n"
        f"+{pts} pts"
    )


async def ai_chat_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    if not context.user_data.get("ai_active"):
        return False
    if not openai_client:
        return False

    uid      = update.effective_user.id
    name     = get_username(update)
    user_msg = update.message.text

    history = context.user_data.get("ai_history", [])
    history.append({"role": "user", "content": user_msg})
    if len(history) > 10:
        history = history[-10:]

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": AI_SYSTEM_PROMPT},
                *history,
            ],
            max_tokens=400,
        )
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        context.user_data["ai_history"] = history

        award_points(uid, "ai_chat", name)
        await update.message.reply_text(f"🤖 MAXIMUS\n\n{reply}")
        await maximus_speak(context, uid, reply)

    except Exception as e:
        await update.message.reply_text(f"🤖 MAXIMUS error: {str(e)}")

    return True

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE — WISDOM + FITNESS                            ║
# ╚══════════════════════════════════════════════════════════════╝

async def wisdom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    pts  = award_points(uid, "wisdom", name)
    await update.message.reply_text(
        f"👑 Royal Wisdom\n\n{random.choice(QUOTES)}\n\n+{pts} pts"
    )


async def fitness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    pts  = award_points(uid, "fitness", name)
    await update.message.reply_text(f"{FITNESS_MSG}\n\n+{pts} pts 💪")

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE 24 — ADMIN CONTROL PANEL                      ║
# ╚══════════════════════════════════════════════════════════════╝

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        "👑 I.A.A.I.M.O ADMIN PANEL\n"
        "═══════════════════════\n\n"
        "ANALYTICS\n"
        "/stats\n"
        "/radar\n\n"
        "CONTENT\n"
        "/list_songs  /delete_song <id>\n"
        "/list_beats  /delete_beat <id>\n"
        "/list_drops  /delete_drop <id>\n\n"
        "BROADCAST\n"
        "/broadcast\n"
        "/shoutout @username\n"
        "/announce <message>\n\n"
        "UPLOAD\n"
        "Send audio + caption:\n"
        "  #song / #beat / #drop"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM fans")
        total_fans = cur.fetchone()[0]
        cur.execute("SELECT SUM(points) FROM fans")
        total_pts = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM songs")
        total_songs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM beats")
        total_beats = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM drops")
        total_drops = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fan_locations")
        mapped = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM purchases WHERE status = 'pending'")
        pending = cur.fetchone()[0]
        cur.execute(
            "SELECT username, points FROM fans ORDER BY points DESC LIMIT 1"
        )
        top = cur.fetchone()
    finally:
        release_db(conn)

    top_fan = f"@{top[0]} ({top[1]} pts)" if top else "None"
    await update.message.reply_text(
        f"📊 MISERBOT STATS\n"
        f"{'═' * 22}\n"
        f"👥 Fans:           {total_fans}\n"
        f"⭐ Points Given:   {total_pts}\n"
        f"🎵 Songs:          {total_songs}\n"
        f"🥁 Beats:          {total_beats}\n"
        f"🎤 Drops:          {total_drops}\n"
        f"📍 Fans Mapped:    {mapped}\n"
        f"🛒 Pending Orders: {pending}\n"
        f"🏆 Top Fan:        {top_fan}\n"
        f"{'═' * 22}"
    )


async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT COALESCE(country, 'Unknown'), COUNT(*) as fans
            FROM fan_locations
            GROUP BY country
            ORDER BY fans DESC
            LIMIT 15
        """)
        rows = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM fan_locations")
        total = cur.fetchone()[0]
    finally:
        release_db(conn)

    if not rows:
        await update.message.reply_text("No fan locations recorded yet.")
        return

    text = (
        f"🗺 TOUR INTELLIGENCE RADAR\n"
        f"{'═' * 22}\n"
        f"Total fans mapped: {total}\n\n"
    )
    for country, fans in rows:
        text += f"📍 {country} — {fans} fans\n"

    await update.message.reply_text(text)


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    pending_broadcasts[ADMIN_ID] = True
    await update.message.reply_text(
        "📢 BROADCAST MODE\n\n"
        "Send your message now.\n"
        "Goes to all fans.\n\n"
        "/cancel to abort."
    )


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_broadcasts.pop(update.effective_user.id, None)
    context.user_data["ai_active"] = False
    await update.message.reply_text("Cancelled.", reply_markup=main_menu)


async def shoutout_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /shoutout @username")
        return
    msg  = (
        f"🔥 SHOUTOUT FROM BAZRAGOD\n\n"
        f"Big up {args[0]} — real Parish 14 energy! 👑\n\n"
        f"I.A.A.I.M.O"
    )
    sent = await _broadcast_to_all(context, msg, speak=True)
    await update.message.reply_text(f"Shoutout sent to {sent} fans.")


async def announce_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /announce <message>")
        return
    msg  = f"📢 OFFICIAL ANNOUNCEMENT\n\n{text}\n\n— BAZRAGOD"
    sent = await _broadcast_to_all(context, msg, speak=True)
    await update.message.reply_text(f"Announcement sent to {sent} fans.")


async def _broadcast_to_all(
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    speak: bool = False,
) -> int:
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT telegram_id FROM fans")
        fans = cur.fetchall()
    finally:
        release_db(conn)

    sent = 0
    for (fan_id,) in fans:
        try:
            await context.bot.send_message(fan_id, text)
            if speak:
                await maximus_speak(context, fan_id, text)
            sent += 1
        except Exception:
            pass
    return sent

# ╔══════════════════════════════════════════════════════════════╗
# ║         MODULE — ADMIN UPLOAD HANDLER                        ║
# ╚══════════════════════════════════════════════════════════════╝

async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID and pending_broadcasts.get(ADMIN_ID) and update.message.text:
        pending_broadcasts.pop(ADMIN_ID)
        sent = await _broadcast_to_all(context, update.message.text)
        await update.message.reply_text(f"📢 Broadcast sent to {sent} fans.")
        return

    if not is_admin(uid):
        return

    audio = update.message.audio
    if not audio:
        return

    caption = (update.message.caption or "").strip().lower()
    title   = audio.title or "Untitled"
    file_id = audio.file_id

    conn = get_db()
    cur  = conn.cursor()
    try:
        if "#beat" in caption:
            cur.execute(
                "INSERT INTO beats (title, file_id) VALUES (%s, %s) RETURNING id",
                (title, file_id),
            )
            table = "beats 🥁"
        elif "#drop" in caption:
            cur.execute(
                "INSERT INTO drops (title, file_id) VALUES (%s, %s) RETURNING id",
                (title, file_id),
            )
            table = "drops 🎤"
        else:
            cur.execute(
                "INSERT INTO songs (title, file_id) VALUES (%s, %s) RETURNING id",
                (title, file_id),
            )
            table = "songs 🎵"

        new_id = cur.fetchone()[0]
        conn.commit()
    finally:
        release_db(conn)

    await update.message.reply_text(
        f"✅ Added to {table}\n\nID: {new_id}\nTitle: {title}"
    )


async def list_songs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await _list_table(update, "songs", "🎵 SONGS")

async def list_beats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await _list_table(update, "beats", "🥁 BEATS")

async def list_drops_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await _list_table(update, "drops", "🎤 DROPS")

async def _list_table(update, table, label):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(f"SELECT id, title FROM {table} ORDER BY id")
        rows = cur.fetchall()
    finally:
        release_db(conn)

    text = f"{label}\n{'═' * 18}\n\n"
    for r in rows:
        text += f"[{r[0]}] {r[1]}\n"
    await update.message.reply_text(text or "Empty.")

async def delete_song_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await _delete_from(update, context, "songs")

async def delete_beat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await _delete_from(update, context, "beats")

async def delete_drop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await _delete_from(update, context, "drops")

async def _delete_from(update, context, table):
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(f"Usage: /delete_{table[:-1]} <id>")
        return
    row_id = int(args[0])
    conn   = get_db()
    cur    = conn.cursor()
    try:
        cur.execute(
            f"DELETE FROM {table} WHERE id = %s RETURNING title",
            (row_id,),
        )
        row = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)

    if row:
        await update.message.reply_text(f"🗑 Deleted from {table}: {row[0]}")
    else:
        await update.message.reply_text("Not found.")

# ╔══════════════════════════════════════════════════════════════╗
# ║         MENU COMMAND                                         ║
# ╚══════════════════════════════════════════════════════════════╝

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ai_active"]  = False
    context.user_data["ai_history"] = []
    await update.message.reply_text("👑 Main Menu", reply_markup=main_menu)

# ╔══════════════════════════════════════════════════════════════╗
# ║         ROUTER (FIX 8 — REGISTERED LAST)                    ║
# ╚══════════════════════════════════════════════════════════════╝

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid  = update.effective_user.id

    if context.user_data.get("ai_active"):
        handled = await ai_chat_handler(update, context)
        if handled:
            return

    if uid == ADMIN_ID and pending_broadcasts.get(ADMIN_ID):
        pending_broadcasts.pop(ADMIN_ID)
        sent = await _broadcast_to_all(context, text)
        await update.message.reply_text(f"📢 Broadcast sent to {sent} fans.")
        return

    routes = {
        "🎵 Music":           music,
        "📻 Radio":            radio,
        "🥁 Beats":            beats,
        "🎤 Drops":            drops_menu,
        "🏆 Leaderboard":     leaderboard,
        "⭐ My Points":       my_points,
        "👤 My Profile":      my_profile,
        "🎯 Daily Mission":   daily_mission,
        "💰 Support Artist":  support,
        "🌐 Social":          social,
        "🛒 Music Store":     music_store,
        "👕 Parish 14 Merch": merch,
        "👑 Wisdom":          wisdom,
        "🏋 Fitness":         fitness,
        "📍 Share Location":  share_location_prompt,
        "👥 Refer a Friend":  refer,
        "🤖 AI Assistant":    ai_assistant,
        "🔙 Back to Menu":    menu_cmd,
    }

    handler = routes.get(text)
    if handler:
        await handler(update, context)

# ╔══════════════════════════════════════════════════════════════╗
# ║    TELEGRAM APP ASSEMBLY (FIX 8 — CORRECT HANDLER ORDER)    ║
# ╚══════════════════════════════════════════════════════════════╝

telegram_app = Application.builder().token(BOT_TOKEN).build()

# Commands
telegram_app.add_handler(CommandHandler("start",       start))
telegram_app.add_handler(CommandHandler("menu",        menu_cmd))
telegram_app.add_handler(CommandHandler("cancel",      cancel_cmd))
telegram_app.add_handler(CommandHandler("admin",       admin_panel))
telegram_app.add_handler(CommandHandler("stats",       stats))
telegram_app.add_handler(CommandHandler("radar",       radar))
telegram_app.add_handler(CommandHandler("broadcast",   broadcast_cmd))
telegram_app.add_handler(CommandHandler("shoutout",    shoutout_cmd))
telegram_app.add_handler(CommandHandler("announce",    announce_cmd))
telegram_app.add_handler(CommandHandler("list_songs",  list_songs_cmd))
telegram_app.add_handler(CommandHandler("list_beats",  list_beats_cmd))
telegram_app.add_handler(CommandHandler("list_drops",  list_drops_cmd))
telegram_app.add_handler(CommandHandler("delete_song", delete_song_cmd))
telegram_app.add_handler(CommandHandler("delete_beat", delete_beat_cmd))
telegram_app.add_handler(CommandHandler("delete_drop", delete_drop_cmd))

# Callbacks — specific patterns first
telegram_app.add_handler(CallbackQueryHandler(intro_cb,           pattern="^intro:"))
telegram_app.add_handler(CallbackQueryHandler(mission_complete_cb,pattern="^mission:"))
telegram_app.add_handler(CallbackQueryHandler(store_cb,           pattern="^store:"))
telegram_app.add_handler(CallbackQueryHandler(merch_cb,           pattern="^merch:"))
telegram_app.add_handler(CallbackQueryHandler(play_song_cb,       pattern="^song:"))
telegram_app.add_handler(CallbackQueryHandler(play_beat_cb,       pattern="^beat:"))
telegram_app.add_handler(CallbackQueryHandler(play_drop_cb,       pattern="^drop:"))

# Media and location
telegram_app.add_handler(MessageHandler(filters.LOCATION, location_handler))
telegram_app.add_handler(MessageHandler(filters.AUDIO,    upload_handler))

# Text router — always last
telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, router)
)

# ╔══════════════════════════════════════════════════════════════╗
# ║         ASYNC LOOP (FIX 9)                                   ║
# ╚══════════════════════════════════════════════════════════════╝

telegram_loop = asyncio.new_event_loop()

def start_telegram():
    asyncio.set_event_loop(telegram_loop)
    telegram_loop.run_until_complete(telegram_app.initialize())
    telegram_loop.run_until_complete(telegram_app.start())
    telegram_loop.run_forever()

threading.Thread(target=start_telegram, daemon=True).start()

# ╔══════════════════════════════════════════════════════════════╗
# ║         WEBHOOK (FIX 9)                                      ║
# ╚══════════════════════════════════════════════════════════════╝

@flask_app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    data   = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    asyncio.run_coroutine_threadsafe(
        telegram_app.process_update(update),
        telegram_loop,
    )
    return "ok"

@flask_app.route("/health")
def health():
    return "I.A.A.I.M.O ONLINE — PARISH 14 NATION", 200

# ╔══════════════════════════════════════════════════════════════╗
# ║         MAIN (FIX 10 — CORRECT BOOT ORDER)                   ║
# ╚══════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    init_pool()
    init_db()
    print("╔══════════════════════════════════════╗")
    print("║   I.A.A.I.M.O — MISERBOT v5000      ║")
    print("║   Owner:   BAZRAGOD                  ║")
    print("║   Nation:  Parish 14                 ║")
    print("║   Status:  ONLINE                    ║")
    print("╚══════════════════════════════════════╝")
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
