"""
╔══════════════════════════════════════════════════════════════╗
║         I.A.A.I.M.O — MASTER SYSTEM v10.000                 ║
║  Independent Artists Artificial Intelligence Music Ops       ║
║  Bot:     Miserbot                                           ║
║  Owner:   BAZRAGOD                                           ║
║  Nation:  Parish 14                                          ║
║  Mission: World's First AI Artist Radio Station              ║
║                                                              ║
║  NEW IN v10.000:                                             ║
║  🎙️ 4 AI DJ Personalities (time-based rotation)             ║
║  🔥 Song Heat + Play Counter System                          ║
║  ❤️  Fan Like + Donate Buttons                               ║
║  📊 Top Charts (plays + likes ranked)                        ║
║  💎 $19.99 Monthly Supporter Tier                            ║
║  📺 YouTube Link Detection + Auto-Announce                   ║
║  🎚️ Smart Audio Upload Classification                        ║
║  🌐 Updated Socials (Snapchat + Twitch + Spotify)            ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import re
import time
import random
import asyncio
import threading
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

# ╔══════════════════════════════════════════════════════════════╗
# ║                        CONFIG                                ║
# ╚══════════════════════════════════════════════════════════════╝

BOT_TOKEN      = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL   = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OWNER_ID       = int(os.environ.get("OWNER_ID", "8741545426"))
BOT_USERNAME   = "miserbot"
WEBHOOK_PATH   = "/webhook"

INTRO_FILE_ID = os.environ.get(
    "INTRO_FILE_ID",
    "CQACAgEAAxkBAAICN2nUZHzzXlQszP-a08nJiSctUeOhAAL-BQACEbKpRg3vpxJvYve3OwQ",
)

BOOKING_EMAIL = "Miserbot.ai@gmail.com"
CASHAPP       = "https://cash.app/$BAZRAGOD"
PAYPAL        = "https://paypal.me/bazragod1"

SOCIALS = {
    "📸 Instagram": "https://www.instagram.com/bazragod_timeless",
    "🎵 TikTok":    "https://www.tiktok.com/@bazragod_official",
    "▶️ YouTube":   "https://youtube.com/@bazragodmusictravelandleis8835",
    "🐦 X":         "https://x.com/toligarch65693",
    "👻 Snapchat":  "https://snapchat.com/t/L7djDwfj",
    "🎮 Twitch":    "https://twitch.tv/bazra14",
    "🎧 Spotify":   "https://open.spotify.com/artist/2IwaaLobpi2NSGD3B5xapK",
}

SUPPORTER_PRICE = 19.99

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
app           = Flask(__name__)

# ╔══════════════════════════════════════════════════════════════╗
# ║                  CONNECTION POOL                             ║
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
# ║              🎙️ DJ PERSONALITY SYSTEM                        ║
# ╚══════════════════════════════════════════════════════════════╝

DJS = {
    "aurora": {
        "name":    "DJ Aurora",
        "emoji":   "🌅",
        "hours":   range(5, 12),
        "style":   (
            "You are DJ Aurora, morning energy host of BazraGod Radio. "
            "Style: uplifting, motivational, sunrise vibes, energetic. "
            "You set the tone for the day. Jamaican warmth meets morning power. "
            "Keep commentary under 2 sentences. End with energy."
        ),
        "intros": [
            "Good morning Parish 14. DJ Aurora on the frequency. Let's rise.",
            "The sun is up. The music is live. DJ Aurora bringing the morning fire.",
            "Rise and grind. BazraGod Radio morning session. DJ Aurora in control.",
        ],
    },
    "colorred": {
        "name":    "DJ Color Red",
        "emoji":   "🔴",
        "hours":   range(12, 18),
        "style":   (
            "You are DJ Color Red, afternoon hype host of BazraGod Radio. "
            "Style: high energy, hype, confident, street culture. "
            "You keep the midday crowd locked in. Raw and powerful. "
            "Keep commentary under 2 sentences. Maximum hype."
        ),
        "intros": [
            "Afternoon session live. DJ Color Red on the dial. Turn it up.",
            "Midday heat. BazraGod Radio. DJ Color Red taking no prisoners.",
            "Color Red in the building. Parish 14 afternoon session. Let's go.",
        ],
    },
    "maximus": {
        "name":    "DJ Maximus",
        "emoji":   "👑",
        "hours":   range(18, 24),
        "style":   (
            "You are DJ Maximus, prime time commander of BazraGod Radio. "
            "Style: sovereign, deep, authoritative, luxury. "
            "Prime time belongs to BAZRAGOD. You control the night. "
            "Keep commentary under 2 sentences. Royal authority."
        ),
        "intros": [
            "Prime time. DJ Maximus commanding the airwaves. Parish 14 Nation.",
            "The sovereign hour begins. DJ Maximus. BazraGod Radio prime time.",
            "Night belongs to us. DJ Maximus live. I.A.A.I.M.O.",
        ],
    },
    "eclipse": {
        "name":    "DJ Eclipse",
        "emoji":   "🌑",
        "hours":   range(0, 5),
        "style":   (
            "You are DJ Eclipse, late night atmosphere host of BazraGod Radio. "
            "Style: deep, mysterious, cinematic, introspective. "
            "The late night thinkers and creators. Dark energy. "
            "Keep commentary under 2 sentences. Deep and atmospheric."
        ),
        "intros": [
            "Late night. DJ Eclipse in the dark. BazraGod Radio never sleeps.",
            "Past midnight. The real ones are awake. DJ Eclipse.",
            "Eclipse on the frequency. No sleep for the sovereign. Parish 14.",
        ],
    },
}

def get_current_dj() -> dict:
    hour = datetime.now().hour
    for key, dj in DJS.items():
        if hour in dj["hours"]:
            return dj
    return DJS["maximus"]

# ╔══════════════════════════════════════════════════════════════╗
# ║                🔥 HEAT LEVEL SYSTEM                          ║
# ╚══════════════════════════════════════════════════════════════╝

def get_heat(plays: int) -> str:
    if plays >= 500000: return "🔥🔥🔥🔥🔥"
    if plays >= 200000: return "🔥🔥🔥🔥"
    if plays >= 100000: return "🔥🔥🔥"
    if plays >= 50000:  return "🔥🔥"
    return "🔥"

# ╔══════════════════════════════════════════════════════════════╗
# ║                   POINTS + RANKS                             ║
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
    "mission":       100,
    "astro":         25,
    "cipher":        15,
    "mood_radio":    10,
    "voice_wall":    20,
    "like_song":      2,
    "supporter_sub": 50,
}

RANKS = [
    (0,    "🎧 Fan"),
    (100,  "⚔️  Supporter"),
    (500,  "🎖  Recruiter"),
    (1000, "🏅  Commander"),
    (2500, "👑  General"),
    (5000, "🌍  Nation Elite"),
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
# ║                  STORE + MERCH                               ║
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
# ║                  RADIO ENGINE                                ║
# ╚══════════════════════════════════════════════════════════════╝

RADIO_CYCLE    = [
    "song", "song", "dj_commentary", "beat",
    "song", "station_id", "promo", "song",
    "voice", "song", "dj_reaction",
]
radio_position  = 0
radio_song_pool = []  # tracks played to avoid repeats

RADIO_PROMOS = [
    "Support independent music. Hit the Support button.",
    "Parish 14 merch available now. Rep the nation.",
    "Invite your friends. Parish 14 grows stronger every day.",
    "Share your location. Put your city on the fan map.",
    "I.A.A.I.M.O — no label, no middleman, just BAZRAGOD.",
    "Book BAZRAGOD for your event. Contact Miserbot.ai@gmail.com",
    "Climb the leaderboard. Earn your rank. Parish 14 Nation.",
    "Drop your verse in the Lyric Cipher. Challenge MAXIMUS.",
    "Try Mood Radio. Let MAXIMUS select your perfect track.",
    "Become a Parish 14 Supporter for $19.99 a month. Tap 💎 Supporter.",
    "Stream BAZRAGOD on Spotify. Search BAZRAGOD.",
    "Follow on all socials. Instagram TikTok YouTube X Snapchat Twitch.",
]

STATION_IDS = [
    "BazraGod Radio. Parish 14 Nation. Independent music lives here.",
    "You are tuned in to BazraGod Radio. I.A.A.I.M.O. No label. No limit.",
    "This is BazraGod Radio. The sovereign station. Parish 14 worldwide.",
    "BazraGod Radio. Where the real ones listen. All day. Every day.",
    "I.A.A.I.M.O Radio. Independent Artists. Artificial Intelligence. Music Operations.",
]

# ╔══════════════════════════════════════════════════════════════╗
# ║                  DAILY MISSIONS                              ║
# ╚══════════════════════════════════════════════════════════════╝

MISSIONS = [
    "Listen to 1 song from the catalog",
    "Press 📻 BazraGod Radio and let it play",
    "Invite 1 friend using your referral link",
    "Share your location to put your city on the map",
    "Follow BAZRAGOD on all social platforms",
    "Check the leaderboard and see your rank",
    "Send a message to MAXIMUS AI",
    "Support the artist via CashApp or PayPal",
    "Try the 🧠 Mood Radio feature",
    "Drop a verse in the ⚔️ Lyric Cipher",
    "Submit a voice shoutout to the 🎙️ Voice Wall",
    "Like a song from the catalog",
    "Check the 📊 Top Charts",
]

# ╔══════════════════════════════════════════════════════════════╗
# ║                  SEED CATALOG                                ║
# ╚══════════════════════════════════════════════════════════════╝

SEED_SONGS = [
    ("Boom Boom",            "CQACAgEAAxkBAAO7adMau7f0mxOIRUMGuVGTePgfMXEAAvsIAAI1Z5hG7XiUWc51fmc7BA"),
    ("MINI 14",              "CQACAgEAAxkBAAO5adMaRT8drrNsgm0xoFaanGe0cVUAAvoIAAI1Z5hGOQE82sZNKSg7BA"),
    ("GUNMAN",               "CQACAgEAAxkBAAPLadMfFX9ypdz5SZrFYwY5PDfbXHEAAggJAAI1Z5hGsWl0k2b4TF47BA"),
    ("TRAPP MASTER",         "CQACAgEAAxkBAAPHadMd18aXn3dTuM6O6-V-VAwGUgkAAgUJAAI1Z5hGFs9yDalWXC87BA"),
    ("FEAR",                 "CQACAgEAAxkBAAPTadMhUx8wc0RTafeXlg63snEcu7sAAgwJAAI1Z5hG5VCl-ykMd8I7BA"),
    ("SUMMERTIME",           "CQACAgEAAxkBAAO_adMcA4iZQx8ReZ7_8PQkFbNHSfIAAv0IAAI1Z5hGP-dTmMrxas47BA"),
    ("REAL GOLD",            "CQACAgEAAxkBAAO9adMbBDzajJrOcGNb6gVyZmjEXTYAAvwIAAI1Z5hGr3nvGz4AAYjbOwQ"),
    ("FACEBOOK LUST",        "CQACAgEAAxkBAAOzadMY-pj_rWBB5wrRP6Nfymv4q6EAAvcIAAI1Z5hG4SGuftZqhPY7BA"),
    ("MI ALONE",             "CQACAgEAAxkBAAPJadMeaMExYAvnDv8gswXyUgOMwpsAAgcJAAI1Z5hGxeKB46IBYZg7BA"),
    ("BUBBLE FI MI",         "CQACAgEAAxkBAAPPadMgBMh10TStncJQXpkyD0mJYM8AAgoJAAI1Z5hG10QJbSDmTyM7BA"),
    ("NATURAL PUSSY",        "CQACAgEAAxkBAAO1adMZtjgiRqYxrOFbE3KOCNxVcxQAAvgIAAI1Z5hGm8QmWqNIojg7BA"),
    ("FRAID AH YUH",         "CQACAgEAAxkBAAO3adMZ_P5y2OoXlyY0XpO_fiPiahMAAvkIAAI1Z5hGgMZ1tOmyhjA7BA"),
    ("CARRY GUH BRING COME", "CQACAgEAAxkBAAPFadMdgVBA0MIwyLNyU8mO5-djfawAAgQJAAI1Z5hGYmzehzRMIZY7BA"),
    ("IMPECCABLE",           "CQACAgEAAxkBAAPRadMgsX9xJh3boHp64jA1-sVPC80AAgsJAAI1Z5hGIlCi8cg5E_k7BA"),
    ("BIG FAT MATIC",        "CQACAgEAAxkBAAPNadMfiOZJNeE3Eihp-r-olvpfzWIAAgkJAAI1Z5hGaNvyiVRhwEw7BA"),
]

QUOTES = [
    "Discipline equals freedom.",
    "Move in silence. Only speak when it's time to say checkmate.",
    "Kings are built through struggle.",
    "He who conquers himself is the mightiest warrior.",
    "Never outshine the master.",
    "Appear weak when you are strong.",
    "The obstacle is the way.",
    "A lion does not concern himself with the opinions of sheep.",
    "Kings are not born — they are made through discipline.",
    "Do not pray for an easy life. Pray for the strength to endure a difficult one.",
    "The successful warrior is the average man with laser-like focus.",
    "What you seek is seeking you.",
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

BAZRAGOD is fully independent — no label, no middleman.
Platform lives inside Telegram. Catalog: 15 tracks. Nation: Parish 14.

Keep responses concise for Telegram — max 3 paragraphs.
End every response with a power statement."""

# ╔══════════════════════════════════════════════════════════════╗
# ║                  SESSION STATES                              ║
# ╚══════════════════════════════════════════════════════════════╝

pending_broadcasts:  dict = {}
astro_sessions:      dict = {}
mood_sessions:       dict = {}
cipher_sessions:     dict = {}
upload_sessions:     dict = {}  # tracks admin upload classification

# ╔══════════════════════════════════════════════════════════════╗
# ║                     DATABASE                                 ║
# ╚══════════════════════════════════════════════════════════════╝

def init_db():
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fans (
                telegram_id     BIGINT PRIMARY KEY,
                username        TEXT,
                points          INT DEFAULT 0,
                invites         INT DEFAULT 0,
                referrer_id     BIGINT,
                tier            TEXT DEFAULT '🎧 Fan',
                city            TEXT,
                country         TEXT,
                is_supporter    BOOLEAN DEFAULT FALSE,
                prophecy_tiers  TEXT DEFAULT '',
                joined_at       TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("ALTER TABLE fans ADD COLUMN IF NOT EXISTS prophecy_tiers TEXT DEFAULT ''")
        cur.execute("ALTER TABLE fans ADD COLUMN IF NOT EXISTS is_supporter BOOLEAN DEFAULT FALSE")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id          SERIAL PRIMARY KEY,
                title       TEXT,
                file_id     TEXT,
                plays       INTEGER DEFAULT 30000,
                likes       INTEGER DEFAULT 0,
                uploaded_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("ALTER TABLE songs ADD COLUMN IF NOT EXISTS plays INTEGER DEFAULT 30000")
        cur.execute("ALTER TABLE songs ADD COLUMN IF NOT EXISTS likes INTEGER DEFAULT 0")

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
                price        FLOAT,
                status       TEXT DEFAULT 'pending',
                purchased_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS astro_profiles (
                telegram_id  BIGINT PRIMARY KEY,
                birth_date   TEXT,
                birth_time   TEXT,
                birth_city   TEXT,
                current_city TEXT,
                last_reading TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS voice_wall (
                id           SERIAL PRIMARY KEY,
                telegram_id  BIGINT,
                username     TEXT,
                file_id      TEXT,
                status       TEXT DEFAULT 'pending',
                submitted_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS song_likes (
                telegram_id BIGINT,
                song_id     INT,
                PRIMARY KEY (telegram_id, song_id)
            )
        """)

        # Seed songs
        cur.execute("SELECT COUNT(*) FROM songs")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO songs (title, file_id) VALUES (%s, %s)",
                SEED_SONGS,
            )

        conn.commit()
        print("I.A.A.I.M.O DATABASE READY — v10.000")
    finally:
        release_db(conn)

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
        cur.execute("SELECT points FROM fans WHERE telegram_id = %s", (telegram_id,))
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
        cur.execute("SELECT telegram_id FROM fans WHERE telegram_id = %s", (telegram_id,))
        if cur.fetchone():
            return False
        cur.execute("""
            INSERT INTO fans (telegram_id, username, referrer_id)
            VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
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
        ["🎧 BAZRAGOD MUSIC",  "📻 BazraGod Radio"],
        ["🧠 Mood Radio",      "⚔️ Lyric Cipher"],
        ["📊 Top Charts",      "💎 Supporter"],
        ["🥁 Beats",           "🎤 Drops"],
        ["🏆 Leaderboard",     "⭐ My Points"],
        ["👤 My Profile",      "🎯 Daily Mission"],
        ["💰 Support Artist",  "🌐 Social"],
        ["🛒 Music Store",     "👕 Parish 14"],
        ["👑 Wisdom",          "🏋 Fitness"],
        ["📍 Share Location",  "👥 Refer a Friend"],
        ["📡 Fan Radar",       "📅 Booking"],
        ["🎙️ Voice Wall",      "🪐 Astro Reading"],
        ["🤖 MAXIMUS AI"],
    ],
    resize_keyboard=True,
)

def get_username(update: Update) -> str:
    u = update.effective_user
    return u.username or u.first_name or str(u.id)

def is_admin(uid: int) -> bool:
    return uid == OWNER_ID

# ╔══════════════════════════════════════════════════════════════╗
# ║                  MAXIMUS VOICE ENGINE                        ║
# ╚══════════════════════════════════════════════════════════════╝

async def maximus_speak(context, chat_id: int, text: str):
    if not openai_client:
        return
    try:
        response   = openai_client.audio.speech.create(
            model="tts-1", voice="onyx",
            input=text[:500], speed=0.95,
        )
        audio_file = BytesIO(response.content)
        audio_file.name = "maximus.ogg"
        await context.bot.send_voice(chat_id=chat_id, voice=audio_file)
    except Exception as e:
        print(f"Voice error: {e}")


async def maximus_speak_direct(bot, chat_id: int, text: str):
    if not openai_client:
        return
    try:
        response   = openai_client.audio.speech.create(
            model="tts-1", voice="onyx",
            input=text[:500], speed=0.95,
        )
        audio_file = BytesIO(response.content)
        audio_file.name = "maximus.ogg"
        await bot.send_voice(chat_id=chat_id, voice=audio_file)
    except Exception as e:
        print(f"Voice direct error: {e}")


async def dj_speak(context, chat_id: int, text: str, dj: dict):
    """Generate DJ voice — uses onyx voice for all DJs."""
    if not openai_client:
        return
    try:
        response   = openai_client.audio.speech.create(
            model="tts-1", voice="onyx",
            input=text[:500], speed=0.92,
        )
        audio_file = BytesIO(response.content)
        audio_file.name = "dj.ogg"
        await context.bot.send_voice(chat_id=chat_id, voice=audio_file)
    except Exception as e:
        print(f"DJ voice error: {e}")


async def generate_dj_line(dj: dict, song_title: str = None, action: str = "intro") -> str:
    if not openai_client:
        return random.choice(dj["intros"])
    try:
        if action == "commentary" and song_title:
            user_prompt = (
                f"Give a 1-2 sentence DJ commentary about the song '{song_title}' "
                f"by BAZRAGOD that just played."
            )
        elif action == "reaction" and song_title:
            user_prompt = (
                f"Give a 1 sentence hot reaction to the track '{song_title}' by BAZRAGOD."
            )
        elif action == "intro" and song_title:
            user_prompt = (
                f"Introduce the next track '{song_title}' by BAZRAGOD in 1-2 sentences."
            )
        else:
            return random.choice(dj["intros"])

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": dj["style"]},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=80,
        )
        return response.choices[0].message.content
    except Exception:
        return random.choice(dj["intros"])

# ╔══════════════════════════════════════════════════════════════╗
# ║              🔮 SOVEREIGN PROPHECY ENGINE                    ║
# ╚══════════════════════════════════════════════════════════════╝

async def maybe_prophecy(uid: int, username: str, context):
    if not openai_client:
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT points, tier, prophecy_tiers FROM fans WHERE telegram_id = %s",
            (uid,),
        )
        row = cur.fetchone()
        if not row:
            return
        points, tier, sent_tiers = row
        sent_tiers = sent_tiers or ""
        if tier == "🎧 Fan" or tier in sent_tiers:
            return
        cur.execute(
            "UPDATE fans SET prophecy_tiers = prophecy_tiers || %s WHERE telegram_id = %s",
            (f"{tier}|", uid),
        )
        conn.commit()
    finally:
        release_db(conn)

    try:
        name_display = f"@{username}" if username else "soldier"
        prompt = (
            f"Fan: {name_display}\nRank achieved: {tier}\nPoints: {points}\n\n"
            f"Write a personal sovereign prophecy for this fan who just reached {tier} "
            f"in BAZRAGOD's I.A.A.I.M.O platform. 4 sentences max. "
            f"Make them feel chosen. End with their rank title in capitals."
        )
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": AI_SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=200,
        )
        prophecy = response.choices[0].message.content
        await context.bot.send_message(
            uid,
            f"🔮 SOVEREIGN PROPHECY\n\nBAZRAGOD sees you.\n\n{prophecy}\n\nRank: {tier} 👑",
        )
        await maximus_speak(context, uid, prophecy)
    except Exception as e:
        print(f"Prophecy error: {e}")

# ╔══════════════════════════════════════════════════════════════╗
# ║                  UFO LAUNCH + INTRO                          ║
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
                f"👥 New soldier joined your link!\n"
                f"+{POINTS['invite_friend']} points credited 🔥",
            )
            award_points(referrer, "invite_friend")
        except Exception:
            pass

    ufo = (
        "⠀⠀⠀✦⠀⠀⠀⠀✦⠀⠀⠀⠀⠀✦\n"
        "⠀⠀⠀⠀⠀⠀🛸⠀⠀⠀⠀⠀⠀\n"
        "⠀⠀✦⠀⠀⠀⠀⠀⠀⠀✦⠀⠀\n\n"
        "▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄\n"
        "  B A Z R A G O D\n"
        "  I . A . A . I . M . O\n"
        "  PARISH 14 COMMAND\n"
        "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀\n\n"
        "Initiating entry sequence... 🛸"
    )
    await update.message.reply_text(ufo)

    if INTRO_FILE_ID:
        await update.message.reply_text(
            "👑 Before you enter —\n\nPress play. Real fans only. 🎙️"
        )
        await update.message.reply_voice(
            INTRO_FILE_ID,
            caption="🎙️ BAZRAGOD — The Vision\nI.A.A.I.M.O",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("▶️  Enter The Platform", callback_data="intro:play")
            ]]),
        )
    else:
        await update.message.reply_text(
            f"🛸 WELCOME TO I.A.A.I.M.O\n\nParish 14 Nation\n\n+{pts} pts awarded 🔥",
            reply_markup=main_menu,
        )


async def intro_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT points, tier FROM fans WHERE telegram_id = %s", (uid,))
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
# ║                🎵 MUSIC CATALOG                              ║
# ╚══════════════════════════════════════════════════════════════╝

async def music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    award_points(uid, "play_song", name)

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, title, plays, likes FROM songs ORDER BY id")
        songs = cur.fetchall()
    finally:
        release_db(conn)

    if not songs:
        await update.message.reply_text("Catalog loading... check back soon.")
        return

    keyboard = [
        [InlineKeyboardButton(
            f"▶  {s[1]}  {get_heat(s[2])}",
            callback_data=f"song:{s[0]}"
        )]
        for s in songs
    ]
    await update.message.reply_text(
        f"🎧 BAZRAGOD CATALOG\n"
        f"Parish 14 Nation — {len(songs)} tracks\n\n"
        f"Select a track 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def play_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        song_id = int(query.data.split(":")[1])
    except Exception:
        return

    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT title, file_id, plays, likes FROM songs WHERE id = %s", (song_id,))
        song = cur.fetchone()
        if song:
            cur.execute("UPDATE songs SET plays = plays + 1 WHERE id = %s", (song_id,))
            conn.commit()
    finally:
        release_db(conn)

    if song:
        title, file_id, plays, likes = song
        plays += 1
        heat  = get_heat(plays)
        pts   = award_points(uid, "play_song", name)
        dj    = get_current_dj()
        line  = await generate_dj_line(dj, title, "intro")

        await dj_speak(context, uid, line, dj)
        await query.message.reply_audio(
            file_id,
            caption=(
                f"🎵 {title}\nBAZRAGOD\n\n"
                f"{heat} {plays:,} plays  ❤️ {likes}\n\n"
                f"+{pts} pts 🏆"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❤️ Like", callback_data=f"like:{song_id}"),
                InlineKeyboardButton("💰 Donate", url=CASHAPP),
            ]]),
        )
        await maybe_prophecy(uid, name, context)

# ╔══════════════════════════════════════════════════════════════╗
# ║                ❤️ LIKE SYSTEM                                 ║
# ╚══════════════════════════════════════════════════════════════╝

async def like_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
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
            "INSERT INTO song_likes (telegram_id, song_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (uid, song_id),
        )
        if cur.rowcount > 0:
            cur.execute("UPDATE songs SET likes = likes + 1 WHERE id = %s", (song_id,))
            conn.commit()
            award_points(uid, "like_song", name)
            await query.answer("❤️ Liked! +2 pts", show_alert=False)
        else:
            await query.answer("Already liked 👑", show_alert=False)
    finally:
        release_db(conn)

# ╔══════════════════════════════════════════════════════════════╗
# ║                📊 TOP CHARTS SYSTEM                          ║
# ╚══════════════════════════════════════════════════════════════╝

async def top_charts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT title, plays, likes, (plays + likes * 10) as score
            FROM songs
            ORDER BY score DESC
            LIMIT 10
        """)
        songs = cur.fetchall()
    finally:
        release_db(conn)

    if not songs:
        await update.message.reply_text("No songs in the chart yet.")
        return

    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    text   = "📊 PARISH 14 TOP CHARTS\n\n"

    for i, (title, plays, likes, score) in enumerate(songs):
        heat = get_heat(plays)
        text += (
            f"{medals[i]} {title}\n"
            f"   {heat}  {plays:,} plays  ❤️ {likes}\n\n"
        )

    dj   = get_current_dj()
    text += f"\n{dj['emoji']} {dj['name']} presents the Parish 14 Charts 👑"
    await update.message.reply_text(text)

# ╔══════════════════════════════════════════════════════════════╗
# ║                💎 SUPPORTER TIER                             ║
# ╚══════════════════════════════════════════════════════════════╝

async def supporter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT is_supporter FROM fans WHERE telegram_id = %s", (uid,))
        row = cur.fetchone()
    finally:
        release_db(conn)

    is_sup = row[0] if row else False

    if is_sup:
        await update.message.reply_text(
            "💎 PARISH 14 SUPPORTER\n\n"
            "✅ You are an active Supporter!\n\n"
            "Your benefits:\n"
            "🌍 Nation Elite badge\n"
            "📻 Priority radio shoutouts\n"
            "🎧 Early access to new songs\n"
            "🎤 Exclusive drops\n"
            "👑 Leaderboard priority\n\n"
            "Thank you for funding the movement. 👑"
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 Pay via CashApp — $19.99/mo", url=CASHAPP)],
        [InlineKeyboardButton("💳 Pay via PayPal — $19.99/mo",  url=PAYPAL)],
        [InlineKeyboardButton("✅ I've Paid — Activate Me", callback_data="supporter:verify")],
    ])

    await update.message.reply_text(
        f"💎 PARISH 14 SUPPORTER\n\n"
        f"${SUPPORTER_PRICE}/month\n\n"
        f"Benefits:\n"
        f"🌍 Nation Elite badge\n"
        f"📻 Priority radio shoutouts\n"
        f"🎧 Early access to new songs\n"
        f"🎤 Exclusive drops\n"
        f"👑 Leaderboard priority\n\n"
        f"Pay then tap the button below 👇",
        reply_markup=keyboard,
    )


async def supporter_verify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name

    await query.message.reply_text(
        "💎 Payment submitted for review.\n\n"
        "Admin will verify and activate your Supporter status. 👑"
    )
    try:
        await context.bot.send_message(
            OWNER_ID,
            f"💎 SUPPORTER REQUEST\n\n"
            f"Fan: @{name} ({uid})\n\n"
            f"/activate_supporter {uid}",
        )
    except Exception:
        pass


async def activate_supporter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /activate_supporter <telegram_id>")
        return

    fan_id = int(args[0])
    conn   = get_db()
    cur    = conn.cursor()
    try:
        cur.execute(
            "UPDATE fans SET is_supporter = TRUE, tier = '🌍  Nation Elite' WHERE telegram_id = %s RETURNING username",
            (fan_id,),
        )
        row = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)

    if row:
        award_points(fan_id, "supporter_sub")
        await update.message.reply_text(f"✅ @{row[0]} activated as Parish 14 Supporter 💎")
        try:
            await context.bot.send_message(
                fan_id,
                "💎 PARISH 14 SUPPORTER ACTIVATED!\n\n"
                "Welcome to the inner circle.\n\n"
                "🌍 Nation Elite badge unlocked\n"
                "Your support funds the movement.\n\n"
                "BAZRAGOD sees you. 👑",
            )
        except Exception:
            pass
    else:
        await update.message.reply_text("Fan not found.")

# ╔══════════════════════════════════════════════════════════════╗
# ║                  BEATS LIBRARY                               ║
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
        cur.execute("SELECT title, file_id FROM beats WHERE id = %s", (beat_id,))
        beat = cur.fetchone()
    finally:
        release_db(conn)

    if beat:
        pts = award_points(uid, "play_beat", name)
        await query.message.reply_audio(beat[1], caption=f"🥁 {beat[0]}\n\n+{pts} pts")

# ╔══════════════════════════════════════════════════════════════╗
# ║                  RADIO DROPS                                 ║
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
        cur.execute("SELECT title, file_id FROM drops WHERE id = %s", (drop_id,))
        drop = cur.fetchone()
    finally:
        release_db(conn)

    if drop:
        await query.message.reply_audio(drop[1], caption=f"🎤 {drop[0]}")

# ╔══════════════════════════════════════════════════════════════╗
# ║           📻 RADIO ENGINE — FULL DJ SYSTEM                   ║
# ╚══════════════════════════════════════════════════════════════╝

async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global radio_position, radio_song_pool

    uid  = update.effective_user.id
    name = get_username(update)
    now  = datetime.now().strftime("%I:%M %p")
    pts  = award_points(uid, "radio", name)
    dj   = get_current_dj()

    slot = RADIO_CYCLE[radio_position % len(RADIO_CYCLE)]
    radio_position += 1

    # ── PROMO ──────────────────────────────────────────────────
    if slot == "promo":
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT text FROM radio_promos ORDER BY RANDOM() LIMIT 1")
            row = cur.fetchone()
        finally:
            release_db(conn)
        promo = row[0] if row else random.choice(RADIO_PROMOS)
        await dj_speak(context, uid, f"BazraGod Radio — {now}. {promo}", dj)
        await update.message.reply_text(
            f"📻 {dj['emoji']} {dj['name']} — {now}\n\n🎙️ {promo}\n\n+{pts} pts"
        )
        return

    # ── STATION ID ─────────────────────────────────────────────
    if slot == "station_id":
        sid = random.choice(STATION_IDS)
        await dj_speak(context, uid, sid, dj)
        await update.message.reply_text(
            f"📻 {dj['emoji']} BazraGod Radio — {now}\n\n{sid}\n\n+{pts} pts"
        )
        return

    # ── DJ COMMENTARY ──────────────────────────────────────────
    if slot == "dj_commentary":
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT title FROM songs ORDER BY plays DESC LIMIT 5")
            rows = cur.fetchall()
        finally:
            release_db(conn)
        recent_title = random.choice(rows)[0] if rows else "BAZRAGOD"
        line = await generate_dj_line(dj, recent_title, "commentary")
        await dj_speak(context, uid, line, dj)
        await update.message.reply_text(
            f"📻 {dj['emoji']} {dj['name']} — {now}\n\n💬 {line}\n\n+{pts} pts"
        )
        return

    # ── DJ REACTION ────────────────────────────────────────────
    if slot == "dj_reaction":
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT title FROM songs ORDER BY RANDOM() LIMIT 1")
            row = cur.fetchone()
        finally:
            release_db(conn)
        title = row[0] if row else "that last track"
        line  = await generate_dj_line(dj, title, "reaction")
        await dj_speak(context, uid, line, dj)
        await update.message.reply_text(
            f"📻 {dj['emoji']} {dj['name']} — {now}\n\n🔥 {line}\n\n+{pts} pts"
        )
        return

    # ── VOICE WALL ─────────────────────────────────────────────
    if slot == "voice":
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute(
                "SELECT username, file_id FROM voice_wall "
                "WHERE status = 'approved' ORDER BY RANDOM() LIMIT 1"
            )
            voice = cur.fetchone()
        finally:
            release_db(conn)
        if voice:
            intro = (
                f"BazraGod Radio — {now}. "
                f"Fan shoutout from {voice[0]}. "
                f"Parish 14 Nation. This is what real fans sound like."
            )
            await dj_speak(context, uid, intro, dj)
            await update.message.reply_voice(
                voice[1],
                caption=f"🎙️ Fan Shoutout — @{voice[0]}\n📻 {dj['emoji']} BazraGod Radio — {now}\n\n+{pts} pts",
            )
            return

    # ── DROP ───────────────────────────────────────────────────
    if slot == "drop":
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT title, file_id FROM drops ORDER BY RANDOM() LIMIT 1")
            item = cur.fetchone()
        finally:
            release_db(conn)
        if item:
            intro = f"BazraGod Radio — {now}. Special drop incoming. {item[0]}. Parish 14."
            await dj_speak(context, uid, intro, dj)
            await update.message.reply_audio(
                item[1],
                caption=f"📻 {dj['emoji']} BazraGod Radio — {now}\n\n🎤 DROP: {item[0]}\n\n+{pts} pts",
            )
            return

    # ── BEAT ───────────────────────────────────────────────────
    if slot == "beat":
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT title, file_id FROM beats ORDER BY RANDOM() LIMIT 1")
            item = cur.fetchone()
        finally:
            release_db(conn)
        if item:
            intro = f"BazraGod Radio. {now}. This beat is called {item[0]}. Feel it."
            await dj_speak(context, uid, intro, dj)
            await update.message.reply_audio(
                item[1],
                caption=f"📻 {dj['emoji']} BazraGod Radio — {now}\n\n🥁 BEAT: {item[0]}\n\n+{pts} pts",
            )
            return

    # ── DEFAULT: SONG ──────────────────────────────────────────
    conn = get_db()
    cur  = conn.cursor()
    try:
        # No-repeat cycle — reset when all songs played
        if not radio_song_pool:
            cur.execute("SELECT id FROM songs")
            all_ids = [r[0] for r in cur.fetchall()]
            random.shuffle(all_ids)
            radio_song_pool.extend(all_ids)

        song_id = radio_song_pool.pop(0)
        cur.execute("SELECT title, file_id, plays, likes FROM songs WHERE id = %s", (song_id,))
        song = cur.fetchone()
        if song:
            cur.execute("UPDATE songs SET plays = plays + 1 WHERE id = %s", (song_id,))
            conn.commit()
    finally:
        release_db(conn)

    if not song:
        await update.message.reply_text("Radio loading... no songs found.")
        return

    title, file_id, plays, likes = song
    plays += 1
    heat  = get_heat(plays)
    intro = await generate_dj_line(dj, title, "intro")

    await dj_speak(context, uid, intro, dj)
    await update.message.reply_audio(
        file_id,
        caption=(
            f"📻 {dj['emoji']} BazraGod Radio — {now}\n\n"
            f"🎵 {title}\n"
            f"{heat}  {plays:,} plays  ❤️ {likes}\n\n"
            f"+{pts} pts 🔥"
        ),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❤️ Like", callback_data=f"like:{song_id}"),
            InlineKeyboardButton("💰 Donate", url=CASHAPP),
        ]]),
    )
    await maybe_prophecy(uid, name, context)

# ╔══════════════════════════════════════════════════════════════╗
# ║         🧠 MOOD RADIO — ALIEN TECH #1                        ║
# ╚══════════════════════════════════════════════════════════════╝

async def mood_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mood_sessions[uid] = True
    await update.message.reply_text(
        "🧠 MOOD RADIO\n\n"
        "MAXIMUS reads your energy and selects\n"
        "the perfect BAZRAGOD track for your soul.\n\n"
        "How are you feeling right now?\n\n"
        "Examples:\n"
        "• motivated and on fire\n"
        "• sad and reflective\n"
        "• locked in and focused\n"
        "• celebrating a win\n\n"
        "Type your mood 👇"
    )


async def mood_radio_handler(
    uid: int, text: str, update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    if uid not in mood_sessions:
        return False

    mood_sessions.pop(uid)
    name = get_username(update)
    dj   = get_current_dj()

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, title FROM songs ORDER BY id")
        songs = cur.fetchall()
    finally:
        release_db(conn)

    if not songs:
        await update.message.reply_text("No songs available yet.")
        return True

    await update.message.reply_text(
        f"🧠 MAXIMUS is reading your energy...\n\nMood: {text}"
    )

    try:
        song_list = "\n".join([f"{s[0]}. {s[1]}" for s in songs])
        response  = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are MAXIMUS, music selector for BAZRAGOD. "
                        "Given a fan's mood and song catalog, select the best matching song. "
                        "Reply with ONLY the song ID number. Nothing else."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Fan mood: {text}\n\nCatalog:\n{song_list}\n\nReply with only the song ID number.",
                },
            ],
            max_tokens=5,
        )
        raw     = response.choices[0].message.content.strip()
        song_id = int("".join(filter(str.isdigit, raw)))

        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT title, file_id, plays, likes FROM songs WHERE id = %s", (song_id,))
            song = cur.fetchone()
            if not song:
                cur.execute("SELECT title, file_id, plays, likes FROM songs ORDER BY RANDOM() LIMIT 1")
                song = cur.fetchone()
            if song:
                cur.execute("UPDATE songs SET plays = plays + 1 WHERE id = %s", (song_id,))
                conn.commit()
        finally:
            release_db(conn)
    except Exception:
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT title, file_id, plays, likes FROM songs ORDER BY RANDOM() LIMIT 1")
            song    = cur.fetchone()
            song_id = 0
        finally:
            release_db(conn)

    if song:
        title, file_id, plays, likes = song
        pts    = award_points(uid, "mood_radio", name)
        heat   = get_heat(plays)
        dj_txt = (
            f"MAXIMUS has read your energy. "
            f"You feel {text}. "
            f"This track was chosen for your soul right now. "
            f"{title}. BAZRAGOD."
        )
        await dj_speak(context, uid, dj_txt, dj)
        await update.message.reply_audio(
            file_id,
            caption=(
                f"🧠 MOOD RADIO\n\n"
                f"Your energy: {text}\n"
                f"MAXIMUS selected: {title}\n"
                f"{heat}  {plays:,} plays\n\n"
                f"+{pts} pts 🎵"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❤️ Like", callback_data=f"like:{song_id}"),
                InlineKeyboardButton("💰 Donate", url=CASHAPP),
            ]]),
        )
        await maybe_prophecy(uid, name, context)

    return True

# ╔══════════════════════════════════════════════════════════════╗
# ║         ⚔️ LYRIC CIPHER — ALIEN TECH #2                      ║
# ╚══════════════════════════════════════════════════════════════╝

async def lyric_cipher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cipher_sessions[uid] = True
    await update.message.reply_text(
        "⚔️ LYRIC CIPHER\n\n"
        "You vs MAXIMUS.\n\n"
        "Drop your verse below.\n"
        "MAXIMUS responds in BAZRAGOD's style.\n\n"
        "Write your bars 👇\n\n"
        "Type /cancel to exit."
    )


async def cipher_handler(
    uid: int, text: str, update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    if uid not in cipher_sessions:
        return False

    cipher_sessions.pop(uid)
    name = get_username(update)

    await update.message.reply_text("⚔️ MAXIMUS is writing the response...")

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are MAXIMUS writing bars in BAZRAGOD's lyric style. "
                        "BAZRAGOD is Jamaican-influenced independent artist. "
                        "Style: sovereign, confident, raw, Patois influence, "
                        "wealth mindset, street knowledge, spiritual power. "
                        "Write exactly 4 bars responding to the fan's verse. "
                        "Match their energy but elevate it. No explicit language."
                    ),
                },
                {"role": "user", "content": f"Fan verse:\n{text}\n\nRespond with 4 bars in BAZRAGOD style."},
            ],
            max_tokens=200,
        )
        verse = response.choices[0].message.content
        pts   = award_points(uid, "cipher", name)

        await update.message.reply_text(
            f"⚔️ BAZRAGOD CIPHER\n"
            f"{'═' * 20}\n\n"
            f"You:\n{text}\n\n"
            f"MAXIMUS:\n{verse}\n\n"
            f"{'═' * 20}\n"
            f"+{pts} pts — Parish 14 Cipher 🔥"
        )
        await maximus_speak(context, uid, verse)
        await maybe_prophecy(uid, name, context)

    except Exception as e:
        await update.message.reply_text(f"⚔️ Cipher error: {str(e)}")

    return True

# ╔══════════════════════════════════════════════════════════════╗
# ║         🎙️ FAN VOICE WALL — ALIEN TECH #5                    ║
# ╚══════════════════════════════════════════════════════════════╝

async def voice_wall_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["voice_wall_active"] = True
    await update.message.reply_text(
        "🎙️ FAN VOICE WALL\n\n"
        "Record a voice message and send it here.\n\n"
        "Approved shoutouts play LIVE on BazraGod Radio! 🔥\n\n"
        "Tips:\n"
        "• Shout out BAZRAGOD\n"
        "• Say your city and country\n"
        "• Big up Parish 14 Nation\n"
        "• Under 30 seconds\n\n"
        "Record and send now 👇\n\nType /cancel to go back."
    )


async def voice_wall_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)

    if not context.user_data.get("voice_wall_active"):
        return

    context.user_data.pop("voice_wall_active", None)
    voice = update.message.voice
    if not voice:
        return

    file_id = voice.file_id
    conn    = get_db()
    cur     = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO voice_wall (telegram_id, username, file_id) VALUES (%s, %s, %s) RETURNING id",
            (uid, name, file_id),
        )
        submission_id = cur.fetchone()[0]
        conn.commit()
    finally:
        release_db(conn)

    pts = award_points(uid, "voice_wall", name)
    await update.message.reply_text(
        f"🎙️ Submission #{submission_id} received!\n\n"
        f"MAXIMUS will review it.\n"
        f"Approved voices play on BazraGod Radio. 🔥\n\n"
        f"+{pts} pts 👑",
        reply_markup=main_menu,
    )
    try:
        await context.bot.send_message(
            OWNER_ID,
            f"🎙️ VOICE SUBMISSION #{submission_id}\n\n"
            f"Fan: @{name} ({uid})\n\n"
            f"/approve_voice {submission_id}\n"
            f"/reject_voice {submission_id}",
        )
        await context.bot.forward_message(
            chat_id=OWNER_ID,
            from_chat_id=uid,
            message_id=update.message.message_id,
        )
    except Exception:
        pass
    await maybe_prophecy(uid, name, context)


async def approve_voice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /approve_voice <id>")
        return
    vid  = int(args[0])
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "UPDATE voice_wall SET status = 'approved' WHERE id = %s RETURNING telegram_id, username",
            (vid,),
        )
        row = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)
    if row:
        await update.message.reply_text(f"✅ Voice #{vid} approved. Goes live on radio. 🎙️")
        try:
            await context.bot.send_message(
                row[0],
                "🎙️ YOUR VOICE SHOUTOUT WAS APPROVED!\n\nIt plays live on BazraGod Radio. 🔥\n\nThe world hears you. Parish 14. 👑",
            )
        except Exception:
            pass
    else:
        await update.message.reply_text("Not found.")


async def reject_voice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /reject_voice <id>")
        return
    vid  = int(args[0])
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("DELETE FROM voice_wall WHERE id = %s RETURNING id", (vid,))
        row = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)
    await update.message.reply_text(f"🗑 Voice #{vid} rejected." if row else "Not found.")


async def list_voices_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT id, username, status, submitted_at FROM voice_wall ORDER BY id DESC LIMIT 20"
        )
        rows = cur.fetchall()
    finally:
        release_db(conn)
    if not rows:
        await update.message.reply_text("No voice submissions yet.")
        return
    text = "🎙️ VOICE WALL\n\n"
    for r in rows:
        text += f"[{r[0]}] @{r[1]} — {r[3].strftime('%d/%m')} — {r[2]}\n"
    await update.message.reply_text(text)

# ╔══════════════════════════════════════════════════════════════╗
# ║         📺 YOUTUBE DETECTION SYSTEM                          ║
# ╚══════════════════════════════════════════════════════════════╝

async def youtube_detector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    uid  = update.effective_user.id
    name = get_username(update)

    if not re.search(r"youtube\.com|youtu\.be", text):
        return False

    dj  = get_current_dj()
    now = datetime.now().strftime("%I:%M %p")

    announcement = (
        f"📺 NEW BAZRAGOD VIDEO DETECTED\n\n"
        f"🔥 {dj['emoji']} {dj['name']} — {now}\n\n"
        f"A new BAZRAGOD video has landed.\n"
        f"Click the link and go watch it NOW. 🛸\n\n"
        f"{text}"
    )

    dj_text = (
        f"Attention Parish 14 Nation. "
        f"New BAZRAGOD video just dropped. "
        f"Go watch it now. "
        f"This is I.A.A.I.M.O Radio."
    )

    await dj_speak(context, uid, dj_text, dj)
    await update.message.reply_text(announcement)

    try:
        await _broadcast_to_all(context, announcement)
    except Exception:
        pass

    return True

# ╔══════════════════════════════════════════════════════════════╗
# ║         🎚️ SMART AUDIO UPLOAD CLASSIFICATION                 ║
# ╚══════════════════════════════════════════════════════════════╝

async def handle_audio_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    # Broadcast intercept
    if uid == OWNER_ID and pending_broadcasts.get(OWNER_ID) and update.message.text:
        pending_broadcasts.pop(OWNER_ID)
        sent = await _broadcast_to_all(context, update.message.text)
        await update.message.reply_text(f"📢 Broadcast sent to {sent} fans.")
        return

    if not is_admin(uid):
        return

    audio = update.message.audio
    if not audio:
        return

    caption = (update.message.caption or "").strip().lower()

    # Caption tag quick-classify
    if "#beat" in caption:
        await _save_audio(update, context, audio, "beats")
        return
    if "#drop" in caption:
        await _save_audio(update, context, audio, "drops")
        return
    if "#promo" in caption:
        text_content = audio.title or caption or "Promo"
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("INSERT INTO radio_promos (text) VALUES (%s) RETURNING id", (text_content,))
            new_id = cur.fetchone()[0]
            conn.commit()
        finally:
            release_db(conn)
        await update.message.reply_text(f"✅ Promo added. ID: {new_id}")
        return
    if "#song" in caption:
        await _save_audio(update, context, audio, "songs")
        return

    # No tag — show classification menu
    upload_sessions[uid] = {
        "file_id": audio.file_id,
        "title":   audio.title or "Untitled",
    }
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 Song",         callback_data="upload:songs")],
        [InlineKeyboardButton("🥁 Beat",         callback_data="upload:beats")],
        [InlineKeyboardButton("🎤 Drop",          callback_data="upload:drops")],
        [InlineKeyboardButton("📣 Radio Promo",   callback_data="upload:promo")],
    ])
    await update.message.reply_text(
        f"🎚️ CLASSIFY UPLOAD\n\n"
        f"Title: {audio.title or 'Untitled'}\n\n"
        f"What type is this audio?",
        reply_markup=keyboard,
    )


async def upload_classify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    if not is_admin(uid):
        return

    try:
        table = query.data.split(":")[1]
    except Exception:
        return

    session = upload_sessions.pop(uid, None)
    if not session:
        await query.message.reply_text("Session expired. Send the file again.")
        return

    file_id = session["file_id"]
    title   = session["title"]

    if table == "promo":
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("INSERT INTO radio_promos (text) VALUES (%s) RETURNING id", (title,))
            new_id = cur.fetchone()[0]
            conn.commit()
        finally:
            release_db(conn)
        await query.message.reply_text(f"✅ Radio Promo added. ID: {new_id}")
        return

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            f"INSERT INTO {table} (title, file_id) VALUES (%s, %s) RETURNING id",
            (title, file_id),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
    finally:
        release_db(conn)

    icons = {"songs": "🎵", "beats": "🥁", "drops": "🎤"}
    await query.message.reply_text(
        f"✅ {icons.get(table, '✅')} Added to {table}\nID: {new_id}\nTitle: {title}"
    )


async def _save_audio(update, context, audio, table: str):
    file_id = audio.file_id
    title   = audio.title or "Untitled"
    conn    = get_db()
    cur     = conn.cursor()
    try:
        cur.execute(
            f"INSERT INTO {table} (title, file_id) VALUES (%s, %s) RETURNING id",
            (title, file_id),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
    finally:
        release_db(conn)
    icons = {"songs": "🎵", "beats": "🥁", "drops": "🎤"}
    await update.message.reply_text(
        f"✅ {icons.get(table, '')} Added to {table}\nID: {new_id}\nTitle: {title}"
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║                  SOCIAL + SUPPORT                            ║
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
        f"Follow on every platform.\n"
        f"Bring more soldiers to the nation 🔥\n\n"
        f"+{pts} pts",
        reply_markup=keyboard,
    )


async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    pts  = award_points(uid, "support_artist", name)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 CashApp", url=CASHAPP)],
        [InlineKeyboardButton("💳 PayPal",  url=PAYPAL)],
    ])
    await update.message.reply_text(
        f"💰 SUPPORT BAZRAGOD\n\n"
        f"No label takes a cut here.\n"
        f"Every dollar goes directly to the music.\n\n"
        f"+{pts} pts for showing love 👑",
        reply_markup=keyboard,
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║                  MERCH + MUSIC STORE                         ║
# ╚══════════════════════════════════════════════════════════════╝

async def merch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👕 {MERCH_ITEMS['tshirt'][0]} — ${MERCH_ITEMS['tshirt'][1]}", callback_data="merch:tshirt")],
        [InlineKeyboardButton(f"🧥 {MERCH_ITEMS['pullover'][0]} — ${MERCH_ITEMS['pullover'][1]}", callback_data="merch:pullover")],
    ])
    await update.message.reply_text(
        f"👕 PARISH 14 MERCH\n\nOfficial BAZRAGOD clothing.\nWear the nation.\n\nSelect your item 👇",
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
        f"👕 PARISH 14 ORDER\n\nItem:  {item_name}\nPrice: ${price}\n\n"
        f"After payment send admin:\n• Your size\n• Shipping address\n• Payment confirmation\n\nParish 14 Nation. 👑",
        reply_markup=keyboard,
    )


async def music_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🎵 {STORE_ITEMS['single'][0]} — ${STORE_ITEMS['single'][1]}", callback_data="store:single")],
        [InlineKeyboardButton(f"📦 {STORE_ITEMS['bundle'][0]} — ${STORE_ITEMS['bundle'][1]}", callback_data="store:bundle")],
        [InlineKeyboardButton(f"👑 {STORE_ITEMS['exclusive'][0]} — ${STORE_ITEMS['exclusive'][1]}", callback_data="store:exclusive")],
    ])
    await update.message.reply_text(
        f"🛒 BAZRAGOD MUSIC STORE\n\nDirect from the artist.\nNo streaming cuts. No label fees.\n\nSelect your purchase 👇",
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
    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name
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
        f"🛒 ORDER #{purchase_id}\n\nItem:  {item_name}\nPrice: ${price}\n\n"
        f"Send payment then message admin with proof.\nDownload unlocked. 🔐",
        reply_markup=keyboard,
    )
    try:
        await context.bot.send_message(
            OWNER_ID,
            f"💰 NEW PURCHASE\n\nOrder: #{purchase_id}\nFan: @{name} ({uid})\nItem: {item_name}\nPrice: ${price}",
        )
    except Exception:
        pass

# ╔══════════════════════════════════════════════════════════════╗
# ║                  BOOKING + FAN RADAR                         ║
# ╚══════════════════════════════════════════════════════════════╝

async def booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📅 BOOK BAZRAGOD\n\nShows, features, events, collabs.\n\n"
        f"Contact:\n{BOOKING_EMAIL}\n\n"
        f"Include:\n• Event type\n• Date and location\n• Budget\n• Contact number\n\n"
        f"BAZRAGOD is global. Parish 14 Nation. 🛸"
    )


async def fan_radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT COALESCE(country, 'Unknown'), COUNT(*) as fans
            FROM fan_locations GROUP BY country ORDER BY fans DESC LIMIT 10
        """)
        rows = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM fan_locations")
        total = cur.fetchone()[0]
    finally:
        release_db(conn)

    if not rows:
        await update.message.reply_text("📡 No fans mapped yet. Share your location! 🌍")
        return

    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    text   = f"📡 PARISH 14 FAN RADAR\n\nTotal fans mapped: {total}\n\n"
    for i, (country, fans) in enumerate(rows):
        text += f"{medals[i]} {country} — {fans} fans\n"
    text += "\n🛸 This is where BAZRAGOD's army stands."
    await update.message.reply_text(text)

# ╔══════════════════════════════════════════════════════════════╗
# ║                  WISDOM + FITNESS                            ║
# ╚══════════════════════════════════════════════════════════════╝

async def wisdom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    pts  = award_points(uid, "wisdom", name)
    await update.message.reply_text(f"👑 Royal Wisdom\n\n{random.choice(QUOTES)}\n\n+{pts} pts")


async def fitness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    pts  = award_points(uid, "fitness", name)
    await update.message.reply_text(f"{FITNESS_MSG}\n\n+{pts} pts 💪")

# ╔══════════════════════════════════════════════════════════════╗
# ║                  LEADERBOARD + POINTS                        ║
# ╚══════════════════════════════════════════════════════════════╝

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT username, points, tier, is_supporter FROM fans ORDER BY points DESC LIMIT 10")
        rows = cur.fetchall()
    finally:
        release_db(conn)

    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    text   = "🏆 PARISH 14 LEADERBOARD\n\n"
    for i, (username, points, tier, is_sup) in enumerate(rows):
        label  = f"@{username}" if username else "Anonymous"
        badge  = " 💎" if is_sup else ""
        text  += f"{medals[i]} {label}{badge}\n   {points} pts — {tier}\n\n"
    await update.message.reply_text(text)


async def my_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT points, invites, tier FROM fans WHERE telegram_id = %s", (uid,))
        row = cur.fetchone()
        cur.execute(
            "SELECT COUNT(*) FROM fans WHERE points > COALESCE((SELECT points FROM fans WHERE telegram_id = %s), 0)",
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
        f"⭐ YOUR STATS\n{'═' * 20}\n"
        f"Points:  {pts}\nRank:    #{rank}\nTier:    {tier}\nInvites: {invites}\n{'═' * 20}\n"
        f"{next_tier_msg}\n\nKeep grinding to climb 👑"
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║                  FAN PROFILE                                 ║
# ╚══════════════════════════════════════════════════════════════╝

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT username, points, invites, tier, city, country, joined_at, is_supporter FROM fans WHERE telegram_id = %s",
            (uid,),
        )
        row = cur.fetchone()
        cur.execute(
            "SELECT COUNT(*) FROM fans WHERE points > COALESCE((SELECT points FROM fans WHERE telegram_id = %s), 0)",
            (uid,),
        )
        rank_pos = cur.fetchone()[0] + 1
    finally:
        release_db(conn)

    if not row:
        await update.message.reply_text("Send /start first.")
        return

    username, points, invites, tier, city, country, joined_at, is_sup = row
    display  = f"@{username}" if username else name
    location = f"{city}, {country}" if city else "Not shared yet"
    joined   = joined_at.strftime("%B %Y") if joined_at else "Unknown"
    sup_badge = " 💎 Supporter" if is_sup else ""

    next_rank_msg = ""
    for threshold, label in RANKS:
        if points < threshold:
            next_rank_msg = f"\n🎯 {threshold - points} pts to reach {label}"
            break

    await update.message.reply_text(
        f"👤 FAN PROFILE\n{'═' * 20}\n"
        f"Name:    {display}{sup_badge}\n"
        f"Rank:    {tier}\n"
        f"Points:  {points}\n"
        f"#:       #{rank_pos}\n"
        f"Invites: {invites}\n"
        f"City:    {location}\n"
        f"Joined:  {joined}\n"
        f"{'═' * 20}{next_rank_msg}"
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║                  DAILY MISSION                               ║
# ╚══════════════════════════════════════════════════════════════╝

async def daily_mission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid   = update.effective_user.id
    today = date.today()
    conn  = get_db()
    cur   = conn.cursor()
    try:
        cur.execute(
            "SELECT completed FROM missions WHERE telegram_id = %s AND mission_date = %s",
            (uid, today),
        )
        row = cur.fetchone()
        if not row:
            cur.execute(
                "INSERT INTO missions (telegram_id, mission_date) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (uid, today),
            )
            conn.commit()
    finally:
        release_db(conn)

    if row and row[0]:
        await update.message.reply_text("🎯 DAILY MISSION\n\n✅ Already completed today!\n\nCome back tomorrow. 👑")
        return

    mission_text = random.choice(MISSIONS)
    await update.message.reply_text(
        f"🎯 DAILY MISSION\n{'═' * 20}\n\n{mission_text}\n\nReward: +{POINTS['mission']} pts\n\nComplete it then tap below 👇",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Mark Complete", callback_data=f"mission:complete:{uid}")
        ]]),
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
            INSERT INTO missions (telegram_id, mission_date, completed) VALUES (%s, %s, TRUE)
            ON CONFLICT (telegram_id, mission_date) DO UPDATE SET completed = TRUE
        """, (uid, today))
        conn.commit()
    finally:
        release_db(conn)

    name = query.from_user.username or query.from_user.first_name
    pts  = award_points(uid, "mission", name)
    await query.message.reply_text(
        f"🎯 MISSION COMPLETE!\n\n+{pts} points 🔥\n\nCome back tomorrow. Parish 14 never stops. 👑"
    )
    await maybe_prophecy(uid, name, context)

# ╔══════════════════════════════════════════════════════════════╗
# ║                  REFERRAL SYSTEM                             ║
# ╚══════════════════════════════════════════════════════════════╝

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT invites, tier FROM fans WHERE telegram_id = %s", (uid,))
        row = cur.fetchone()
    finally:
        release_db(conn)

    invites = row[0] if row else 0
    tier    = row[1] if row else "🎧 Fan"
    tiers   = "\n".join([f"  {v} — {k} invites" for k, v in REFERRAL_TIERS.items()])

    await update.message.reply_text(
        f"👥 REFERRAL SYSTEM\n\nYour link:\n{link}\n\n"
        f"Invites: {invites}\nTier:    {tier}\n\n"
        f"Tier Rewards:\n{tiers}\n\n"
        f"Every invite = +{POINTS['invite_friend']} pts 🔥\nBuild the Parish 14 army. 👑"
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║                  LOCATION SYSTEM                             ║
# ╚══════════════════════════════════════════════════════════════╝

async def location_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Send Location", request_location=True)], ["🔙 Back to Menu"]],
        resize_keyboard=True, one_time_keyboard=True,
    )
    await update.message.reply_text(
        f"📍 Share your location.\n\nPut your city on the Parish 14 fan map.\nEarn +{POINTS['share_location']} pts 🌍",
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
            SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude, updated_at = NOW()
        """, (uid, loc.latitude, loc.longitude))
        conn.commit()
    finally:
        release_db(conn)
    pts = award_points(uid, "share_location", name)
    await update.message.reply_text(
        f"📍 Location recorded!\n\n+{pts} pts — your city is on the map 🌍\n\nBAZRAGOD sees where his army stands. 👑",
        reply_markup=main_menu,
    )
    await maybe_prophecy(uid, name, context)

# ╔══════════════════════════════════════════════════════════════╗
# ║              ASTROCARTOGRAPHY SYSTEM                         ║
# ╚══════════════════════════════════════════════════════════════╝

async def astro_reading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not openai_client:
        await update.message.reply_text("🪐 ASTRO READING\n\nMAXIMUS offline. OPENAI_API_KEY required.")
        return
    uid = update.effective_user.id
    astro_sessions[uid] = {"step": "birth_date"}
    await update.message.reply_text(
        "🪐 MAXIMUS ASTRO READING\n\nStep 1 of 3\n\n"
        "Enter your birth date:\nFormat: DD/MM/YYYY\n\nExample: 15/03/1990"
    )


async def astro_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    uid     = update.effective_user.id
    name    = get_username(update)
    if uid not in astro_sessions:
        return False

    session = astro_sessions[uid]
    text    = update.message.text.strip()
    step    = session.get("step")

    if step == "birth_date":
        session["birth_date"] = text
        session["step"]       = "birth_time"
        await update.message.reply_text("✅ Birth date saved.\n\nStep 2 of 3\n\nEnter birth time:\nFormat: HH:MM AM/PM\n\nType 'unknown' if unsure.")
        return True

    if step == "birth_time":
        session["birth_time"] = text
        session["step"]       = "location"
        await update.message.reply_text("✅ Birth time saved.\n\nStep 3 of 3\n\nEnter birth city and current city:\n\nFormat: BirthCity, CurrentCity\n\nExample: Kingston, London")
        return True

    if step == "location":
        session["step"] = "generating"
        await update.message.reply_text("🪐 MAXIMUS is reading your stars...\n\nStand by. 👑")
        try:
            parts        = text.split(",")
            birth_city   = parts[0].strip() if parts else "Unknown"
            current_city = parts[1].strip() if len(parts) > 1 else birth_city
            prompt = (
                f"Birth Date: {session.get('birth_date')}\n"
                f"Birth Time: {session.get('birth_time')}\n"
                f"Birth City: {birth_city}\n"
                f"Current City: {current_city}\n\n"
                f"Generate a full astrocartography reading."
            )
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are MAXIMUS, astrocartography reader for BAZRAGOD. Generate a powerful documentary-style reading in 4 paragraphs: current location energy, best for creativity and music, best for business and wealth, power advice now. No fear language. End with a sovereign statement."},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=600,
            )
            reading = response.choices[0].message.content
            conn = get_db()
            cur  = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO astro_profiles (telegram_id, birth_date, birth_time, birth_city, current_city)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (telegram_id) DO UPDATE
                    SET birth_date = EXCLUDED.birth_date, birth_time = EXCLUDED.birth_time,
                        birth_city = EXCLUDED.birth_city, current_city = EXCLUDED.current_city, last_reading = NOW()
                """, (uid, session.get("birth_date"), session.get("birth_time"), birth_city, current_city))
                conn.commit()
            finally:
                release_db(conn)
            pts = award_points(uid, "astro", name)
            await update.message.reply_text(
                f"🪐 YOUR ASTRO READING\n{'═' * 20}\n\n{reading}\n\n{'═' * 20}\n+{pts} pts 👑"
            )
            await maximus_speak(context, uid, reading[:500])
            await maybe_prophecy(uid, name, context)
        except Exception as e:
            await update.message.reply_text(f"🪐 Error: {str(e)}\n\nTry again later.")
        finally:
            astro_sessions.pop(uid, None)
        return True

    return False

# ╔══════════════════════════════════════════════════════════════╗
# ║                  MAXIMUS AI ASSISTANT                        ║
# ╚══════════════════════════════════════════════════════════════╝

async def ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not openai_client:
        await update.message.reply_text("🤖 MAXIMUS is offline. OPENAI_API_KEY not set.")
        return
    uid  = update.effective_user.id
    name = get_username(update)
    context.user_data["ai_active"]  = True
    context.user_data["ai_history"] = context.user_data.get("ai_history", [])
    pts = award_points(uid, "ai_chat", name)
    await update.message.reply_text(
        f"🤖 MAXIMUS ONLINE\n\nRoyal AI of BAZRAGOD.\nManager. Publicist. Radio DJ. Strategist.\n\nAsk me anything.\nType /menu to return.\n\n+{pts} pts"
    )


async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
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
            messages=[{"role": "system", "content": AI_SYSTEM_PROMPT}, *history],
            max_tokens=400,
        )
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        context.user_data["ai_history"] = history
        award_points(uid, "ai_chat", name)
        await update.message.reply_text(f"🤖 MAXIMUS\n\n{reply}")
        await maximus_speak(context, uid, reply)
        await maybe_prophecy(uid, name, context)
    except Exception as e:
        await update.message.reply_text(f"🤖 MAXIMUS error: {str(e)}")

    return True

# ╔══════════════════════════════════════════════════════════════╗
# ║         📊 WEEKLY INTEL BROADCAST — ALIEN TECH #4            ║
# ╚══════════════════════════════════════════════════════════════╝

async def send_weekly_intel():
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM fans")
        total_fans = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fans WHERE joined_at > NOW() - INTERVAL '7 days'")
        new_fans = cur.fetchone()[0]
        cur.execute("SELECT SUM(points) FROM fans")
        total_pts = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM fan_locations")
        mapped = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(country,'Unknown'), COUNT(*) FROM fan_locations GROUP BY country ORDER BY 2 DESC LIMIT 3")
        top_countries = cur.fetchall()
        cur.execute("SELECT username, points FROM fans ORDER BY points DESC LIMIT 3")
        top_fans = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM purchases WHERE status = 'pending'")
        pending = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM voice_wall WHERE status = 'pending'")
        pending_voices = cur.fetchone()[0]
        cur.execute("SELECT title, plays FROM songs ORDER BY plays DESC LIMIT 3")
        top_songs = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM fans WHERE is_supporter = TRUE")
        supporters = cur.fetchone()[0]
    finally:
        release_db(conn)

    countries_text = "\n".join([f"  📍 {c} — {f} fans" for c, f in top_countries]) or "  None yet"
    fans_text      = "\n".join([f"  🏅 @{f} — {p} pts" for f, p in top_fans if f]) or "  None yet"
    songs_text     = "\n".join([f"  🎵 {t} — {p:,} plays {get_heat(p)}" for t, p in top_songs]) or "  None"

    report = (
        f"📊 WEEKLY INTEL REPORT\n{'═' * 22}\n"
        f"Week: {datetime.now().strftime('%d %B %Y')}\n\n"
        f"👥 Total Fans:       {total_fans}\n"
        f"🆕 New This Week:    {new_fans}\n"
        f"⭐ Total Points:     {total_pts}\n"
        f"💎 Supporters:       {supporters}\n"
        f"📍 Fans Mapped:      {mapped}\n"
        f"🛒 Pending Orders:   {pending}\n"
        f"🎙️ Pending Voices:   {pending_voices}\n\n"
        f"TOP COUNTRIES:\n{countries_text}\n\n"
        f"TOP FANS:\n{fans_text}\n\n"
        f"TOP SONGS:\n{songs_text}\n\n"
        f"— MAXIMUS INTEL SYSTEM 👑"
    )
    summary = (
        f"Weekly intel report ready. "
        f"{new_fans} new fans joined this week. "
        f"{total_fans} total soldiers in the Parish 14 army. "
        f"{supporters} active supporters. "
        f"The movement grows."
    )
    try:
        await telegram_app.bot.send_message(OWNER_ID, report)
        await maximus_speak_direct(telegram_app.bot, OWNER_ID, summary)
    except Exception as e:
        print(f"Weekly intel error: {e}")


def weekly_intel_thread():
    last_sent_week = None
    while True:
        try:
            now      = datetime.now()
            week_key = now.strftime("%Y-%W")
            if now.weekday() == 6 and now.hour == 9 and last_sent_week != week_key:
                asyncio.run_coroutine_threadsafe(send_weekly_intel(), loop)
                last_sent_week = week_key
        except Exception as e:
            print(f"Weekly thread error: {e}")
        time.sleep(60)

# ╔══════════════════════════════════════════════════════════════╗
# ║                  ADMIN PANEL                                 ║
# ╚══════════════════════════════════════════════════════════════╝

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        "👑 I.A.A.I.M.O ADMIN PANEL v10.000\n"
        "════════════════════════════\n\n"
        "ANALYTICS\n"
        "/stats  /radar  /weekly\n\n"
        "CONTENT\n"
        "/list_songs   /delete_song <id>\n"
        "/list_beats   /delete_beat <id>\n"
        "/list_drops   /delete_drop <id>\n\n"
        "VOICE WALL\n"
        "/list_voices\n"
        "/approve_voice <id>\n"
        "/reject_voice <id>\n\n"
        "SUPPORTERS\n"
        "/activate_supporter <telegram_id>\n\n"
        "BROADCAST\n"
        "/broadcast\n"
        "/shoutout @username\n"
        "/announce <message>\n\n"
        "UPLOAD\n"
        "Send audio (smart classify menu appears)\n"
        "Or use captions: #song #beat #drop #promo"
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
        cur.execute("SELECT COUNT(*) FROM voice_wall WHERE status = 'pending'")
        pending_voices = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM astro_profiles")
        astro_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fans WHERE is_supporter = TRUE")
        supporters = cur.fetchone()[0]
        cur.execute("SELECT title, plays FROM songs ORDER BY plays DESC LIMIT 1")
        top_song = cur.fetchone()
        cur.execute("SELECT username, points FROM fans ORDER BY points DESC LIMIT 1")
        top_fan = cur.fetchone()
    finally:
        release_db(conn)

    top_song_str = f"{top_song[0]} ({top_song[1]:,} plays)" if top_song else "None"
    top_fan_str  = f"@{top_fan[0]} ({top_fan[1]} pts)" if top_fan else "None"

    await update.message.reply_text(
        f"📊 MISERBOT STATS — v10.000\n{'═' * 22}\n"
        f"👥 Fans:             {total_fans}\n"
        f"💎 Supporters:       {supporters}\n"
        f"⭐ Points Given:     {total_pts}\n"
        f"🎵 Songs:            {total_songs}\n"
        f"🥁 Beats:            {total_beats}\n"
        f"🎤 Drops:            {total_drops}\n"
        f"📍 Fans Mapped:      {mapped}\n"
        f"🪐 Astro Readings:   {astro_count}\n"
        f"🛒 Pending Orders:   {pending}\n"
        f"🎙️ Pending Voices:   {pending_voices}\n"
        f"🔥 Top Song:         {top_song_str}\n"
        f"🏆 Top Fan:          {top_fan_str}"
    )


async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT COALESCE(country,'Unknown'), COUNT(*) FROM fan_locations GROUP BY country ORDER BY 2 DESC LIMIT 15")
        rows = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM fan_locations")
        total = cur.fetchone()[0]
    finally:
        release_db(conn)
    if not rows:
        await update.message.reply_text("No fan locations yet.")
        return
    text = f"🗺 TOUR INTELLIGENCE RADAR\nTotal mapped: {total}\n\n"
    for country, fans in rows:
        text += f"📍 {country} — {fans} fans\n"
    await update.message.reply_text(text)


async def weekly_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("📊 Generating weekly intel...")
    await send_weekly_intel()
    await update.message.reply_text("✅ Weekly intel sent.")


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    pending_broadcasts[OWNER_ID] = True
    await update.message.reply_text("📢 BROADCAST MODE\n\nSend your message now.\n/cancel to abort.")


async def shoutout_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /shoutout @username")
        return
    msg  = f"🔥 SHOUTOUT FROM BAZRAGOD\n\nBig up {args[0]} — real Parish 14 energy! 👑\n\nI.A.A.I.M.O"
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
    await update.message.reply_text(f"Sent to {sent} fans.")


async def _broadcast_to_all(context, text: str, speak: bool = False) -> int:
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


async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    pending_broadcasts.pop(uid, None)
    astro_sessions.pop(uid, None)
    mood_sessions.pop(uid, None)
    cipher_sessions.pop(uid, None)
    upload_sessions.pop(uid, None)
    context.user_data["ai_active"]         = False
    context.user_data["voice_wall_active"] = False
    await update.message.reply_text("Cancelled.", reply_markup=main_menu)


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    astro_sessions.pop(uid, None)
    mood_sessions.pop(uid, None)
    cipher_sessions.pop(uid, None)
    upload_sessions.pop(uid, None)
    context.user_data["ai_active"]         = False
    context.user_data["ai_history"]        = []
    context.user_data["voice_wall_active"] = False
    await update.message.reply_text("👑 Main Menu", reply_markup=main_menu)


async def list_songs_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    await _list_table_with_stats(update, "songs")

async def list_beats_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    await _list_table(update, "beats", "🥁 BEATS")

async def list_drops_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    await _list_table(update, "drops", "🎤 DROPS")

async def _list_table_with_stats(update, table):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(f"SELECT id, title, plays, likes FROM {table} ORDER BY id")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    text = f"🎵 SONGS\n{'═' * 16}\n\n"
    for r in rows:
        heat  = get_heat(r[2])
        text += f"[{r[0]}] {r[1]}\n   {heat} {r[2]:,} plays  ❤️ {r[3]}\n"
    await update.message.reply_text(text or "Empty.")

async def _list_table(update, table, label):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(f"SELECT id, title FROM {table} ORDER BY id")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    text = f"{label}\n{'═' * 16}\n\n"
    for r in rows:
        text += f"[{r[0]}] {r[1]}\n"
    await update.message.reply_text(text or "Empty.")

async def delete_song_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    await _delete_from(update, context, "songs")

async def delete_beat_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    await _delete_from(update, context, "beats")

async def delete_drop_cmd(update, context):
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
        cur.execute(f"DELETE FROM {table} WHERE id = %s RETURNING title", (row_id,))
        row = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)
    await update.message.reply_text(f"🗑 Deleted: {row[0]}" if row else "Not found.")

# ╔══════════════════════════════════════════════════════════════╗
# ║                       ROUTER                                 ║
# ╚══════════════════════════════════════════════════════════════╝

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    uid  = update.effective_user.id

    # Priority session intercepts
    if uid in astro_sessions:
        if await astro_input_handler(update, context): return

    if uid in mood_sessions:
        if await mood_radio_handler(uid, text, update, context): return

    if uid in cipher_sessions:
        if await cipher_handler(uid, text, update, context): return

    if context.user_data.get("ai_active"):
        if await ai_chat_handler(update, context): return

    # YouTube detection — fires before menu routes
    if re.search(r"youtube\.com|youtu\.be", text):
        if await youtube_detector(update, context): return

    # Broadcast intercept
    if uid == OWNER_ID and pending_broadcasts.get(OWNER_ID):
        pending_broadcasts.pop(OWNER_ID)
        sent = await _broadcast_to_all(context, text)
        await update.message.reply_text(f"📢 Broadcast sent to {sent} fans.")
        return

    routes = {
        "🎧 BAZRAGOD MUSIC":  music,
        "📻 BazraGod Radio":  radio,
        "🧠 Mood Radio":      mood_radio,
        "⚔️ Lyric Cipher":   lyric_cipher,
        "📊 Top Charts":      top_charts,
        "💎 Supporter":       supporter,
        "🥁 Beats":           beats,
        "🎤 Drops":           drops_menu,
        "🏆 Leaderboard":     leaderboard,
        "⭐ My Points":       my_points,
        "👤 My Profile":      my_profile,
        "🎯 Daily Mission":   daily_mission,
        "💰 Support Artist":  support,
        "🌐 Social":          social,
        "🛒 Music Store":     music_store,
        "👕 Parish 14":       merch,
        "👑 Wisdom":          wisdom,
        "🏋 Fitness":         fitness,
        "📍 Share Location":  location_prompt,
        "👥 Refer a Friend":  refer,
        "📡 Fan Radar":       fan_radar,
        "📅 Booking":         booking,
        "🎙️ Voice Wall":     voice_wall_prompt,
        "🪐 Astro Reading":   astro_reading,
        "🤖 MAXIMUS AI":      ai_assistant,
        "🔙 Back to Menu":    menu_cmd,
    }

    handler = routes.get(text)
    if handler:
        await handler(update, context)

# ╔══════════════════════════════════════════════════════════════╗
# ║              TELEGRAM APP ASSEMBLY                           ║
# ╚══════════════════════════════════════════════════════════════╝

telegram_app = Application.builder().token(BOT_TOKEN).build()

# Core
telegram_app.add_handler(CommandHandler("start",               start))
telegram_app.add_handler(CommandHandler("menu",                menu_cmd))
telegram_app.add_handler(CommandHandler("cancel",              cancel_cmd))

# Admin
telegram_app.add_handler(CommandHandler("admin",               admin_panel))
telegram_app.add_handler(CommandHandler("stats",               stats))
telegram_app.add_handler(CommandHandler("radar",               radar))
telegram_app.add_handler(CommandHandler("weekly",              weekly_cmd))
telegram_app.add_handler(CommandHandler("broadcast",           broadcast_cmd))
telegram_app.add_handler(CommandHandler("shoutout",            shoutout_cmd))
telegram_app.add_handler(CommandHandler("announce",            announce_cmd))
telegram_app.add_handler(CommandHandler("list_songs",          list_songs_cmd))
telegram_app.add_handler(CommandHandler("list_beats",          list_beats_cmd))
telegram_app.add_handler(CommandHandler("list_drops",          list_drops_cmd))
telegram_app.add_handler(CommandHandler("delete_song",         delete_song_cmd))
telegram_app.add_handler(CommandHandler("delete_beat",         delete_beat_cmd))
telegram_app.add_handler(CommandHandler("delete_drop",         delete_drop_cmd))
telegram_app.add_handler(CommandHandler("list_voices",         list_voices_cmd))
telegram_app.add_handler(CommandHandler("approve_voice",       approve_voice_cmd))
telegram_app.add_handler(CommandHandler("reject_voice",        reject_voice_cmd))
telegram_app.add_handler(CommandHandler("activate_supporter",  activate_supporter_cmd))

# Callbacks — most specific first
telegram_app.add_handler(CallbackQueryHandler(intro_cb,            pattern="^intro:"))
telegram_app.add_handler(CallbackQueryHandler(mission_complete_cb, pattern="^mission:"))
telegram_app.add_handler(CallbackQueryHandler(store_cb,            pattern="^store:"))
telegram_app.add_handler(CallbackQueryHandler(merch_cb,            pattern="^merch:"))
telegram_app.add_handler(CallbackQueryHandler(like_cb,             pattern="^like:"))
telegram_app.add_handler(CallbackQueryHandler(supporter_verify_cb, pattern="^supporter:"))
telegram_app.add_handler(CallbackQueryHandler(upload_classify_cb,  pattern="^upload:"))
telegram_app.add_handler(CallbackQueryHandler(play_song,           pattern="^song:"))
telegram_app.add_handler(CallbackQueryHandler(play_beat_cb,        pattern="^beat:"))
telegram_app.add_handler(CallbackQueryHandler(play_drop_cb,        pattern="^drop:"))

# Media handlers
telegram_app.add_handler(MessageHandler(filters.LOCATION, location_handler))
telegram_app.add_handler(MessageHandler(filters.VOICE,    voice_wall_submit))
telegram_app.add_handler(MessageHandler(filters.AUDIO,    handle_audio_upload))

# Text router — always last
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

# ╔══════════════════════════════════════════════════════════════╗
# ║                    ASYNC LOOP                                ║
# ╚══════════════════════════════════════════════════════════════╝

loop = asyncio.new_event_loop()

def start_bot():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    loop.run_forever()

threading.Thread(target=start_bot, daemon=True).start()

# ╔══════════════════════════════════════════════════════════════╗
# ║                      WEBHOOK                                 ║
# ╚══════════════════════════════════════════════════════════════╝

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    data   = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), loop)
    return "ok"

@app.route("/")
def health():
    return "I.A.A.I.M.O ONLINE — PARISH 14 NATION v10.000", 200

# ╔══════════════════════════════════════════════════════════════╗
# ║                       MAIN                                   ║
# ╚══════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    init_pool()
    init_db()
    threading.Thread(target=weekly_intel_thread, daemon=True).start()
    print("╔══════════════════════════════════════════╗")
    print("║   I.A.A.I.M.O — MISERBOT v10.000        ║")
    print("║   Owner:    BAZRAGOD                     ║")
    print("║   Nation:   Parish 14                    ║")
    print("║   DJ System: ACTIVE                      ║")
    print("║   Alien Tech: ALL 5 ONLINE               ║")
    print("║   Status:   ONLINE                       ║")
    print("╚══════════════════════════════════════════╝")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
