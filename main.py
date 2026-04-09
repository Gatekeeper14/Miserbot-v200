"""
╔══════════════════════════════════════════════════════════════╗
║         I.A.A.I.M.O — MASTER SYSTEM v13.000                 ║
║  Independent Artists Artificial Intelligence Music Ops       ║
║  Bot:     Miserbot       Nation:  Parish 14                  ║
║  Owner:   BAZRAGOD                                           ║
║                                                              ║
║  v13 UPGRADES:                                               ║
║  📻 Channel Radio Loop — 24/7 broadcast to Telegram channel  ║
║  ▶️  Next Track Button — in-chat continuous play             ║
║  🎚️ Ordered Playlist + Ad Breaks in rotation                 ║
║  🌍 Language gate before intro (new fans only)               ║
║  🔧 Deployment hardened (Procfile + health check)            ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import re
import time
import random
import asyncio
import threading
from datetime import datetime, date, timedelta
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

BOT_TOKEN        = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL     = os.environ.get("DATABASE_URL")
OPENAI_API_KEY   = os.environ.get("OPENAI_API_KEY")
OWNER_ID         = int(os.environ.get("OWNER_ID", "8741545426"))
RADIO_CHANNEL_ID = os.environ.get("RADIO_CHANNEL_ID", "")  # e.g. -1001234567890
BOT_USERNAME     = "miserbot"
WEBHOOK_PATH     = "/webhook"

INTRO_FILE_ID = os.environ.get(
    "INTRO_FILE_ID",
    "CQACAgEAAxkBAAICN2nUZHzzXlQszP-a08nJiSctUeOhAAL-BQACEbKpRg3vpxJvYve3OwQ",
)

BOOKING_EMAIL     = "Miserbot.ai@gmail.com"
CASHAPP           = "https://cash.app/$BAZRAGOD"
PAYPAL            = "https://paypal.me/bazragod1"
SUPPORTER_PRICE   = 19.99
CHARITY_PRICE     = 1.00
CHARITY_THRESHOLD = 500

# How long radio loop waits between songs (seconds)
# Tune this to approximate your average song length
RADIO_SONG_DELAY = 200
RADIO_AD_DELAY   = 25

SOCIALS = {
    "📸 Instagram": "https://www.instagram.com/bazragod_timeless",
    "🎵 TikTok":    "https://www.tiktok.com/@bazragod_official",
    "▶️ YouTube":   "https://youtube.com/@bazragodmusictravelandleis8835",
    "🐦 X":         "https://x.com/toligarch65693",
    "👻 Snapchat":  "https://snapchat.com/t/L7djDwfj",
    "🎮 Twitch":    "https://twitch.tv/bazra14",
    "🎧 Spotify":   "https://open.spotify.com/artist/2IwaaLobpi2NSGD3B5xapK",
}

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
app           = Flask(__name__)

# ╔══════════════════════════════════════════════════════════════╗
# ║                🌍 LANGUAGE SYSTEM                            ║
# ╚══════════════════════════════════════════════════════════════╝

SUPPORTED_LANGUAGES = {
    "en": "🇺🇸 English",
    "es": "🇪🇸 Español",
    "fr": "🇫🇷 Français",
    "pt": "🇧🇷 Português",
    "de": "🇩🇪 Deutsch",
    "jm": "🇯🇲 Patois",
}

TRANSLATIONS = {
    "en": {
        "select_lang":    "🌍 Select your language to enter the platform.",
        "lang_saved":     "✅ Language saved.",
        "welcome_inside": "🛸 YOU ARE NOW INSIDE\n\nI.A.A.I.M.O — Parish 14 Nation.\nNo labels. No middlemen. Just the movement.\n\nYou are part of history. 🔥",
        "no_songs":       "Catalog loading... check back soon.",
        "location_saved": "📍 Location recorded!\n\nYour city is on the map 🌍\n\nBAZRAGOD sees where his army stands. 👑",
        "mission_done":   "🎯 MISSION COMPLETE!\n\nCome back tomorrow. Parish 14 never stops. 👑",
    },
    "es": {
        "select_lang":    "🌍 Selecciona tu idioma para entrar a la plataforma.",
        "lang_saved":     "✅ Idioma guardado.",
        "welcome_inside": "🛸 AHORA ESTÁS DENTRO\n\nI.A.A.I.M.O — Nación Parish 14.\nSin sellos. Sin intermediarios. Solo el movimiento.\n\nEres parte de la historia. 🔥",
        "no_songs":       "Catálogo cargando... vuelve pronto.",
        "location_saved": "📍 ¡Ubicación registrada!\n\nTu ciudad está en el mapa 🌍",
        "mission_done":   "🎯 ¡MISIÓN COMPLETADA!\n\nVuelve mañana. Parish 14 nunca para. 👑",
    },
    "fr": {
        "select_lang":    "🌍 Sélectionnez votre langue pour entrer sur la plateforme.",
        "lang_saved":     "✅ Langue sauvegardée.",
        "welcome_inside": "🛸 VOUS ÊTES MAINTENANT À L'INTÉRIEUR\n\nI.A.A.I.M.O — Nation Parish 14.\nSans labels. Sans intermédiaires. Juste le mouvement.\n\nVous faites partie de l'histoire. 🔥",
        "no_songs":       "Catalogue en chargement... revenez bientôt.",
        "location_saved": "📍 Localisation enregistrée!\n\nVotre ville est sur la carte 🌍",
        "mission_done":   "🎯 MISSION ACCOMPLIE!\n\nReviens demain. Parish 14 ne s'arrête jamais. 👑",
    },
    "pt": {
        "select_lang":    "🌍 Selecione seu idioma para entrar na plataforma.",
        "lang_saved":     "✅ Idioma salvo.",
        "welcome_inside": "🛸 VOCÊ ESTÁ DENTRO\n\nI.A.A.I.M.O — Nação Parish 14.\nSem gravadoras. Sem intermediários. Só o movimento.\n\nVocê faz parte da história. 🔥",
        "no_songs":       "Catálogo carregando... volte em breve.",
        "location_saved": "📍 Localização registrada!\n\nSua cidade está no mapa 🌍",
        "mission_done":   "🎯 MISSÃO COMPLETA!\n\nVolte amanhã. Parish 14 nunca para. 👑",
    },
    "de": {
        "select_lang":    "🌍 Wähle deine Sprache, um die Plattform zu betreten.",
        "lang_saved":     "✅ Sprache gespeichert.",
        "welcome_inside": "🛸 DU BIST JETZT DRIN\n\nI.A.A.I.M.O — Parish 14 Nation.\nKein Label. Kein Mittelsmann. Nur die Bewegung.\n\nDu bist Teil der Geschichte. 🔥",
        "no_songs":       "Katalog wird geladen... bald verfügbar.",
        "location_saved": "📍 Standort gespeichert!\n\nDeine Stadt ist auf der Karte 🌍",
        "mission_done":   "🎯 MISSION ABGESCHLOSSEN!\n\nKomm morgen wieder. Parish 14 hört nie auf. 👑",
    },
    "jm": {
        "select_lang":    "🌍 Select yu language fi enter di platform.",
        "lang_saved":     "✅ Language saved, massive.",
        "welcome_inside": "🛸 YU INSIDE NOW\n\nI.A.A.I.M.O — Parish 14 Nation.\nNo label. No middleman. Just di movement.\n\nYu part of history. 🔥",
        "no_songs":       "Catalog loading... check back soon.",
        "location_saved": "📍 Location saved!\n\nYu city pon di map 🌍",
        "mission_done":   "🎯 MISSION COMPLETE!\n\nCome back tomorrow. Parish 14 nuh stop. 👑",
    },
}

def t(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )

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
# ║          🎙️ DJ PERSONALITY SYSTEM (4 time-based DJs)         ║
# ╚══════════════════════════════════════════════════════════════╝

DJS = {
    "aurora": {
        "name":   "DJ Aurora",  "emoji": "🌅",
        "hours":  range(5, 12), "db_key": "aurora",
        "style":  "You are DJ Aurora, morning host of BazraGod Radio. Uplifting, motivational, sunrise vibes. Keep commentary under 2 sentences.",
        "intros": [
            "Good morning Parish 14. DJ Aurora on the frequency. Let's rise.",
            "The sun is up. BazraGod Radio morning session. DJ Aurora in control.",
        ],
    },
    "colorred": {
        "name":   "DJ Color Red",  "emoji": "🔴",
        "hours":  range(12, 18),   "db_key": "colorred",
        "style":  "You are DJ Color Red, afternoon hype host of BazraGod Radio. High energy, street culture. Keep commentary under 2 sentences.",
        "intros": [
            "Afternoon session live. DJ Color Red on the dial. Turn it up.",
            "Midday heat. BazraGod Radio. DJ Color Red taking no prisoners.",
        ],
    },
    "maximus": {
        "name":   "DJ Maximus",  "emoji": "👑",
        "hours":  range(18, 24), "db_key": "maximus",
        "style":  "You are DJ Maximus, prime time commander of BazraGod Radio. Sovereign, deep, authoritative. Keep commentary under 2 sentences.",
        "intros": [
            "Prime time. DJ Maximus commanding the airwaves. Parish 14 Nation.",
            "The sovereign hour begins. DJ Maximus. BazraGod Radio.",
        ],
    },
    "eclipse": {
        "name":   "DJ Eclipse",  "emoji": "🌑",
        "hours":  range(0, 5),   "db_key": "eclipse",
        "style":  "You are DJ Eclipse, late night host of BazraGod Radio. Deep, mysterious, cinematic. Keep commentary under 2 sentences.",
        "intros": [
            "Late night. DJ Eclipse in the dark. BazraGod Radio never sleeps.",
            "Past midnight. The real ones are awake. DJ Eclipse.",
        ],
    },
}

DJ_TRANSITIONS = [
    "That was heavy. Parish 14 stays winning.",
    "Keep it locked. BazraGod Radio never sleeps.",
    "You are listening to the sovereign frequency.",
    "Only real ones tuned in right now.",
    "Parish 14 worldwide. Stay with us.",
    "No label. No limit. Just the music.",
    "BazraGod built this from nothing. That is power.",
    "This is what independence sounds like.",
]

STATION_IDS = [
    "BazraGod Radio. Parish 14 Nation. Independent music lives here.",
    "You are tuned in to BazraGod Radio. I.A.A.I.M.O. No label. No limit.",
    "This is BazraGod Radio. The sovereign station. Parish 14 worldwide.",
]

AD_MESSAGES = [
    "📢 Support independent music. Tap 💰 Support Artist in the menu.",
    "📢 Parish 14 merch available now. Rep the nation. Tap 👕 Parish 14.",
    "📢 Become a Supporter for $19.99/mo. Tap 💎 Supporter.",
    "📢 Invite friends to grow the army. Tap 👥 Refer a Friend.",
    f"📢 Book BAZRAGOD for your event. {BOOKING_EMAIL}",
    "📢 Stream BAZRAGOD on Spotify. Search BAZRAGOD.",
]

def get_current_dj() -> dict:
    hour = datetime.now().hour
    for key, dj in DJS.items():
        if hour in dj["hours"]:
            return dj
    return DJS["maximus"]

# ╔══════════════════════════════════════════════════════════════╗
# ║       📻 PLAYLIST ENGINE (ordered + ad breaks)               ║
# ╚══════════════════════════════════════════════════════════════╝

# Per-user playlist index for in-chat radio
USER_PLAYLIST_INDEX: dict = {}

# Per-user last DJ announce timestamp
RADIO_LAST_ANNOUNCE: dict = {}


def get_playlist_from_db() -> list:
    """
    Returns ordered playlist from DB.
    Inserts an AD_BREAK slot every 4 songs.
    Structure: [{"type": "song"|"ad", "title": str, "file_id": str|None}, ...]
    """
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT title, file_id FROM songs ORDER BY id"
        )
        songs = cur.fetchall()
    finally:
        release_db(conn)

    playlist = []
    for i, (title, file_id) in enumerate(songs):
        playlist.append({"type": "song", "title": title, "file_id": file_id})
        if (i + 1) % 4 == 0:
            playlist.append({"type": "ad", "title": "AD_BREAK", "file_id": None})

    return playlist


def get_next_playlist_item(uid: int) -> dict:
    """Return next item for this user and advance their index."""
    playlist = get_playlist_from_db()
    if not playlist:
        return {"type": "empty", "title": "", "file_id": None}

    idx = USER_PLAYLIST_INDEX.get(uid, 0)
    if idx >= len(playlist):
        idx = 0

    item = playlist[idx]
    USER_PLAYLIST_INDEX[uid] = idx + 1
    return item

# ╔══════════════════════════════════════════════════════════════╗
# ║       📻 24/7 CHANNEL RADIO LOOP                             ║
# ╚══════════════════════════════════════════════════════════════╝

radio_loop_running = False


async def channel_radio_loop():
    """
    Continuously broadcasts to RADIO_CHANNEL_ID.
    Runs as background task from main startup.
    """
    global radio_loop_running
    if radio_loop_running:
        return
    radio_loop_running = True

    if not RADIO_CHANNEL_ID:
        print("RADIO_CHANNEL_ID not set — channel radio loop skipped.")
        radio_loop_running = False
        return

    channel_id = int(RADIO_CHANNEL_ID)
    playlist_index = 0
    print(f"📻 Channel radio loop started → {channel_id}")

    while True:
        try:
            playlist = get_playlist_from_db()
            if not playlist:
                await asyncio.sleep(30)
                continue

            if playlist_index >= len(playlist):
                playlist_index = 0

            item = playlist[playlist_index]
            playlist_index += 1

            dj  = get_current_dj()
            now = datetime.now().strftime("%I:%M %p")

            if item["type"] == "ad":
                ad_text = random.choice(AD_MESSAGES)
                await telegram_app.bot.send_message(
                    chat_id=channel_id,
                    text=(
                        f"📻 {dj['emoji']} BazraGod Radio — {now}\n\n"
                        f"{ad_text}\n\n"
                        f"t.me/{BOT_USERNAME}"
                    ),
                )
                await asyncio.sleep(RADIO_AD_DELAY)

            elif item["type"] == "song" and item["file_id"]:
                conn = get_db()
                cur  = conn.cursor()
                try:
                    cur.execute(
                        "UPDATE songs SET plays = plays + 1 WHERE title = %s",
                        (item["title"],),
                    )
                    cur.execute(
                        "SELECT plays, likes, donations FROM songs WHERE title = %s",
                        (item["title"],),
                    )
                    row = cur.fetchone()
                    conn.commit()
                finally:
                    release_db(conn)

                plays     = row[0] if row else 0
                likes     = row[1] if row else 0
                donations = row[2] if row else 0
                heat      = calculate_heat(likes, donations, plays)

                await telegram_app.bot.send_audio(
                    chat_id=channel_id,
                    audio=item["file_id"],
                    caption=(
                        f"📻 {dj['emoji']} BazraGod Radio — {now}\n\n"
                        f"🎵 {item['title']}\n"
                        f"BAZRAGOD\n\n"
                        f"{heat}  {plays:,} plays\n\n"
                        f"Join the nation: t.me/{BOT_USERNAME}"
                    ),
                )
                await asyncio.sleep(RADIO_SONG_DELAY)

        except Exception as e:
            print(f"Channel radio loop error: {e}")
            await asyncio.sleep(15)

# ╔══════════════════════════════════════════════════════════════╗
# ║                🔥 HEAT ENGINE                                ║
# ╚══════════════════════════════════════════════════════════════╝

def calculate_heat(likes: int, donations: int, plays: int) -> str:
    score = (likes * 5) + (donations * 10) + (plays / 1000)
    if score >= 250: return "🔥🔥🔥🔥🔥"
    if score >= 100: return "🔥🔥🔥🔥"
    if score >=  50: return "🔥🔥🔥"
    if score >=  10: return "🔥🔥"
    return "🔥"

def auto_classify_rotation():
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, plays, likes, donations FROM songs")
        songs = cur.fetchall()
        for sid, plays, likes, donations in songs:
            score = (plays / 1000.0) + (likes * 5) + (donations * 10)
            rotation = "A" if score > 1000 else "B" if score > 500 else "C"
            cur.execute("UPDATE songs SET rotation = %s WHERE id = %s", (rotation, sid))
        conn.commit()
    except Exception as e:
        print(f"Rotation error: {e}")
    finally:
        release_db(conn)

# ╔══════════════════════════════════════════════════════════════╗
# ║                   POINTS + RANKS                             ║
# ╚══════════════════════════════════════════════════════════════╝

POINTS = {
    "start": 5, "play_song": 8, "play_beat": 6, "radio": 10,
    "share_location": 15, "follow_social": 3, "support_artist": 5,
    "invite_friend": 20, "wisdom": 3, "fitness": 3, "ai_chat": 2,
    "mission": 100, "astro": 25, "cipher": 15, "mood_radio": 10,
    "voice_wall": 20, "like_song": 3, "supporter_sub": 50,
    "request_song": 3, "charity": 10, "donate_song": 10,
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

STORE_ITEMS = {
    "single":    ("Single Song Download",    5),
    "bundle":    ("Bundle — 7 Songs",       20),
    "exclusive": ("Exclusive Album — VIP", 500),
}

MERCH_ITEMS = {
    "tshirt":   ("Parish 14 T-Shirt",   50),
    "pullover": ("Parish 14 Pullover", 150),
}

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
    "Request a track using 📀 Request Track",
    "Make a $1 charity donation",
]

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
    "The obstacle is the way.",
    "A lion does not concern himself with the opinions of sheep.",
    "Kings are not born — they are made through discipline.",
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

pending_broadcasts: dict = {}
astro_sessions:     dict = {}
mood_sessions:      dict = {}
cipher_sessions:    dict = {}
upload_sessions:    dict = {}
request_sessions:   dict = {}

# ╔══════════════════════════════════════════════════════════════╗
# ║                     DATABASE                                 ║
# ╚══════════════════════════════════════════════════════════════╝

def init_db():
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fans (
                telegram_id       BIGINT PRIMARY KEY,
                username          TEXT,
                points            INT DEFAULT 0,
                invites           INT DEFAULT 0,
                referrer_id       BIGINT,
                tier              TEXT DEFAULT '🎧 Fan',
                city              TEXT,
                country           TEXT,
                is_supporter      BOOLEAN DEFAULT FALSE,
                supporter_expires DATE,
                prophecy_tiers    TEXT DEFAULT '',
                language          TEXT DEFAULT 'en',
                joined_at         TIMESTAMP DEFAULT NOW()
            )
        """)
        for col, defn in [
            ("prophecy_tiers",    "TEXT DEFAULT ''"),
            ("is_supporter",      "BOOLEAN DEFAULT FALSE"),
            ("supporter_expires", "DATE"),
            ("language",          "TEXT DEFAULT 'en'"),
        ]:
            cur.execute(f"ALTER TABLE fans ADD COLUMN IF NOT EXISTS {col} {defn}")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id          SERIAL PRIMARY KEY,
                title       TEXT UNIQUE,
                file_id     TEXT,
                plays       INTEGER DEFAULT 30000,
                likes       INTEGER DEFAULT 0,
                donations   INTEGER DEFAULT 0,
                rotation    TEXT DEFAULT 'C',
                uploaded_at TIMESTAMP DEFAULT NOW()
            )
        """)
        for col, defn in [
            ("plays",     "INTEGER DEFAULT 30000"),
            ("likes",     "INTEGER DEFAULT 0"),
            ("donations", "INTEGER DEFAULT 0"),
            ("rotation",  "TEXT DEFAULT 'C'"),
        ]:
            cur.execute(f"ALTER TABLE songs ADD COLUMN IF NOT EXISTS {col} {defn}")

        for tbl in [
            "CREATE TABLE IF NOT EXISTS beats (id SERIAL PRIMARY KEY, title TEXT, file_id TEXT, uploaded_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS drops (id SERIAL PRIMARY KEY, title TEXT, file_id TEXT, uploaded_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS announcements (id SERIAL PRIMARY KEY, title TEXT, file_id TEXT, uploaded_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS promos (id SERIAL PRIMARY KEY, title TEXT, file_id TEXT, uploaded_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS radio_promos (id SERIAL PRIMARY KEY, text TEXT)",
            "CREATE TABLE IF NOT EXISTS dj_drops (id SERIAL PRIMARY KEY, dj TEXT, title TEXT, file_id TEXT, uploaded_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS fan_locations (telegram_id BIGINT PRIMARY KEY, city TEXT, country TEXT, latitude FLOAT, longitude FLOAT, updated_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS point_log (id SERIAL PRIMARY KEY, telegram_id BIGINT, action TEXT, pts INT, logged_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS missions (telegram_id BIGINT, mission_date DATE, completed BOOLEAN DEFAULT FALSE, PRIMARY KEY (telegram_id, mission_date))",
            "CREATE TABLE IF NOT EXISTS purchases (id SERIAL PRIMARY KEY, telegram_id BIGINT, item TEXT, price FLOAT, status TEXT DEFAULT 'pending', purchased_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS astro_profiles (telegram_id BIGINT PRIMARY KEY, birth_date TEXT, birth_time TEXT, birth_city TEXT, current_city TEXT, last_reading TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS voice_wall (id SERIAL PRIMARY KEY, telegram_id BIGINT, username TEXT, file_id TEXT, status TEXT DEFAULT 'pending', submitted_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS song_likes (telegram_id BIGINT, song_id INT, PRIMARY KEY (telegram_id, song_id))",
            "CREATE TABLE IF NOT EXISTS song_requests (id SERIAL PRIMARY KEY, telegram_id BIGINT, username TEXT, song_title TEXT, played BOOLEAN DEFAULT FALSE, requested_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS radio_sessions (telegram_id BIGINT PRIMARY KEY, joined_at TIMESTAMP DEFAULT NOW(), last_ping TIMESTAMP DEFAULT NOW())",
        ]:
            cur.execute(tbl)

        # Seed songs only if table is empty
        cur.execute("SELECT COUNT(*) FROM songs")
        if cur.fetchone()[0] == 0:
            for title, file_id in SEED_SONGS:
                cur.execute(
                    "INSERT INTO songs (title, file_id) VALUES (%s, %s) ON CONFLICT (title) DO NOTHING",
                    (title, file_id),
                )

        conn.commit()
        print("I.A.A.I.M.O DATABASE READY — v13.000")
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


def get_user_lang(uid: int) -> str:
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT language FROM fans WHERE telegram_id = %s", (uid,))
        row = cur.fetchone()
        return row[0] if row and row[0] else "en"
    finally:
        release_db(conn)


def set_user_lang(uid: int, lang: str):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("UPDATE fans SET language = %s WHERE telegram_id = %s", (lang, uid))
        conn.commit()
    finally:
        release_db(conn)


def check_supporter_expiry():
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            UPDATE fans SET is_supporter = FALSE
            WHERE is_supporter = TRUE
              AND supporter_expires IS NOT NULL
              AND supporter_expires < CURRENT_DATE
        """)
        conn.commit()
    finally:
        release_db(conn)


def update_listener(uid: int):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO radio_sessions (telegram_id, joined_at, last_ping)
            VALUES (%s, NOW(), NOW())
            ON CONFLICT (telegram_id) DO UPDATE SET last_ping = NOW()
        """, (uid,))
        conn.commit()
    finally:
        release_db(conn)


def get_listener_count() -> int:
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*) FROM radio_sessions
            WHERE last_ping > NOW() - INTERVAL '30 minutes'
        """)
        return cur.fetchone()[0]
    finally:
        release_db(conn)

# ╔══════════════════════════════════════════════════════════════╗
# ║                       MENUS                                  ║
# ╚══════════════════════════════════════════════════════════════╝

main_menu = ReplyKeyboardMarkup(
    [
        ["🎧 BAZRAGOD MUSIC",  "📻 BazraGod Radio"],
        ["🧠 Mood Radio",      "⚔️ Lyric Cipher"],
        ["📊 Top Charts",      "🔥 Trending"],
        ["📀 Request Track",   "💎 Supporter"],
        ["💝 Charity",         "📈 Song Stats"],
        ["🥁 Beats",           "🎤 Drops"],
        ["🏆 Leaderboard",     "⭐ My Points"],
        ["👤 My Profile",      "🎯 Daily Mission"],
        ["💰 Support Artist",  "🌐 Social"],
        ["🛒 Music Store",     "👕 Parish 14"],
        ["👑 Wisdom",          "🏋 Fitness"],
        ["📍 Share Location",  "👥 Refer a Friend"],
        ["📡 Fan Radar",       "📅 Booking"],
        ["🎙️ Voice Wall",      "🪐 Astro Reading"],
        ["🌍 Language",        "🤖 MAXIMUS AI"],
    ],
    resize_keyboard=True,
)

def get_username(update: Update) -> str:
    u = update.effective_user
    return u.username or u.first_name or str(u.id)

def is_admin(uid: int) -> bool:
    return uid == OWNER_ID

def lang_selector_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=f"lang:{code}")]
        for code, label in SUPPORTED_LANGUAGES.items()
    ])

# ╔══════════════════════════════════════════════════════════════╗
# ║                  VOICE ENGINE                                ║
# ╚══════════════════════════════════════════════════════════════╝

async def maximus_speak(context, chat_id: int, text: str):
    if not openai_client:
        return
    try:
        response   = openai_client.audio.speech.create(
            model="tts-1", voice="onyx", input=text[:500], speed=0.95,
        )
        buf = BytesIO(response.content)
        buf.name = "maximus.ogg"
        await context.bot.send_voice(chat_id=chat_id, voice=buf)
    except Exception as e:
        print(f"Voice error: {e}")


async def maximus_speak_direct(bot, chat_id: int, text: str):
    if not openai_client:
        return
    try:
        response   = openai_client.audio.speech.create(
            model="tts-1", voice="onyx", input=text[:500], speed=0.95,
        )
        buf = BytesIO(response.content)
        buf.name = "maximus.ogg"
        await bot.send_voice(chat_id=chat_id, voice=buf)
    except Exception as e:
        print(f"Voice direct error: {e}")


async def dj_speak(context, chat_id: int, text: str):
    """Fires TTS max once per 15 minutes per user."""
    now  = datetime.now()
    last = RADIO_LAST_ANNOUNCE.get(chat_id)
    if last and (now - last) < timedelta(minutes=15):
        return
    RADIO_LAST_ANNOUNCE[chat_id] = now
    if not openai_client:
        return
    try:
        response   = openai_client.audio.speech.create(
            model="tts-1", voice="onyx", input=text[:500], speed=0.92,
        )
        buf = BytesIO(response.content)
        buf.name = "dj.ogg"
        await context.bot.send_voice(chat_id=chat_id, voice=buf)
    except Exception as e:
        print(f"DJ voice error: {e}")


async def generate_dj_line(dj: dict, song_title: str = None, action: str = "intro") -> str:
    if not openai_client:
        return random.choice(dj["intros"])
    try:
        if action == "intro" and song_title:
            prompt = f"Introduce the next track '{song_title}' by BAZRAGOD in 1-2 sentences."
        elif action == "commentary" and song_title:
            prompt = f"Give a 1-2 sentence DJ commentary about '{song_title}' by BAZRAGOD."
        else:
            return random.choice(dj["intros"])
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": dj["style"]},
                {"role": "user",   "content": prompt},
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
            "SELECT points, tier, prophecy_tiers FROM fans WHERE telegram_id = %s", (uid,)
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
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": AI_SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Fan: {name_display}\nRank: {tier}\nPoints: {points}\n\n"
                    f"Write a personal sovereign prophecy for this fan who just reached {tier}. "
                    f"4 sentences max. Make them feel chosen. End with their rank in capitals."
                )},
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
# ║                🌍 LANGUAGE HANDLERS                          ║
# ╚══════════════════════════════════════════════════════════════╝

async def language_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_user_lang(uid)
    await update.message.reply_text(
        t(lang, "select_lang"),
        reply_markup=lang_selector_kb(),
    )


async def lang_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        lang = query.data.split(":")[1]
    except Exception:
        return
    if lang not in SUPPORTED_LANGUAGES:
        return

    uid = query.from_user.id
    set_user_lang(uid, lang)
    lang_name = SUPPORTED_LANGUAGES[lang]

    # After language — show intro gate
    if INTRO_FILE_ID:
        await query.message.reply_text(
            f"{lang_name} {t(lang, 'lang_saved')}\n\n"
            f"👑 Before you enter — Press play. Real fans only. 🎙️"
        )
        await query.message.reply_voice(
            INTRO_FILE_ID,
            caption="🎙️ BAZRAGOD — The Vision\nI.A.A.I.M.O",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("▶️  Enter The Platform", callback_data="intro:play")
            ]]),
        )
    else:
        await query.message.reply_text(
            f"{lang_name} {t(lang, 'lang_saved')}\n\n{t(lang, 'welcome_inside')}",
            reply_markup=main_menu,
        )

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
                f"👥 New soldier joined your link!\n+{POINTS['invite_friend']} pts credited 🔥",
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

    # NEW FANS → language selector first
    if is_new:
        await update.message.reply_text(
            "🌍 PARISH 14 NETWORK\n\nSelect your language to enter:",
            reply_markup=lang_selector_kb(),
        )
    # RETURNING FANS → intro gate or menu
    elif INTRO_FILE_ID:
        await update.message.reply_text("👑 Welcome back. Press play. 🎙️")
        await update.message.reply_voice(
            INTRO_FILE_ID,
            caption="🎙️ BAZRAGOD — The Vision\nI.A.A.I.M.O",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("▶️  Enter The Platform", callback_data="intro:play")
            ]]),
        )
    else:
        await update.message.reply_text(
            f"🛸 WELCOME TO I.A.A.I.M.O\n\nParish 14 Nation\n\n+{pts} pts 🔥",
            reply_markup=main_menu,
        )


async def intro_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    lang = get_user_lang(uid)
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT points, tier FROM fans WHERE telegram_id = %s", (uid,))
        row = cur.fetchone()
    finally:
        release_db(conn)

    pts  = row[0] if row else 0
    tier = row[1] if row else "🎧 Fan"

    channel_line = ""
    if RADIO_CHANNEL_ID:
        channel_line = f"\n📻 Live Radio: t.me/c/{str(RADIO_CHANNEL_ID).replace('-100', '')}"

    await query.message.reply_text(
        f"{t(lang, 'welcome_inside')}\n\nRank:   {tier}\nPoints: {pts}"
        f"{channel_line}\n\nThe platform is yours. 👑",
        reply_markup=main_menu,
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║          📻 IN-CHAT RADIO (playlist + NEXT button)           ║
# ╚══════════════════════════════════════════════════════════════╝

async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)

    update_listener(uid)
    listeners = get_listener_count()
    pts       = award_points(uid, "radio", name)

    await _play_next_for_user(uid, name, pts, listeners, update.message, context)
    await maybe_prophecy(uid, name, context)


async def radio_next_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """▶ Next Track button callback."""
    query = update.callback_query
    await query.answer("Loading next track... 🎵")
    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name

    update_listener(uid)
    listeners = get_listener_count()
    pts       = award_points(uid, "radio", name)

    await _play_next_for_user(uid, name, pts, listeners, query.message, context)
    await maybe_prophecy(uid, name, context)


async def _play_next_for_user(uid, name, pts, listeners, msg, context):
    """Core: get next playlist item and send it."""
    item = get_next_playlist_item(uid)
    dj   = get_current_dj()
    now  = datetime.now().strftime("%I:%M %p")

    next_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("▶ Next Track", callback_data="radio:next"),
        InlineKeyboardButton("❤️ Like",       callback_data="like:0"),
    ]])

    if item["type"] == "empty":
        await msg.reply_text(
            "📻 Radio loading... Upload songs to the catalog first.",
            reply_markup=main_menu,
        )
        return

    if item["type"] == "ad":
        ad_text = random.choice(AD_MESSAGES)
        # Transition text only (no DJ voice spam for ads)
        await msg.reply_text(
            f"📻 {dj['emoji']} BazraGod Radio — {now}\n\n"
            f"{ad_text}\n\n"
            f"👥 {listeners} listeners tuned in",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("▶ Continue Radio", callback_data="radio:next")
            ]]),
        )
        return

    # Song
    title   = item["title"]
    file_id = item["file_id"]

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("UPDATE songs SET plays = plays + 1 WHERE title = %s", (title,))
        cur.execute(
            "SELECT id, plays, likes, donations, rotation FROM songs WHERE title = %s",
            (title,),
        )
        row = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)

    sid       = row[0] if row else 0
    plays     = (row[1] if row else 0)
    likes     = row[2] if row else 0
    donations = row[3] if row else 0
    rotation  = row[4] if row else "C"
    heat      = calculate_heat(likes, donations, plays)
    rot_badge = {"A": "🔴 Hot", "B": "🟡 Mid", "C": "🟢 Deep"}.get(rotation, "")

    dj_line = await generate_dj_line(dj, title, "intro")

    # Transition 25% of the time
    if random.random() < 0.25:
        await dj_speak(context, uid, random.choice(DJ_TRANSITIONS))

    await dj_speak(context, uid, dj_line)

    await msg.reply_audio(
        file_id,
        caption=(
            f"📻 {dj['emoji']} BazraGod Radio — {now}\n\n"
            f"🎵 {title}  {rot_badge}\n"
            f"BAZRAGOD\n\n"
            f"{heat}  {plays:,} plays  ❤️{likes}  💰{donations}\n\n"
            f"👥 {listeners} listeners tuned in\n\n"
            f"+{pts} pts 🔥"
        ),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("▶ Next Track",  callback_data="radio:next"),
            InlineKeyboardButton("❤️ Like",        callback_data=f"like:{sid}"),
            InlineKeyboardButton("💰 Donate",      callback_data=f"donate:{sid}"),
        ]]),
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
        cur.execute("SELECT id, title, plays, likes, donations FROM songs ORDER BY id")
        songs = cur.fetchall()
    finally:
        release_db(conn)

    lang = get_user_lang(uid)
    if not songs:
        await update.message.reply_text(t(lang, "no_songs"))
        return

    keyboard = [
        [InlineKeyboardButton(
            f"▶  {s[1]}  {calculate_heat(s[3], s[4], s[2])}",
            callback_data=f"song:{s[0]}"
        )]
        for s in songs
    ]
    await update.message.reply_text(
        f"🎧 BAZRAGOD CATALOG\nParish 14 Nation — {len(songs)} tracks\n\nSelect a track 👇",
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
        cur.execute(
            "SELECT title, file_id, plays, likes, donations FROM songs WHERE id = %s",
            (song_id,),
        )
        song = cur.fetchone()
        if song:
            cur.execute("UPDATE songs SET plays = plays + 1 WHERE id = %s", (song_id,))
            conn.commit()
    finally:
        release_db(conn)

    if song:
        title, file_id, plays, likes, donations = song
        plays += 1
        heat  = calculate_heat(likes, donations, plays)
        pts   = award_points(uid, "play_song", name)
        dj    = get_current_dj()
        line  = await generate_dj_line(dj, title, "intro")
        await dj_speak(context, uid, line)
        await query.message.reply_audio(
            file_id,
            caption=(
                f"🎵 {title}\nBAZRAGOD\n\n"
                f"{heat}  {plays:,} plays  ❤️{likes}  💰{donations}\n\n"
                f"+{pts} pts 🏆"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❤️ Like",   callback_data=f"like:{song_id}"),
                InlineKeyboardButton("💰 Donate", callback_data=f"donate:{song_id}"),
            ]]),
        )
        await maybe_prophecy(uid, name, context)

# ╔══════════════════════════════════════════════════════════════╗
# ║                ❤️ LIKE + 💰 DONATE                           ║
# ╚══════════════════════════════════════════════════════════════╝

async def like_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        song_id = int(query.data.split(":")[1])
    except Exception:
        await query.answer()
        return

    if song_id == 0:
        await query.answer("❤️ Tap a song from the catalog to like it!", show_alert=False)
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
            await query.answer("❤️ Liked! +3 pts", show_alert=False)
        else:
            await query.answer("Already liked 👑", show_alert=False)
    finally:
        release_db(conn)


async def donate_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        if song_id > 0:
            cur.execute("UPDATE songs SET donations = donations + 1 WHERE id = %s", (song_id,))
        cur.execute("SELECT SUM(donations) FROM songs")
        total_donations = cur.fetchone()[0] or 0
        conn.commit()
    finally:
        release_db(conn)

    award_points(uid, "donate_song", name)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 CashApp", url=CASHAPP)],
        [InlineKeyboardButton("💳 PayPal",  url=PAYPAL)],
    ])
    await query.message.reply_text(
        f"💰 SUPPORT THE ARTIST\n\nEvery donation powers independent music.\n"
        f"Parish 14 Nation. 👑\n\n+{POINTS['donate_song']} pts",
        reply_markup=keyboard,
    )

    if total_donations >= CHARITY_THRESHOLD:
        try:
            await context.bot.send_message(
                OWNER_ID,
                f"💝 CHARITY THRESHOLD REACHED!\n\nTotal: {total_donations}\n"
                f"${CHARITY_THRESHOLD} milestone hit! 👑",
            )
        except Exception:
            pass

# ╔══════════════════════════════════════════════════════════════╗
# ║                📊 CHARTS + STATS                             ║
# ╚══════════════════════════════════════════════════════════════╝

async def top_charts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Top Played",  callback_data="chart:played")],
        [InlineKeyboardButton("❤️ Most Liked",  callback_data="chart:liked")],
        [InlineKeyboardButton("📈 Trending",     callback_data="chart:trending")],
    ])
    dj = get_current_dj()
    await update.message.reply_text(
        f"📊 PARISH 14 CHARTS\n\n{dj['emoji']} {dj['name']} presents the charts.\n\nSelect 👇",
        reply_markup=keyboard,
    )


async def chart_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        chart_type = query.data.split(":")[1]
    except Exception:
        return

    conn = get_db()
    cur  = conn.cursor()
    try:
        if chart_type == "played":
            cur.execute("SELECT title, plays, likes, donations FROM songs ORDER BY plays DESC LIMIT 10")
            label = "🔥 TOP PLAYED"
        elif chart_type == "liked":
            cur.execute("SELECT title, plays, likes, donations FROM songs ORDER BY likes DESC LIMIT 10")
            label = "❤️ MOST LIKED"
        else:
            cur.execute("""
                SELECT title, plays, likes, donations
                FROM songs ORDER BY (plays/1000.0 + likes*5 + donations*10) DESC LIMIT 10
            """)
            label = "📈 TRENDING"
        songs = cur.fetchall()
    finally:
        release_db(conn)

    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    text   = f"📊 {label}\nParish 14 Nation\n\n"
    for i, (title, plays, likes, donations) in enumerate(songs):
        heat  = calculate_heat(likes, donations, plays)
        text += f"{medals[i]} {title}\n   {heat}  {plays:,} plays  ❤️{likes}  💰{donations}\n\n"
    await query.message.reply_text(text)


async def trending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT title, plays, likes, donations
            FROM songs ORDER BY (plays/1000.0 + likes*5 + donations*10) DESC LIMIT 10
        """)
        songs = cur.fetchall()
    finally:
        release_db(conn)
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    text   = "🔥 TRENDING ON PARISH 14\n\n"
    for i, (title, plays, likes, donations) in enumerate(songs):
        text += f"{medals[i]} {title}\n   {plays:,} plays  {calculate_heat(likes, donations, plays)}\n\n"
    await update.message.reply_text(text)


async def song_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT title, plays, likes, donations, rotation FROM songs ORDER BY plays DESC LIMIT 10")
        songs = cur.fetchall()
    finally:
        release_db(conn)
    rb   = {"A": "🔴 Hot", "B": "🟡 Mid", "C": "🟢 Deep"}
    text = "📈 SONG STATISTICS\n\n"
    for title, plays, likes, donations, rotation in songs:
        heat  = calculate_heat(likes, donations, plays)
        badge = rb.get(rotation, "")
        text += (
            f"🎵 {title}  {badge}\n"
            f"Plays: {plays:,}  Likes: {likes}  Donations: {donations}\n"
            f"Heat: {heat}\n\n"
        )
    await update.message.reply_text(text)

# ╔══════════════════════════════════════════════════════════════╗
# ║                  BEATS + DROPS                               ║
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
    keyboard = [[InlineKeyboardButton(f"🥁  {r[1]}", callback_data=f"beat:{r[0]}")] for r in rows]
    await update.message.reply_text(f"🥁 BAZRAGOD BEATS — {len(rows)} available", reply_markup=InlineKeyboardMarkup(keyboard))


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
    keyboard = [[InlineKeyboardButton(f"🎤  {r[1]}", callback_data=f"drop:{r[0]}")] for r in rows]
    await update.message.reply_text(f"🎤 RADIO DROPS — {len(rows)} available", reply_markup=InlineKeyboardMarkup(keyboard))


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
# ║                🧠 MOOD RADIO                                 ║
# ╚══════════════════════════════════════════════════════════════╝

async def mood_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mood_sessions[uid] = True
    await update.message.reply_text(
        "🧠 MOOD RADIO\n\nMAXIMUS reads your energy and selects\n"
        "the perfect BAZRAGOD track.\n\n"
        "How are you feeling right now?\n\nExamples:\n"
        "• motivated\n• reflective\n• focused\n• celebrating\n\nType your mood 👇"
    )


async def mood_radio_handler(uid: int, text: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if uid not in mood_sessions:
        return False
    mood_sessions.pop(uid)
    name = get_username(update)

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

    await update.message.reply_text(f"🧠 MAXIMUS reading your energy...\n\nMood: {text}")

    try:
        song_list = "\n".join([f"{s[0]}. {s[1]}" for s in songs])
        response  = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are MAXIMUS. Reply with ONLY the song ID number."},
                {"role": "user",   "content": f"Fan mood: {text}\n\nCatalog:\n{song_list}\n\nReply with only the song ID."},
            ],
            max_tokens=5,
        )
        song_id = int("".join(filter(str.isdigit, response.choices[0].message.content.strip())))
    except Exception:
        song_id = random.choice(songs)[0] if songs else 0

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, title, file_id, plays, likes, donations FROM songs WHERE id = %s", (song_id,))
        song = cur.fetchone()
        if not song:
            cur.execute("SELECT id, title, file_id, plays, likes, donations FROM songs ORDER BY RANDOM() LIMIT 1")
            song = cur.fetchone()
        if song:
            cur.execute("UPDATE songs SET plays = plays + 1 WHERE id = %s", (song[0],))
            conn.commit()
    finally:
        release_db(conn)

    if song:
        sid, title, file_id, plays, likes, donations = song
        pts  = award_points(uid, "mood_radio", name)
        heat = calculate_heat(likes, donations, plays)
        await dj_speak(context, uid, f"MAXIMUS has read your energy. You feel {text}. This track is for your soul. {title}. BAZRAGOD.")
        await update.message.reply_audio(
            file_id,
            caption=(
                f"🧠 MOOD RADIO\n\nYour energy: {text}\n"
                f"MAXIMUS selected: {title}\n"
                f"{heat}  {plays:,} plays\n\n+{pts} pts 🎵"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❤️ Like",   callback_data=f"like:{sid}"),
                InlineKeyboardButton("💰 Donate", callback_data=f"donate:{sid}"),
            ]]),
        )
        await maybe_prophecy(uid, name, context)
    return True

# ╔══════════════════════════════════════════════════════════════╗
# ║         ⚔️ LYRIC CIPHER                                      ║
# ╚══════════════════════════════════════════════════════════════╝

async def lyric_cipher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cipher_sessions[uid] = True
    await update.message.reply_text(
        "⚔️ LYRIC CIPHER\n\nYou vs MAXIMUS.\n\n"
        "Drop your verse below. MAXIMUS responds in BAZRAGOD's style.\n\n"
        "Write your bars 👇\n\nType /cancel to exit."
    )


async def cipher_handler(uid: int, text: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if uid not in cipher_sessions:
        return False
    cipher_sessions.pop(uid)
    name = get_username(update)
    await update.message.reply_text("⚔️ MAXIMUS is writing the response...")
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are MAXIMUS writing bars in BAZRAGOD's lyric style. Jamaican-influenced. Sovereign, confident, Patois influence, spiritual power. Exactly 4 bars. No explicit language."},
                {"role": "user", "content": f"Fan verse:\n{text}\n\nRespond with 4 bars in BAZRAGOD style."},
            ],
            max_tokens=200,
        )
        verse = response.choices[0].message.content
        pts   = award_points(uid, "cipher", name)
        await update.message.reply_text(
            f"⚔️ BAZRAGOD CIPHER\n{'═'*20}\n\nYou:\n{text}\n\nMAXIMUS:\n{verse}\n\n{'═'*20}\n+{pts} pts 🔥"
        )
        await maximus_speak(context, uid, verse)
        await maybe_prophecy(uid, name, context)
    except Exception as e:
        await update.message.reply_text(f"⚔️ Cipher error: {str(e)}")
    return True

# ╔══════════════════════════════════════════════════════════════╗
# ║                📀 SONG REQUEST SYSTEM                        ║
# ╚══════════════════════════════════════════════════════════════╝

async def request_track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    request_sessions[uid] = True
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT title FROM songs ORDER BY id")
        songs = cur.fetchall()
    finally:
        release_db(conn)
    song_list = "\n".join([f"• {s[0]}" for s in songs])
    await update.message.reply_text(
        f"📀 REQUEST A TRACK\n\nType the song name.\n\nAvailable:\n{song_list}\n\n"
        f"MAXIMUS will spin it on air. 🎙️\n\nType /cancel to go back."
    )


async def request_handler(uid: int, text: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if uid not in request_sessions:
        return False
    request_sessions.pop(uid)
    name = get_username(update)
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO song_requests (telegram_id, username, song_title) VALUES (%s, %s, %s) RETURNING id",
            (uid, name, text),
        )
        req_id = cur.fetchone()[0]
        conn.commit()
    finally:
        release_db(conn)
    pts = award_points(uid, "request_song", name)
    await update.message.reply_text(
        f"📀 REQUEST QUEUED!\n\nSong: {text}\nRequest #{req_id}\n\n"
        f"MAXIMUS will spin it on air. 🎙️\n\n+{pts} pts 🔥",
        reply_markup=main_menu,
    )
    return True

# ╔══════════════════════════════════════════════════════════════╗
# ║         💝 CHARITY                                           ║
# ╚══════════════════════════════════════════════════════════════╝

async def charity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT SUM(donations) FROM songs")
        total = cur.fetchone()[0] or 0
    finally:
        release_db(conn)
    progress = min(total, CHARITY_THRESHOLD)
    filled   = int((progress / CHARITY_THRESHOLD) * 10)
    bar      = "█" * filled + "░" * (10 - filled)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💵 Donate ${CHARITY_PRICE:.2f} via CashApp", url=CASHAPP)],
        [InlineKeyboardButton(f"💳 Donate ${CHARITY_PRICE:.2f} via PayPal",  url=PAYPAL)],
        [InlineKeyboardButton("✅ I've Donated", callback_data="charity:confirm")],
    ])
    await update.message.reply_text(
        f"💝 PARISH 14 CHARITY FUND\n\n"
        f"Progress to ${CHARITY_THRESHOLD} milestone:\n"
        f"[{bar}] {progress}/{CHARITY_THRESHOLD}\n\n"
        f"Every donation powers the movement.\n\nPay then tap below 👇",
        reply_markup=keyboard,
    )


async def charity_confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name
    pts  = award_points(uid, "charity", name)
    await query.message.reply_text(
        f"💝 THANK YOU!\n\nYour contribution supports independent music.\nParish 14 Nation appreciates you. 👑\n\n+{pts} pts 🔥"
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║                💎 SUPPORTER TIER                             ║
# ╚══════════════════════════════════════════════════════════════╝

async def supporter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT is_supporter, supporter_expires FROM fans WHERE telegram_id = %s", (uid,))
        row = cur.fetchone()
    finally:
        release_db(conn)
    is_sup  = row[0] if row else False
    sup_exp = row[1] if row else None
    if is_sup:
        exp_str = sup_exp.strftime("%B %d, %Y") if sup_exp else "Active"
        await update.message.reply_text(
            f"💎 PARISH 14 SUPPORTER\n\n✅ Active!\nExpires: {exp_str}\n\n"
            f"Benefits:\n🌍 Nation Elite badge\n📻 Priority radio shoutouts\n"
            f"🎧 Early access songs\n👑 Leaderboard priority\n\nThank you. 👑"
        )
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💵 Pay CashApp — ${SUPPORTER_PRICE:.2f}/mo", url=CASHAPP)],
        [InlineKeyboardButton(f"💳 Pay PayPal — ${SUPPORTER_PRICE:.2f}/mo",  url=PAYPAL)],
        [InlineKeyboardButton("✅ I've Paid — Activate Me", callback_data="supporter:verify")],
    ])
    await update.message.reply_text(
        f"💎 PARISH 14 SUPPORTER\n\n${SUPPORTER_PRICE:.2f}/month\n\n"
        f"Benefits:\n🌍 Nation Elite badge\n📻 Priority radio shoutouts\n"
        f"🎧 Early access songs\n👑 Leaderboard priority\n\nPay then tap below 👇",
        reply_markup=keyboard,
    )


async def supporter_verify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name
    await query.message.reply_text("💎 Payment submitted. Admin will activate your status. 👑")
    try:
        await context.bot.send_message(OWNER_ID, f"💎 SUPPORTER REQUEST\nFan: @{name} ({uid})\n\n/activate_supporter {uid}")
    except Exception:
        pass


async def activate_supporter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /activate_supporter <telegram_id>")
        return
    fan_id  = int(args[0])
    expires = date.today() + timedelta(days=30)
    conn    = get_db()
    cur     = conn.cursor()
    try:
        cur.execute(
            "UPDATE fans SET is_supporter = TRUE, tier = '🌍  Nation Elite', supporter_expires = %s "
            "WHERE telegram_id = %s RETURNING username",
            (expires, fan_id),
        )
        row = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)
    if row:
        award_points(fan_id, "supporter_sub")
        await update.message.reply_text(f"✅ @{row[0]} activated 💎 Expires: {expires}")
        try:
            await context.bot.send_message(
                fan_id,
                f"💎 PARISH 14 SUPPORTER ACTIVATED!\n\n🌍 Nation Elite unlocked.\nExpires: {expires.strftime('%B %d, %Y')}\n\nBAZRAGOD sees you. 👑",
            )
        except Exception:
            pass
    else:
        await update.message.reply_text("Fan not found.")

# ╔══════════════════════════════════════════════════════════════╗
# ║         🎙️ FAN VOICE WALL                                    ║
# ╚══════════════════════════════════════════════════════════════╝

async def voice_wall_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["voice_wall_active"] = True
    await update.message.reply_text(
        "🎙️ FAN VOICE WALL\n\nRecord a voice message and send it here.\n\n"
        "Approved shoutouts play LIVE on BazraGod Radio! 🔥\n\n"
        "Tips:\n• Shout out BAZRAGOD\n• Say your city\n• Big up Parish 14 Nation\n• Under 30 seconds\n\n"
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
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO voice_wall (telegram_id, username, file_id) VALUES (%s, %s, %s) RETURNING id",
            (uid, name, voice.file_id),
        )
        sid = cur.fetchone()[0]
        conn.commit()
    finally:
        release_db(conn)
    pts = award_points(uid, "voice_wall", name)
    await update.message.reply_text(
        f"🎙️ Submission #{sid} received!\nApproved voices play on BazraGod Radio. 🔥\n\n+{pts} pts 👑",
        reply_markup=main_menu,
    )
    try:
        await context.bot.send_message(OWNER_ID, f"🎙️ VOICE #{sid}\nFan: @{name} ({uid})\n/approve_voice {sid}\n/reject_voice {sid}")
        await context.bot.forward_message(chat_id=OWNER_ID, from_chat_id=uid, message_id=update.message.message_id)
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
        cur.execute("UPDATE voice_wall SET status = 'approved' WHERE id = %s RETURNING telegram_id, username", (vid,))
        row = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)
    if row:
        await update.message.reply_text(f"✅ Voice #{vid} approved. Goes live on radio. 🎙️")
        try:
            await context.bot.send_message(row[0], "🎙️ YOUR VOICE WAS APPROVED!\nIt plays live on BazraGod Radio. 🔥\nParish 14. 👑")
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
        cur.execute("SELECT id, username, status, submitted_at FROM voice_wall ORDER BY id DESC LIMIT 20")
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
# ║      🎚️ SMART AUDIO UPLOAD CLASSIFICATION                    ║
# ╚══════════════════════════════════════════════════════════════╝

async def handle_audio_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    audio = update.message.audio
    if not audio:
        return

    title = (
        audio.title
        or audio.file_name
        or (update.message.caption or "").strip()
        or "Untitled Track"
    )
    file_id = audio.file_id
    caption = (update.message.caption or "").strip().lower()

    tag_map = {
        "#song":     ("songs",         "🎵 Song"),
        "#beat":     ("beats",         "🥁 Beat"),
        "#drop":     ("drops",         "🎤 Drop"),
        "#promo":    ("promos",        "📻 Audio Promo"),
        "#announce": ("announcements", "📢 Announcement"),
        "#aurora":   ("dj:aurora",     "🌅 DJ Aurora Drop"),
        "#colorred": ("dj:colorred",   "🔴 DJ Color Red Drop"),
        "#maximus":  ("dj:maximus",    "👑 DJ Maximus Drop"),
        "#eclipse":  ("dj:eclipse",    "🌑 DJ Eclipse Drop"),
    }
    for tag, (dest, label) in tag_map.items():
        if tag in caption:
            await _save_classified_audio(update.message, file_id, title, dest, label)
            return

    upload_sessions[uid] = {"file_id": file_id, "title": title}
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 Song",              callback_data="upload:songs")],
        [InlineKeyboardButton("🥁 Beat",              callback_data="upload:beats")],
        [InlineKeyboardButton("🎤 Drop (General)",    callback_data="upload:drops")],
        [InlineKeyboardButton("📻 Audio Promo",       callback_data="upload:promos")],
        [InlineKeyboardButton("📢 Announcement",      callback_data="upload:announcements")],
        [InlineKeyboardButton("🌅 DJ Aurora Drop",    callback_data="upload:dj:aurora")],
        [InlineKeyboardButton("🔴 DJ Color Red Drop", callback_data="upload:dj:colorred")],
        [InlineKeyboardButton("👑 DJ Maximus Drop",   callback_data="upload:dj:maximus")],
        [InlineKeyboardButton("🌑 DJ Eclipse Drop",   callback_data="upload:dj:eclipse")],
    ])
    await update.message.reply_text(
        f"🎚️ CLASSIFY UPLOAD\n\nTitle: {title}\n\nWhat type is this audio?",
        reply_markup=keyboard,
    )


async def upload_classify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    if not is_admin(uid):
        return
    try:
        dest = ":".join(query.data.split(":")[1:])
    except Exception:
        return
    session = upload_sessions.pop(uid, None)
    if not session:
        await query.message.reply_text("Session expired. Send the file again.")
        return
    label_map = {
        "songs": "🎵 Song", "beats": "🥁 Beat", "drops": "🎤 Drop",
        "promos": "📻 Audio Promo", "announcements": "📢 Announcement",
        "dj:aurora": "🌅 DJ Aurora", "dj:colorred": "🔴 DJ Color Red",
        "dj:maximus": "👑 DJ Maximus", "dj:eclipse": "🌑 DJ Eclipse",
    }
    await _save_classified_audio(query.message, session["file_id"], session["title"], dest, label_map.get(dest, "✅"))


async def _save_classified_audio(msg, file_id: str, title: str, dest: str, label: str):
    conn = get_db()
    cur  = conn.cursor()
    try:
        if dest.startswith("dj:"):
            dj_key = dest.split(":")[1]
            cur.execute("INSERT INTO dj_drops (dj, title, file_id) VALUES (%s, %s, %s) RETURNING id", (dj_key, title, file_id))
            new_id = cur.fetchone()[0]; conn.commit()
            text = f"✅ {label} added. ID: {new_id}\nTitle: {title}"

        elif dest == "songs":
            cur.execute("SELECT id FROM songs WHERE LOWER(title) = LOWER(%s)", (title,))
            if cur.fetchone():
                text = f"⚠️ Song '{title}' already exists. Upload skipped."
            else:
                cur.execute("INSERT INTO songs (title, file_id) VALUES (%s, %s) RETURNING id", (title, file_id))
                new_id = cur.fetchone()[0]; conn.commit()
                text = f"✅ {label} added. ID: {new_id}\nTitle: {title}"

        else:
            cur.execute(f"INSERT INTO {dest} (title, file_id) VALUES (%s, %s) RETURNING id", (title, file_id))
            new_id = cur.fetchone()[0]; conn.commit()
            text = f"✅ {label} added. ID: {new_id}\nTitle: {title}"

    finally:
        release_db(conn)

    await msg.reply_text(text)

# ╔══════════════════════════════════════════════════════════════╗
# ║         📺 YOUTUBE DETECTION                                 ║
# ╚══════════════════════════════════════════════════════════════╝

async def youtube_detector(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    text = update.message.text or ""
    if not re.search(r"youtube\.com|youtu\.be", text):
        return False
    dj  = get_current_dj()
    now = datetime.now().strftime("%I:%M %p")
    msg = (
        f"📺 NEW BAZRAGOD VIDEO DETECTED\n\n"
        f"🔥 {dj['emoji']} {dj['name']} — {now}\n\n"
        f"New BAZRAGOD video just landed. Go watch it NOW. 🛸\n\n{text}"
    )
    await dj_speak(context, update.effective_user.id, "Attention Parish 14 Nation. New BAZRAGOD video dropped. Go watch it now.")
    await update.message.reply_text(msg)
    try:
        await _broadcast_to_all(context, msg)
    except Exception:
        pass
    return True

# ╔══════════════════════════════════════════════════════════════╗
# ║                  SOCIAL + SUPPORT                            ║
# ╚══════════════════════════════════════════════════════════════╝

async def social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    pts  = award_points(uid, "follow_social", name)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(p, url=u)] for p, u in SOCIALS.items()])
    await update.message.reply_text(f"🌐 BAZRAGOD SOCIAL\n\nFollow on every platform. 🔥\n\n+{pts} pts", reply_markup=keyboard)


async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    pts  = award_points(uid, "support_artist", name)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💵 CashApp", url=CASHAPP)], [InlineKeyboardButton("💳 PayPal", url=PAYPAL)]])
    await update.message.reply_text(f"💰 SUPPORT BAZRAGOD\n\nNo label takes a cut here.\nEvery dollar goes directly to the music.\n\n+{pts} pts 👑", reply_markup=keyboard)

# ╔══════════════════════════════════════════════════════════════╗
# ║                  MERCH + MUSIC STORE                         ║
# ╚══════════════════════════════════════════════════════════════╝

async def merch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👕 {MERCH_ITEMS['tshirt'][0]} — ${MERCH_ITEMS['tshirt'][1]}", callback_data="merch:tshirt")],
        [InlineKeyboardButton(f"🧥 {MERCH_ITEMS['pullover'][0]} — ${MERCH_ITEMS['pullover'][1]}", callback_data="merch:pullover")],
    ])
    await update.message.reply_text("👕 PARISH 14 MERCH\n\nOfficial BAZRAGOD clothing.\nWear the nation. 👇", reply_markup=keyboard)


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
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💵 Pay via CashApp", url=CASHAPP)], [InlineKeyboardButton("💳 Pay via PayPal", url=PAYPAL)]])
    await query.message.reply_text(
        f"👕 PARISH 14 ORDER\n\nItem:  {item_name}\nPrice: ${price}\n\nAfter payment send admin:\n• Your size\n• Shipping address\n• Payment proof\n\nParish 14. 👑",
        reply_markup=keyboard,
    )


async def music_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🎵 {STORE_ITEMS['single'][0]} — ${STORE_ITEMS['single'][1]}", callback_data="store:single")],
        [InlineKeyboardButton(f"📦 {STORE_ITEMS['bundle'][0]} — ${STORE_ITEMS['bundle'][1]}", callback_data="store:bundle")],
        [InlineKeyboardButton(f"👑 {STORE_ITEMS['exclusive'][0]} — ${STORE_ITEMS['exclusive'][1]}", callback_data="store:exclusive")],
    ])
    await update.message.reply_text("🛒 BAZRAGOD MUSIC STORE\n\nDirect from the artist.\nNo streaming cuts. No label fees. 👇", reply_markup=keyboard)


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
        cur.execute("INSERT INTO purchases (telegram_id, item, price) VALUES (%s, %s, %s) RETURNING id", (uid, item_name, price))
        purchase_id = cur.fetchone()[0]; conn.commit()
    finally:
        release_db(conn)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💵 Pay via CashApp", url=CASHAPP)], [InlineKeyboardButton("💳 Pay via PayPal", url=PAYPAL)]])
    await query.message.reply_text(f"🛒 ORDER #{purchase_id}\n\nItem:  {item_name}\nPrice: ${price}\n\nSend payment then message admin with proof.\nDownload unlocked. 🔐", reply_markup=keyboard)
    try:
        await context.bot.send_message(OWNER_ID, f"💰 NEW PURCHASE\n\nOrder: #{purchase_id}\nFan: @{name} ({uid})\nItem: {item_name}\nPrice: ${price}")
    except Exception:
        pass

# ╔══════════════════════════════════════════════════════════════╗
# ║                  BOOKING + FAN RADAR                         ║
# ╚══════════════════════════════════════════════════════════════╝

async def booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📅 BOOK BAZRAGOD\n\nContact:\n{BOOKING_EMAIL}\n\nInclude:\n• Event type\n• Date and location\n• Budget\n• Contact number\n\nBAZRAGOD is global. Parish 14 Nation. 🛸"
    )


async def fan_radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT COALESCE(country, 'Unknown'), COUNT(*) FROM fan_locations GROUP BY country ORDER BY 2 DESC LIMIT 10")
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
    uid = update.effective_user.id
    pts = award_points(uid, "wisdom", get_username(update))
    await update.message.reply_text(f"👑 Royal Wisdom\n\n{random.choice(QUOTES)}\n\n+{pts} pts")


async def fitness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    pts = award_points(uid, "fitness", get_username(update))
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
        label = f"@{username}" if username else "Anonymous"
        badge = " 💎" if is_sup else ""
        text += f"{medals[i]} {label}{badge}\n   {points} pts — {tier}\n\n"
    await update.message.reply_text(text)


async def my_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT points, invites, tier FROM fans WHERE telegram_id = %s", (uid,))
        row = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM fans WHERE points > COALESCE((SELECT points FROM fans WHERE telegram_id = %s), 0)", (uid,))
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
        f"⭐ YOUR STATS\n{'═'*20}\n"
        f"Points:  {pts}\nRank:    #{rank}\nTier:    {tier}\nInvites: {invites}\n"
        f"{'═'*20}\n{next_tier_msg}\n\nKeep grinding to climb 👑"
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
            "SELECT username, points, invites, tier, city, country, joined_at, is_supporter, supporter_expires, language FROM fans WHERE telegram_id = %s",
            (uid,),
        )
        row = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM fans WHERE points > COALESCE((SELECT points FROM fans WHERE telegram_id = %s), 0)", (uid,))
        rank_pos = cur.fetchone()[0] + 1
    finally:
        release_db(conn)
    if not row:
        await update.message.reply_text("Send /start first.")
        return
    username, points, invites, tier, city, country, joined_at, is_sup, sup_exp, lang = row
    display   = f"@{username}" if username else name
    location  = f"{city}, {country}" if city else "Not shared yet"
    joined    = joined_at.strftime("%B %Y") if joined_at else "Unknown"
    sup_badge = " 💎 Supporter" if is_sup else ""
    sup_line  = f"\nExpires: {sup_exp.strftime('%d %b %Y')}" if is_sup and sup_exp else ""
    lang_name = SUPPORTED_LANGUAGES.get(lang, "🇺🇸 English")

    next_rank_msg = ""
    for threshold, label in RANKS:
        if points < threshold:
            next_rank_msg = f"\n🎯 {threshold - points} pts to reach {label}"
            break

    await update.message.reply_text(
        f"👤 FAN PROFILE\n{'═'*20}\n"
        f"Name:     {display}{sup_badge}\n"
        f"Rank:     {tier}\n"
        f"Points:   {points}\n"
        f"#:        #{rank_pos}\n"
        f"Invites:  {invites}\n"
        f"City:     {location}\n"
        f"Language: {lang_name}\n"
        f"Joined:   {joined}{sup_line}\n"
        f"{'═'*20}{next_rank_msg}"
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
        cur.execute("SELECT completed FROM missions WHERE telegram_id = %s AND mission_date = %s", (uid, today))
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO missions (telegram_id, mission_date) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, today))
            conn.commit()
    finally:
        release_db(conn)
    if row and row[0]:
        await update.message.reply_text("🎯 DAILY MISSION\n\n✅ Already completed today!\n\nCome back tomorrow. 👑")
        return
    mission_text = random.choice(MISSIONS)
    await update.message.reply_text(
        f"🎯 DAILY MISSION\n{'═'*20}\n\n{mission_text}\n\nReward: +{POINTS['mission']} pts\n\nComplete it then tap below 👇",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Mark Complete", callback_data=f"mission:complete:{uid}")]]),
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
        cur.execute("SELECT completed FROM missions WHERE telegram_id = %s AND mission_date = %s", (uid, today))
        row = cur.fetchone()
        if row and row[0]:
            await query.message.reply_text("✅ Already completed today!")
            return
        cur.execute("INSERT INTO missions (telegram_id, mission_date, completed) VALUES (%s, %s, TRUE) ON CONFLICT (telegram_id, mission_date) DO UPDATE SET completed = TRUE", (uid, today))
        conn.commit()
    finally:
        release_db(conn)
    name = query.from_user.username or query.from_user.first_name
    pts  = award_points(uid, "mission", name)
    lang = get_user_lang(uid)
    await query.message.reply_text(f"🎯 MISSION COMPLETE!\n\n+{pts} points 🔥\n\n{t(lang, 'mission_done')}")
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
        f"👥 REFERRAL SYSTEM\n\nYour link:\n{link}\n\nInvites: {invites}\nTier:    {tier}\n\n"
        f"Tier Rewards:\n{tiers}\n\nEvery invite = +{POINTS['invite_friend']} pts 🔥\nBuild the Parish 14 army. 👑"
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║                  LOCATION SYSTEM                             ║
# ╚══════════════════════════════════════════════════════════════╝

async def location_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup([[KeyboardButton("📍 Send Location", request_location=True)], ["🔙 Back to Menu"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(f"📍 Share your location.\n\nPut your city on the Parish 14 fan map.\nEarn +{POINTS['share_location']} pts 🌍", reply_markup=kb)


async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    loc  = update.message.location
    lang = get_user_lang(uid)
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
    await update.message.reply_text(f"{t(lang, 'location_saved')}\n\n+{pts} pts", reply_markup=main_menu)
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
    await update.message.reply_text("🪐 MAXIMUS ASTRO READING\n\nStep 1 of 3\n\nEnter your birth date:\nFormat: DD/MM/YYYY\n\nExample: 15/03/1990")


async def astro_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    uid  = update.effective_user.id
    name = get_username(update)
    if uid not in astro_sessions:
        return False
    session = astro_sessions[uid]
    text    = update.message.text.strip()
    step    = session.get("step")

    if step == "birth_date":
        session["birth_date"] = text; session["step"] = "birth_time"
        await update.message.reply_text("✅ Birth date saved.\n\nStep 2 of 3\n\nEnter birth time:\nFormat: HH:MM AM/PM\n\nType 'unknown' if unsure.")
        return True

    if step == "birth_time":
        session["birth_time"] = text; session["step"] = "location"
        await update.message.reply_text("✅ Birth time saved.\n\nStep 3 of 3\n\nEnter birth city and current city:\n\nFormat: BirthCity, CurrentCity")
        return True

    if step == "location":
        session["step"] = "generating"
        await update.message.reply_text("🪐 MAXIMUS is reading your stars...\n\nStand by. 👑")
        try:
            parts        = text.split(",")
            birth_city   = parts[0].strip() if parts else "Unknown"
            current_city = parts[1].strip() if len(parts) > 1 else birth_city
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are MAXIMUS, astrocartography reader. Generate a powerful documentary-style reading in 4 paragraphs: current location energy, best for creativity and music, best for business and wealth, power advice now. No fear language. End with a sovereign statement."},
                    {"role": "user", "content": f"Birth Date: {session.get('birth_date')}\nBirth Time: {session.get('birth_time')}\nBirth City: {birth_city}\nCurrent City: {current_city}\n\nGenerate a full astrocartography reading."},
                ],
                max_tokens=600,
            )
            reading = response.choices[0].message.content
            conn    = get_db()
            cur     = conn.cursor()
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
            await update.message.reply_text(f"🪐 YOUR ASTRO READING\n{'═'*20}\n\n{reading}\n\n{'═'*20}\n+{pts} pts 👑")
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
    await update.message.reply_text(f"🤖 MAXIMUS ONLINE\n\nRoyal AI of BAZRAGOD.\nManager. Publicist. Radio DJ. Strategist.\n\nAsk me anything.\nType /menu to return.\n\n+{pts} pts")


async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("ai_active"):
        return False
    if not openai_client:
        return False
    uid      = update.effective_user.id
    name     = get_username(update)
    user_msg = update.message.text
    history  = context.user_data.get("ai_history", [])
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
# ║               📊 WEEKLY INTEL + ADMIN                        ║
# ╚══════════════════════════════════════════════════════════════╝

async def send_weekly_intel():
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM fans"); total_fans = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fans WHERE joined_at > NOW() - INTERVAL '7 days'"); new_fans = cur.fetchone()[0]
        cur.execute("SELECT SUM(points) FROM fans"); total_pts = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM fan_locations"); mapped = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(country,'Unknown'), COUNT(*) FROM fan_locations GROUP BY country ORDER BY 2 DESC LIMIT 3"); top_countries = cur.fetchall()
        cur.execute("SELECT username, points FROM fans ORDER BY points DESC LIMIT 3"); top_fans = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM purchases WHERE status = 'pending'"); pending = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM voice_wall WHERE status = 'pending'"); pending_voices = cur.fetchone()[0]
        cur.execute("SELECT title, plays, likes, donations FROM songs ORDER BY plays DESC LIMIT 3"); top_songs = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM fans WHERE is_supporter = TRUE"); supporters = cur.fetchone()[0]
        cur.execute("SELECT SUM(donations) FROM songs"); total_donations = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM radio_sessions WHERE last_ping > NOW() - INTERVAL '30 minutes'"); live = cur.fetchone()[0]
    finally:
        release_db(conn)

    countries_text = "\n".join([f"  📍 {c} — {f} fans" for c, f in top_countries]) or "  None yet"
    fans_text      = "\n".join([f"  🏅 @{f} — {p} pts" for f, p in top_fans if f]) or "  None yet"
    songs_text     = "\n".join([f"  🎵 {t} — {p:,} plays {calculate_heat(l, d, p)}" for t, p, l, d in top_songs]) or "  None"

    report = (
        f"📊 WEEKLY INTEL REPORT\n{'═'*22}\n"
        f"Week: {datetime.now().strftime('%d %B %Y')}\n\n"
        f"📻 Live Now:         {live}\n"
        f"👥 Total Fans:       {total_fans}\n"
        f"🆕 New This Week:    {new_fans}\n"
        f"⭐ Total Points:     {total_pts}\n"
        f"💎 Supporters:       {supporters}\n"
        f"📍 Fans Mapped:      {mapped}\n"
        f"💰 Total Donations:  {total_donations}\n"
        f"🛒 Pending Orders:   {pending}\n"
        f"🎙️ Pending Voices:   {pending_voices}\n\n"
        f"TOP COUNTRIES:\n{countries_text}\n\n"
        f"TOP FANS:\n{fans_text}\n\n"
        f"TOP SONGS:\n{songs_text}\n\n"
        f"— MAXIMUS INTEL SYSTEM 👑"
    )
    try:
        await telegram_app.bot.send_message(OWNER_ID, report)
        await maximus_speak_direct(
            telegram_app.bot, OWNER_ID,
            f"Weekly intel ready. {new_fans} new fans this week. {total_fans} total soldiers. The movement grows."
        )
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
            if now.hour == 0 and now.minute < 1:
                check_supporter_expiry()
        except Exception as e:
            print(f"Weekly thread error: {e}")
        time.sleep(60)


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    channel_status = f"📻 Channel Radio: {'ACTIVE' if RADIO_CHANNEL_ID else 'NOT SET (add RADIO_CHANNEL_ID env var)'}"
    await update.message.reply_text(
        f"👑 I.A.A.I.M.O ADMIN PANEL v13.000\n"
        f"══════════════════════════════\n\n"
        f"{channel_status}\n\n"
        f"ANALYTICS\n/stats  /radar  /weekly  /orders\n\n"
        f"CONTENT\n"
        f"/list_songs   /delete_song <id>\n"
        f"/list_beats   /delete_beat <id>\n"
        f"/list_drops   /delete_drop <id>\n"
        f"/list_dj_drops\n\n"
        f"PREMIERE\n/premiere <song_id>\n\n"
        f"RADIO\n/start_radio — start channel loop\n\n"
        f"VOICE WALL\n"
        f"/list_voices\n"
        f"/approve_voice <id>\n"
        f"/reject_voice <id>\n\n"
        f"REQUESTS\n/list_requests\n\n"
        f"SUPPORTERS\n/activate_supporter <telegram_id>\n\n"
        f"BROADCAST\n/broadcast\n/shoutout @username\n/announce <message>\n\n"
        f"UPLOAD\nSend audio — smart classify menu\n"
        f"Caption: #song #beat #drop #promo\n#announce #aurora #colorred #maximus #eclipse"
    )


async def start_radio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually trigger channel radio loop from admin."""
    if not is_admin(update.effective_user.id):
        return
    if not RADIO_CHANNEL_ID:
        await update.message.reply_text(
            "❌ RADIO_CHANNEL_ID not set.\n\n"
            "Add it in Railway environment variables:\n\n"
            "RADIO_CHANNEL_ID = -100XXXXXXXXX\n\n"
            "Get your channel ID by forwarding a message to @userinfobot."
        )
        return
    if radio_loop_running:
        await update.message.reply_text("📻 Channel radio loop is already running.")
        return
    asyncio.run_coroutine_threadsafe(channel_radio_loop(), loop)
    await update.message.reply_text(f"📻 Channel radio loop STARTED.\n\nBroadcasting to channel: {RADIO_CHANNEL_ID}\n\nStation is live. 👑")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM fans"); total_fans = cur.fetchone()[0]
        cur.execute("SELECT SUM(points) FROM fans"); total_pts = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM songs"); total_songs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM beats"); total_beats = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM drops"); total_drops = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM dj_drops"); total_dj = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM promos"); total_promos = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fan_locations"); mapped = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM purchases WHERE status = 'pending'"); pending = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM voice_wall WHERE status = 'pending'"); pv = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fans WHERE is_supporter = TRUE"); supporters = cur.fetchone()[0]
        cur.execute("SELECT SUM(donations) FROM songs"); total_donations = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM radio_sessions WHERE last_ping > NOW() - INTERVAL '30 minutes'"); live = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM song_requests WHERE played = FALSE"); pending_reqs = cur.fetchone()[0]
        cur.execute("SELECT title, plays, likes, donations FROM songs ORDER BY plays DESC LIMIT 1"); top_song = cur.fetchone()
        cur.execute("SELECT username, points FROM fans ORDER BY points DESC LIMIT 1"); top_fan = cur.fetchone()
    finally:
        release_db(conn)

    dj = get_current_dj()
    top_song_str = f"{top_song[0]} ({top_song[1]:,} plays)" if top_song else "None"
    top_fan_str  = f"@{top_fan[0]} ({top_fan[1]} pts)" if top_fan else "None"

    await update.message.reply_text(
        f"📊 MISERBOT STATS — v13.000\n{'═'*24}\n"
        f"📻 On Air: {dj['emoji']} {dj['name']}\n"
        f"📡 Channel Radio: {'ACTIVE' if radio_loop_running else 'STANDBY'}\n"
        f"👥 Live Listeners:   {live}\n\n"
        f"👥 Total Fans:       {total_fans}\n"
        f"💎 Supporters:       {supporters}\n"
        f"⭐ Points Given:     {total_pts}\n"
        f"💰 Total Donations:  {total_donations}\n"
        f"🎵 Songs:            {total_songs}\n"
        f"🥁 Beats:            {total_beats}\n"
        f"🎤 Drops:            {total_drops}\n"
        f"🎙️ DJ Drops:         {total_dj}\n"
        f"📻 Audio Promos:     {total_promos}\n"
        f"📍 Fans Mapped:      {mapped}\n"
        f"🛒 Pending Orders:   {pending}\n"
        f"🎙️ Pending Voices:   {pv}\n"
        f"📀 Pending Requests: {pending_reqs}\n"
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
        cur.execute("SELECT COUNT(*) FROM fan_locations"); total = cur.fetchone()[0]
    finally:
        release_db(conn)
    if not rows:
        await update.message.reply_text("No fan locations yet.")
        return
    text = f"🗺 TOUR INTELLIGENCE RADAR\nTotal mapped: {total}\n\n"
    for country, fans in rows:
        text += f"📍 {country} — {fans} fans\n"
    await update.message.reply_text(text)


async def orders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, telegram_id, item, price, purchased_at FROM purchases WHERE status = 'pending' ORDER BY purchased_at DESC LIMIT 20")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    if not rows:
        await update.message.reply_text("No pending orders. 🎉")
        return
    text = "🛒 PENDING ORDERS\n\n"
    for r in rows:
        text += f"Order #{r[0]} — {r[2]} (${r[3]})\nFan: {r[1]}\n{r[4].strftime('%d/%m %H:%M')}\n\n"
    await update.message.reply_text(text)


async def weekly_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("📊 Generating weekly intel...")
    await send_weekly_intel()
    await update.message.reply_text("✅ Weekly intel sent.")


async def premiere_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /premiere <song_id>")
        return
    song_id = int(args[0])
    conn    = get_db()
    cur     = conn.cursor()
    try:
        cur.execute("UPDATE songs SET rotation = 'A' WHERE id = %s RETURNING title", (song_id,))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    if not row:
        await update.message.reply_text("Song not found.")
        return
    title = row[0]
    dj    = get_current_dj()
    now   = datetime.now().strftime("%I:%M %p")
    msg   = (
        f"🌍 WORLD PREMIERE\n\n"
        f"📻 {dj['emoji']} BazraGod Radio — {now}\n\n"
        f"You are hearing '{title}' for the first time.\n\n"
        f"BAZRAGOD drops it here first.\nNo label. No middleman. Parish 14 Nation. 🛸"
    )
    sent = await _broadcast_to_all(context, msg)
    await update.message.reply_text(f"🎙️ Premiere broadcast sent to {sent} fans.\nSong '{title}' set to 🔴 A rotation.")


async def list_requests_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, username, song_title, played, requested_at FROM song_requests ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    if not rows:
        await update.message.reply_text("No requests yet.")
        return
    text = "📀 SONG REQUESTS\n\n"
    for r in rows:
        text += f"[{r[0]}] {'✅' if r[3] else '⏳'} @{r[1]} — {r[2]}\n"
    await update.message.reply_text(text)


async def list_dj_drops_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, dj, title FROM dj_drops ORDER BY dj, id")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    if not rows:
        await update.message.reply_text("No DJ drops yet.")
        return
    text = "🎙️ DJ DROPS\n\n"
    for r in rows:
        text += f"[{r[0]}] {r[1]} — {r[2]}\n"
    await update.message.reply_text(text)


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
    for d in [pending_broadcasts, astro_sessions, mood_sessions, cipher_sessions, upload_sessions, request_sessions]:
        d.pop(uid, None)
    context.user_data["ai_active"]         = False
    context.user_data["voice_wall_active"] = False
    await update.message.reply_text("Cancelled.", reply_markup=main_menu)


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    for d in [astro_sessions, mood_sessions, cipher_sessions, upload_sessions, request_sessions]:
        d.pop(uid, None)
    context.user_data["ai_active"]         = False
    context.user_data["ai_history"]        = []
    context.user_data["voice_wall_active"] = False
    await update.message.reply_text("👑 Main Menu", reply_markup=main_menu)


async def list_songs_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, title, plays, likes, donations, rotation FROM songs ORDER BY id")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    rb   = {"A": "🔴", "B": "🟡", "C": "🟢"}
    text = f"🎵 SONGS\n{'═'*16}\n\n"
    for r in rows:
        heat  = calculate_heat(r[3], r[4], r[2])
        text += f"[{r[0]}] {rb.get(r[5],'')} {r[1]}\n   {heat} {r[2]:,} plays  ❤️{r[3]}  💰{r[4]}\n"
    await update.message.reply_text(text or "Empty.")

async def list_beats_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    await _list_simple(update, "beats", "🥁 BEATS")

async def list_drops_cmd(update, context):
    if not is_admin(update.effective_user.id): return
    await _list_simple(update, "drops", "🎤 DROPS")

async def _list_simple(update, table, label):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(f"SELECT id, title FROM {table} ORDER BY id")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    text = f"{label}\n{'═'*16}\n\n"
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
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    await update.message.reply_text(f"🗑 Deleted: {row[0]}" if row else "Not found.")

# ╔══════════════════════════════════════════════════════════════╗
# ║                       ROUTER                                 ║
# ╚══════════════════════════════════════════════════════════════╝

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    uid  = update.effective_user.id

    if uid in astro_sessions:
        if await astro_input_handler(update, context): return

    if uid in mood_sessions:
        if await mood_radio_handler(uid, text, update, context): return

    if uid in cipher_sessions:
        if await cipher_handler(uid, text, update, context): return

    if uid in request_sessions:
        if await request_handler(uid, text, update, context): return

    if context.user_data.get("ai_active"):
        if await ai_chat_handler(update, context): return

    if re.search(r"youtube\.com|youtu\.be", text):
        if await youtube_detector(update, context): return

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
        "🔥 Trending":        trending,
        "📈 Song Stats":      song_stats,
        "📀 Request Track":   request_track,
        "💎 Supporter":       supporter,
        "💝 Charity":         charity,
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
        "🌍 Language":        language_select,
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
telegram_app.add_handler(CommandHandler("lang",                language_select))

# Admin
telegram_app.add_handler(CommandHandler("admin",               admin_panel))
telegram_app.add_handler(CommandHandler("stats",               stats))
telegram_app.add_handler(CommandHandler("radar",               radar))
telegram_app.add_handler(CommandHandler("orders",              orders_cmd))
telegram_app.add_handler(CommandHandler("weekly",              weekly_cmd))
telegram_app.add_handler(CommandHandler("premiere",            premiere_cmd))
telegram_app.add_handler(CommandHandler("start_radio",         start_radio_cmd))
telegram_app.add_handler(CommandHandler("broadcast",           broadcast_cmd))
telegram_app.add_handler(CommandHandler("shoutout",            shoutout_cmd))
telegram_app.add_handler(CommandHandler("announce",            announce_cmd))
telegram_app.add_handler(CommandHandler("list_songs",          list_songs_cmd))
telegram_app.add_handler(CommandHandler("list_beats",          list_beats_cmd))
telegram_app.add_handler(CommandHandler("list_drops",          list_drops_cmd))
telegram_app.add_handler(CommandHandler("list_dj_drops",       list_dj_drops_cmd))
telegram_app.add_handler(CommandHandler("list_requests",       list_requests_cmd))
telegram_app.add_handler(CommandHandler("delete_song",         delete_song_cmd))
telegram_app.add_handler(CommandHandler("delete_beat",         delete_beat_cmd))
telegram_app.add_handler(CommandHandler("delete_drop",         delete_drop_cmd))
telegram_app.add_handler(CommandHandler("list_voices",         list_voices_cmd))
telegram_app.add_handler(CommandHandler("approve_voice",       approve_voice_cmd))
telegram_app.add_handler(CommandHandler("reject_voice",        reject_voice_cmd))
telegram_app.add_handler(CommandHandler("activate_supporter",  activate_supporter_cmd))

# Callbacks
telegram_app.add_handler(CallbackQueryHandler(lang_cb,             pattern="^lang:"))
telegram_app.add_handler(CallbackQueryHandler(intro_cb,            pattern="^intro:"))
telegram_app.add_handler(CallbackQueryHandler(mission_complete_cb, pattern="^mission:"))
telegram_app.add_handler(CallbackQueryHandler(store_cb,            pattern="^store:"))
telegram_app.add_handler(CallbackQueryHandler(merch_cb,            pattern="^merch:"))
telegram_app.add_handler(CallbackQueryHandler(like_cb,             pattern="^like:"))
telegram_app.add_handler(CallbackQueryHandler(donate_cb,           pattern="^donate:"))
telegram_app.add_handler(CallbackQueryHandler(charity_confirm_cb,  pattern="^charity:"))
telegram_app.add_handler(CallbackQueryHandler(supporter_verify_cb, pattern="^supporter:"))
telegram_app.add_handler(CallbackQueryHandler(upload_classify_cb,  pattern="^upload:"))
telegram_app.add_handler(CallbackQueryHandler(chart_cb,            pattern="^chart:"))
telegram_app.add_handler(CallbackQueryHandler(play_song,           pattern="^song:"))
telegram_app.add_handler(CallbackQueryHandler(play_beat_cb,        pattern="^beat:"))
telegram_app.add_handler(CallbackQueryHandler(play_drop_cb,        pattern="^drop:"))
telegram_app.add_handler(CallbackQueryHandler(radio_next_cb,       pattern="^radio:next"))

# Media
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
    # Start channel radio loop if configured
    if RADIO_CHANNEL_ID:
        loop.create_task(channel_radio_loop())
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
    radio_status = "BROADCASTING" if radio_loop_running else "STANDBY"
    return f"I.A.A.I.M.O ONLINE — PARISH 14 NATION v13.000 | RADIO: {radio_status}", 200

# ╔══════════════════════════════════════════════════════════════╗
# ║                       MAIN                                   ║
# ╚══════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    init_pool()
    init_db()
    auto_classify_rotation()
    threading.Thread(target=weekly_intel_thread, daemon=True).start()
    print("╔══════════════════════════════════════════════╗")
    print("║   I.A.A.I.M.O — MISERBOT v13.000            ║")
    print("║   Owner:      BAZRAGOD                       ║")
    print("║   Nation:     Parish 14                      ║")
    print(f"║   Channel:    {RADIO_CHANNEL_ID or 'NOT SET':<30}║")
    print("║   Languages:  6 ACTIVE                       ║")
    print("║   Status:     ONLINE                         ║")
    print("╚══════════════════════════════════════════════╝")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
