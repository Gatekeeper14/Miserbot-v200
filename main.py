"""
I.A.A.I.M.O — MASTER SYSTEM v15.000
Independent Artists Artificial Intelligence Music Ops
Bot: Miserbot   Nation: Parish 14   Owner: BAZRAGOD

v15 VIRAL GROWTH ENGINE:
- Playlist Cache 300s TTL
- Radio History + Anti-Repeat (last 8 songs excluded)
- Secret Vault — point-gated exclusive content
- Artist Submissions — fans pitch tracks to BAZRAGOD
- Enhanced Leaderboard — Today / Week / All Time
- Dual Rank System — Nation Tier + Station Rank
- Referral Milestones — 5/10/25/50 invite rewards
- Community screen + Help system
- Cache invalidation on every content change
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

BOT_TOKEN        = os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL     = os.environ.get("DATABASE_URL")
OPENAI_API_KEY   = os.environ.get("OPENAI_API_KEY")
OWNER_ID         = int(os.environ.get("OWNER_ID", "8741545426"))
RADIO_CHANNEL_ID = os.environ.get("RADIO_CHANNEL_ID", "")
BOT_USERNAME     = "miserbot"
WEBHOOK_PATH     = "/webhook"

INTRO_FILE_ID = os.environ.get(
    "INTRO_FILE_ID",
    "CQACAgEAAxkBAAEdA9Jp2WRb5KP00P7uDWZQhizBRaY0nAACfwcAAmxuyUaMnHhvbPnphTsE",
)

BOOKING_EMAIL     = "Miserbot.ai@gmail.com"
CASHAPP           = "https://cash.app/$BAZRAGOD"
PAYPAL            = "https://paypal.me/bazragod1"
SUPPORTER_PRICE   = 19.99
CHARITY_PRICE     = 1.00
CHARITY_THRESHOLD = 500

RADIO_SONG_DELAY     = 200
RADIO_BEAT_DELAY     = 120
RADIO_DROP_DELAY     = 35
RADIO_AD_DELAY       = 25
RADIO_ANNOUNCE_DELAY = 30
PLAYLIST_CACHE_TTL   = 300

SOCIALS = {
    "Instagram": "https://www.instagram.com/bazragod_timeless",
    "TikTok":    "https://www.tiktok.com/@bazragod_official",
    "YouTube":   "https://youtube.com/@bazragodmusictravelandleis8835",
    "X":         "https://x.com/toligarch65693",
    "Snapchat":  "https://snapchat.com/t/L7djDwfj",
    "Twitch":    "https://twitch.tv/bazra14",
    "Spotify":   "https://open.spotify.com/artist/2IwaaLobpi2NSGD3B5xapK",
}

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
app           = Flask(__name__)

SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Espanol",
    "fr": "Francais",
    "pt": "Portugues",
    "de": "Deutsch",
    "jm": "Patois",
}

TRANSLATIONS = {
    "en": {
        "select_lang":    "Select your language to enter the platform.",
        "lang_saved":     "Language saved.",
        "welcome_inside": "YOU ARE NOW INSIDE\n\nI.A.A.I.M.O — Parish 14 Nation.\nNo labels. No middlemen. Just the movement.\n\nYou are part of history.",
        "no_songs":       "Catalog loading... check back soon.",
        "location_saved": "Location recorded!\n\nYour city is on the map.\n\nBAZRAGOD sees where his army stands.",
        "mission_done":   "MISSION COMPLETE!\n\nCome back tomorrow. Parish 14 never stops.",
    },
    "es": {
        "select_lang":    "Selecciona tu idioma para entrar a la plataforma.",
        "lang_saved":     "Idioma guardado.",
        "welcome_inside": "AHORA ESTAS DENTRO\n\nI.A.A.I.M.O — Nacion Parish 14.\nSin sellos. Sin intermediarios. Solo el movimiento.\n\nEres parte de la historia.",
        "no_songs":       "Catalogo cargando... vuelve pronto.",
        "location_saved": "Ubicacion registrada!\n\nTu ciudad esta en el mapa.",
        "mission_done":   "MISION COMPLETADA!\n\nVuelve manana. Parish 14 nunca para.",
    },
    "fr": {
        "select_lang":    "Selectionnez votre langue pour entrer sur la plateforme.",
        "lang_saved":     "Langue sauvegardee.",
        "welcome_inside": "VOUS ETES MAINTENANT A L'INTERIEUR\n\nI.A.A.I.M.O — Nation Parish 14.\nSans labels. Sans intermediaires. Juste le mouvement.\n\nVous faites partie de l'histoire.",
        "no_songs":       "Catalogue en chargement... revenez bientot.",
        "location_saved": "Localisation enregistree!\n\nVotre ville est sur la carte.",
        "mission_done":   "MISSION ACCOMPLIE!\n\nReviens demain. Parish 14 ne s'arrete jamais.",
    },
    "pt": {
        "select_lang":    "Selecione seu idioma para entrar na plataforma.",
        "lang_saved":     "Idioma salvo.",
        "welcome_inside": "VOCE ESTA DENTRO\n\nI.A.A.I.M.O — Nacao Parish 14.\nSem gravadoras. Sem intermediarios. So o movimento.\n\nVoce faz parte da historia.",
        "no_songs":       "Catalogo carregando... volte em breve.",
        "location_saved": "Localizacao registrada!\n\nSua cidade esta no mapa.",
        "mission_done":   "MISSAO COMPLETA!\n\nVolte amanha. Parish 14 nunca para.",
    },
    "de": {
        "select_lang":    "Wahle deine Sprache, um die Plattform zu betreten.",
        "lang_saved":     "Sprache gespeichert.",
        "welcome_inside": "DU BIST JETZT DRIN\n\nI.A.A.I.M.O — Parish 14 Nation.\nKein Label. Kein Mittelsmann. Nur die Bewegung.\n\nDu bist Teil der Geschichte.",
        "no_songs":       "Katalog wird geladen... bald verfugbar.",
        "location_saved": "Standort gespeichert!\n\nDeine Stadt ist auf der Karte.",
        "mission_done":   "MISSION ABGESCHLOSSEN!\n\nKomm morgen wieder. Parish 14 hort nie auf.",
    },
    "jm": {
        "select_lang":    "Select yu language fi enter di platform.",
        "lang_saved":     "Language saved, massive.",
        "welcome_inside": "YU INSIDE NOW\n\nI.A.A.I.M.O — Parish 14 Nation.\nNo label. No middleman. Just di movement.\n\nYu part of history.",
        "no_songs":       "Catalog loading... check back soon.",
        "location_saved": "Location saved!\n\nYu city pon di map.",
        "mission_done":   "MISSION COMPLETE!\n\nCome back tomorrow. Parish 14 nuh stop.",
    },
}

def t(lang, key):
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))

db_pool = None

def init_pool():
    global db_pool
    db_pool = SimpleConnectionPool(1, 10, dsn=DATABASE_URL)

def get_db():
    return db_pool.getconn()

def release_db(conn):
    db_pool.putconn(conn)

DJS = {
    "aurora": {
        "name": "DJ Aurora", "emoji": "🌅",
        "hours": range(5, 12), "db_key": "aurora",
        "style": "You are DJ Aurora, morning host of BazraGod Radio. Uplifting, motivational, sunrise vibes. Keep commentary under 2 sentences.",
        "intros": [
            "Good morning Parish 14. DJ Aurora on the frequency. Lets rise.",
            "The sun is up. BazraGod Radio morning session. DJ Aurora in control.",
        ],
    },
    "colorred": {
        "name": "DJ Color Red", "emoji": "🔴",
        "hours": range(12, 18), "db_key": "colorred",
        "style": "You are DJ Color Red, afternoon hype host of BazraGod Radio. High energy, street culture. Keep commentary under 2 sentences.",
        "intros": [
            "Afternoon session live. DJ Color Red on the dial. Turn it up.",
            "Midday heat. BazraGod Radio. DJ Color Red taking no prisoners.",
        ],
    },
    "maximus": {
        "name": "DJ Maximus", "emoji": "👑",
        "hours": range(18, 24), "db_key": "maximus",
        "style": "You are DJ Maximus, prime time commander of BazraGod Radio. Sovereign, deep, authoritative. Keep commentary under 2 sentences.",
        "intros": [
            "Prime time. DJ Maximus commanding the airwaves. Parish 14 Nation.",
            "The sovereign hour begins. DJ Maximus. BazraGod Radio.",
        ],
    },
    "eclipse": {
        "name": "DJ Eclipse", "emoji": "🌑",
        "hours": range(0, 5), "db_key": "eclipse",
        "style": "You are DJ Eclipse, late night host of BazraGod Radio. Deep, mysterious, cinematic. Keep commentary under 2 sentences.",
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
    "The nation grows stronger every day.",
    "Another BazraGod classic just touched the airwaves.",
]

AD_MESSAGES = [
    "Support independent music. Tap Support Artist in the menu.",
    "Parish 14 merch available now. Rep the nation. Tap Parish 14.",
    "Become a Supporter for $19.99/mo. Tap Supporter.",
    "Invite friends to grow the army. Tap Refer a Friend.",
    "Book BAZRAGOD for your event. Miserbot.ai@gmail.com",
    "Stream BAZRAGOD on Spotify. Search BAZRAGOD.",
    "Drop your verse. Tap Lyric Cipher and battle MAXIMUS.",
    "Unlock the Secret Vault. Earn points to access exclusive content.",
    "Are you an artist? Tap Submit Track and get on BazraGod Radio.",
    "Share your location. Put your city on the Parish 14 map.",
]

def get_current_dj():
    hour = datetime.now().hour
    for key, dj in DJS.items():
        if hour in dj["hours"]:
            return dj
    return DJS["maximus"]

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
    ("WINE GAL",             "CQACAgEAAxkBAAEdA9Bp2WPhWL8sSeviZWhQSZ_8CouWdAACfgcAAmxuyUajBWk0t2y2RzsE"),
]

SEED_BEATS = [
    ("BazraGod x Krayv Music", "CQACAgEAAxkBAAEdA-Zp2Wc0fY3nXOytykCPAAHjrr27BPgAAoIHAAJsbslGBBD2WfxSy987BA"),
    ("Stamp Dem Out",           "CQACAgEAAxkBAAEdA-hp2Wc0xqwDQ_PgXmy_9BMKWOgq7wAChAcAAmxuyUa3R76448OH-zsE"),
    ("Thing Dem Work",          "CQACAgEAAxkBAAEdA-lp2Wc0PDZ4Hl_TDsO61qPqODq6WwAChQcAAmxuyUbCwPZz3etTETsE"),
    ("Mad Symphony",            "CQACAgEAAxkBAAEdA-pp2Wc0UK_DWVbcp85NNxC8euxNZwAChgcAAmxuyUZHszd4DIsO2jsE"),
    ("Angels Cry",              "CQACAgEAAxkBAAEdA-tp2Wc06DGCVe_3P0MSftU90gV_UAAChwcAAmxuyUa_gsBT_qZDvzsE"),
]

SEED_DROPS = [
    ("BazraGod Drop 1", "CQACAgEAAxkBAAEdBAxp2WpPO2qN05UvBgqyRxxlKSdITAACigcAAmxuyUZ_p1-vZV720TsE"),
    ("BazraGod Drop 2", "CQACAgEAAxkBAAEdBBJp2WpPVvtkxNj3s50URaj7tGmP3AACkAcAAmxuyUaoKg1vw-BhfDsE"),
    ("BazraGod Drop 3", "CQACAgEAAxkBAAEdBApp2WpPpBMSgo0wbDDxQf1Oc-lm8AACiAcAAmxuyUYPXA0vWtk9rTsE"),
    ("BazraGod Drop 4", "CQACAgEAAxkBAAEdBBBp2WpP2WWiQlfY8lFCTdffMYxvxwACjgcAAmxuyUYJKHZz3otFODsE"),
    ("BazraGod Drop 5", "CQACAgEAAxkBAAEdBA1p2WpPXhfU71f1hY1OLqmCKVHyigACiwcAAmxuyUaTAuEpc5K6eDsE"),
    ("BazraGod Drop 6", "CQACAgEAAxkBAAEdBBNp2WpPk5TCLYY3chJsIyf-TEhDmgACkQcAAmxuyUbtePYuogtjUDsE"),
    ("BazraGod Drop 7", "CQACAgEAAxkBAAEdBA9p2WpPey4nzh_cMZuo7ZwochvSpgACjQcAAmxuyUZNCFz2CsYTYjsE"),
    ("BazraGod Drop 8", "CQACAgEAAxkBAAEdBAtp2WpPoEQ7v16RmJqXXocNh8_VbQACiQcAAmxuyUYFeLat27WdKjsE"),
    ("BazraGod Drop 9", "CQACAgEAAxkBAAEdBBFp2WpP-EM_p8JOt-fGhWUrDrWBYAACjwcAAmxuyUYuvzc5S9MEujsE"),
]

SEED_ANNOUNCEMENTS = [
    ("Parish 14 Nation Welcome", "CQACAgEAAxkBAAEdBA5p2WpPQ99yqaSeaKFJ1e2byrh1fwACjAcAAmxuyUYlAZdP-EiH0zsE"),
]

QUOTES = [
    "Discipline equals freedom.",
    "Move in silence. Only speak when it is time to say checkmate.",
    "Kings are built through struggle.",
    "He who conquers himself is the mightiest warrior.",
    "The obstacle is the way.",
    "A lion does not concern himself with the opinions of sheep.",
    "Kings are not born. They are made through discipline.",
    "What you seek is seeking you.",
    "Never outshine the master.",
    "The successful warrior is the average man with laser-like focus.",
]

FITNESS_MSG = """FITNESS PROTOCOL

Morning Circuit
50 Pushups
50 Squats
50 Situps
2km Run

Meal Plan
Eggs and Rice
Grilled Chicken
Fresh Fruit
Water only

No excuses. Repeat daily."""

AI_SYSTEM_PROMPT = """You are MAXIMUS the Royal AI of BAZRAGOD founder of I.A.A.I.M.O.

Roles: Artist Manager, Publicist, Tour Strategist, Fan Engagement Agent, Radio DJ, Music Business Advisor.

Personality: Sovereign, direct, loyal to BAZRAGOD. Jamaican cultural pride. Black and Gold aesthetic. Inspire fans. Protect the brand.

BAZRAGOD is fully independent no label no middleman. Platform lives inside Telegram. Catalog 16 tracks. Nation Parish 14.

Keep responses concise for Telegram max 3 paragraphs. End every response with a power statement."""

RANKS = [
    (0,    "Fan"),
    (100,  "Supporter"),
    (500,  "Recruiter"),
    (1000, "Commander"),
    (2500, "General"),
    (5000, "Nation Elite"),
]

LISTENER_RANKS = [
    (0,     "Listener"),
    (500,   "Supporter"),
    (2000,  "Ambassador"),
    (5000,  "Commander"),
    (10000, "Legend"),
]

def get_rank(points):
    rank = RANKS[0][1]
    for threshold, label in RANKS:
        if points >= threshold:
            rank = label
    return rank

def get_station_rank(points):
    rank = LISTENER_RANKS[0][1]
    for threshold, label in LISTENER_RANKS:
        if points >= threshold:
            rank = label
    return rank

def get_next_station_rank_info(points):
    for threshold, label in LISTENER_RANKS:
        if points < threshold:
            return f"{threshold - points} pts to reach {label}"
    return "Maximum Station Rank achieved"

POINTS = {
    "start": 5, "play_song": 8, "play_beat": 6, "radio": 10,
    "share_location": 15, "follow_social": 3, "support_artist": 5,
    "invite_friend": 20, "wisdom": 3, "fitness": 3, "ai_chat": 2,
    "mission": 100, "astro": 25, "cipher": 15, "mood_radio": 10,
    "voice_wall": 20, "like_song": 3, "supporter_sub": 50,
    "request_song": 3, "charity": 10, "donate_song": 10,
    "vault_unlock": 5, "submit_track": 10,
}

REFERRAL_TIERS = {
    5:  "Supporter",
    10: "Recruiter",
    25: "Commander",
    50: "General",
}

STORE_ITEMS = {
    "single":    ("Single Song Download",    5),
    "bundle":    ("Bundle 7 Songs",         20),
    "exclusive": ("Exclusive Album VIP",   500),
}

MERCH_ITEMS = {
    "tshirt":   ("Parish 14 T-Shirt",   50),
    "pullover": ("Parish 14 Pullover", 150),
}

MISSIONS = [
    "Listen to 1 song from the catalog",
    "Press BazraGod Radio and let it play",
    "Invite 1 friend using your referral link",
    "Share your location to put your city on the map",
    "Follow BAZRAGOD on all social platforms",
    "Check the leaderboard and see your rank",
    "Send a message to MAXIMUS AI",
    "Support the artist via CashApp or PayPal",
    "Try the Mood Radio feature",
    "Drop a verse in the Lyric Cipher",
    "Submit a voice shoutout to the Voice Wall",
    "Like a song from the catalog",
    "Check the Top Charts",
    "Request a track",
    "Make a $1 charity donation",
    "Visit the Secret Vault",
    "Submit a track to BazraGod Radio",
]

pending_broadcasts  = {}
astro_sessions      = {}
mood_sessions       = {}
cipher_sessions     = {}
upload_sessions     = {}
request_sessions    = {}
submission_sessions = {}
USER_PLAYLIST_INDEX = {}
RADIO_LAST_ANNOUNCE = {}

_PLAYLIST_CACHE      = []
_PLAYLIST_LAST_BUILD = 0.0

def get_cached_playlist():
    global _PLAYLIST_CACHE, _PLAYLIST_LAST_BUILD
    if time.time() - _PLAYLIST_LAST_BUILD > PLAYLIST_CACHE_TTL:
        _PLAYLIST_CACHE      = build_professional_playlist()
        _PLAYLIST_LAST_BUILD = time.time()
    return _PLAYLIST_CACHE

def invalidate_playlist_cache():
    global _PLAYLIST_LAST_BUILD
    _PLAYLIST_LAST_BUILD = 0.0

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
                tier              TEXT DEFAULT 'Fan',
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
            "CREATE TABLE IF NOT EXISTS radio_history (id SERIAL PRIMARY KEY, file_id TEXT, title TEXT, played_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS vault (id SERIAL PRIMARY KEY, title TEXT, file_id TEXT, required_points INTEGER DEFAULT 1000, uploaded_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS vault_unlocks (telegram_id BIGINT, vault_id INT, PRIMARY KEY (telegram_id, vault_id))",
            "CREATE TABLE IF NOT EXISTS artist_submissions (id SERIAL PRIMARY KEY, telegram_id BIGINT, username TEXT, artist_name TEXT, song_title TEXT, file_id TEXT, status TEXT DEFAULT 'pending', submitted_at TIMESTAMP DEFAULT NOW())",
        ]:
            cur.execute(tbl)

        cur.execute("SELECT COUNT(*) FROM songs")
        if cur.fetchone()[0] == 0:
            for title, file_id in SEED_SONGS:
                cur.execute("INSERT INTO songs (title, file_id) VALUES (%s, %s) ON CONFLICT (title) DO NOTHING", (title, file_id))

        cur.execute("SELECT COUNT(*) FROM beats")
        if cur.fetchone()[0] == 0:
            for title, file_id in SEED_BEATS:
                cur.execute("INSERT INTO beats (title, file_id) VALUES (%s, %s)", (title, file_id))

        cur.execute("SELECT COUNT(*) FROM drops")
        if cur.fetchone()[0] == 0:
            for title, file_id in SEED_DROPS:
                cur.execute("INSERT INTO drops (title, file_id) VALUES (%s, %s)", (title, file_id))

        cur.execute("SELECT COUNT(*) FROM announcements")
        if cur.fetchone()[0] == 0:
            for title, file_id in SEED_ANNOUNCEMENTS:
                cur.execute("INSERT INTO announcements (title, file_id) VALUES (%s, %s)", (title, file_id))

        conn.commit()
        print("DATABASE READY v15.000")
    finally:
        release_db(conn)

def calculate_heat(likes, donations, plays):
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
        for sid, plays, likes, donations in cur.fetchall():
            score    = (plays / 1000.0) + (likes * 5) + (donations * 10)
            rotation = "A" if score > 1000 else "B" if score > 500 else "C"
            cur.execute("UPDATE songs SET rotation = %s WHERE id = %s", (rotation, sid))
        conn.commit()
    except Exception as e:
        print(f"Rotation error: {e}")
    finally:
        release_db(conn)

def build_professional_playlist():
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT title, file_id, plays, likes, donations, rotation
            FROM songs
            WHERE file_id NOT IN (
                SELECT COALESCE(file_id, '')
                FROM radio_history
                ORDER BY played_at DESC
                LIMIT 8
            )
            ORDER BY id
        """)
        songs = cur.fetchall()
        if not songs:
            cur.execute("SELECT title, file_id, plays, likes, donations, rotation FROM songs ORDER BY id")
            songs = cur.fetchall()
        cur.execute("SELECT title, file_id FROM drops ORDER BY id")
        drops = cur.fetchall()
        cur.execute("SELECT title, file_id FROM beats ORDER BY id")
        beats = cur.fetchall()
        cur.execute("SELECT title, file_id FROM announcements ORDER BY id")
        announcements = cur.fetchall()
    finally:
        release_db(conn)

    if not songs:
        return []

    playlist   = []
    drop_idx   = 0
    beat_idx   = 0
    ann_idx    = 0
    song_count = 0

    for song in songs:
        title, file_id, plays, likes, donations, rotation = song
        playlist.append({"type": "song", "title": title, "file_id": file_id,
                          "plays": plays, "likes": likes, "donations": donations, "rotation": rotation})
        song_count += 1
        if drops:
            d = drops[drop_idx % len(drops)]
            playlist.append({"type": "drop", "title": d[0], "file_id": d[1]})
            drop_idx += 1
        if song_count % 2 == 0 and beats:
            b = beats[beat_idx % len(beats)]
            playlist.append({"type": "beat", "title": b[0], "file_id": b[1]})
            beat_idx += 1
        if song_count % 4 == 0:
            playlist.append({"type": "ad", "title": "AD_BREAK", "file_id": None})
            if announcements:
                a = announcements[ann_idx % len(announcements)]
                playlist.append({"type": "announcement", "title": a[0], "file_id": a[1]})
                ann_idx += 1
    return playlist

def _log_radio_history(file_id, title):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("INSERT INTO radio_history (file_id, title) VALUES (%s, %s)", (file_id, title))
        cur.execute("DELETE FROM radio_history WHERE id NOT IN (SELECT id FROM radio_history ORDER BY played_at DESC LIMIT 50)")
        conn.commit()
    except Exception as e:
        print(f"Radio history error: {e}")
    finally:
        release_db(conn)

def get_next_playlist_item(uid):
    playlist = build_professional_playlist()
    if not playlist:
        return {"type": "empty", "title": "", "file_id": None}
    idx = USER_PLAYLIST_INDEX.get(uid, 0)
    if idx >= len(playlist):
        idx = 0
    item = playlist[idx]
    USER_PLAYLIST_INDEX[uid] = idx + 1
    return item

radio_loop_running = False

async def channel_radio_loop():
    global radio_loop_running
    if radio_loop_running:
        return
    radio_loop_running = True
    if not RADIO_CHANNEL_ID:
        print("RADIO_CHANNEL_ID not set")
        radio_loop_running = False
        return
    channel_id     = int(RADIO_CHANNEL_ID)
    playlist_index = 0
    print(f"Channel radio loop started {channel_id}")
    while True:
        try:
            playlist = get_cached_playlist()
            if not playlist:
                await asyncio.sleep(30)
                continue
            if playlist_index >= len(playlist):
                playlist_index = 0
                invalidate_playlist_cache()
            item = playlist[playlist_index]
            playlist_index += 1
            dj  = get_current_dj()
            now = datetime.now().strftime("%I:%M %p")
            if item["type"] == "ad":
                await telegram_app.bot.send_message(
                    chat_id=channel_id,
                    text=f"BazraGod Radio {now}\n\n{random.choice(AD_MESSAGES)}\n\nt.me/{BOT_USERNAME}",
                )
                await asyncio.sleep(RADIO_AD_DELAY)
            elif item["type"] == "announcement" and item["file_id"]:
                await telegram_app.bot.send_audio(
                    chat_id=channel_id, audio=item["file_id"],
                    caption=f"{item['title']}\nBazraGod Radio {now}\n\nt.me/{BOT_USERNAME}",
                )
                await asyncio.sleep(RADIO_ANNOUNCE_DELAY)
            elif item["type"] == "drop" and item["file_id"]:
                await telegram_app.bot.send_audio(
                    chat_id=channel_id, audio=item["file_id"],
                    caption=f"{dj['name']}\nBazraGod Radio {now}\n\nt.me/{BOT_USERNAME}",
                )
                await asyncio.sleep(RADIO_DROP_DELAY)
            elif item["type"] == "beat" and item["file_id"]:
                await telegram_app.bot.send_audio(
                    chat_id=channel_id, audio=item["file_id"],
                    caption=f"BAZRAGOD BEAT {item['title']}\nBazraGod Radio {now}\n\nt.me/{BOT_USERNAME}",
                )
                await asyncio.sleep(RADIO_BEAT_DELAY)
            elif item["type"] == "song" and item["file_id"]:
                conn = get_db()
                cur  = conn.cursor()
                try:
                    cur.execute("UPDATE songs SET plays = plays + 1 WHERE title = %s", (item["title"],))
                    cur.execute("SELECT plays, likes, donations FROM songs WHERE title = %s", (item["title"],))
                    row = cur.fetchone()
                    conn.commit()
                finally:
                    release_db(conn)
                plays     = row[0] if row else 0
                likes     = row[1] if row else 0
                donations = row[2] if row else 0
                heat      = calculate_heat(likes, donations, plays)
                await telegram_app.bot.send_audio(
                    chat_id=channel_id, audio=item["file_id"],
                    caption=f"BazraGod Radio {now}\n\n{item['title']}\nBAZRAGOD\n\n{heat}  {plays:,} plays\n\nJoin: t.me/{BOT_USERNAME}",
                )
                _log_radio_history(item["file_id"], item["title"])
                await asyncio.sleep(RADIO_SONG_DELAY)
        except Exception as e:
            print(f"Channel radio loop error: {e}")
            await asyncio.sleep(15)

def award_points(telegram_id, action, username=None):
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
        cur.execute("INSERT INTO point_log (telegram_id, action, pts) VALUES (%s, %s, %s)", (telegram_id, action, pts))
        cur.execute("SELECT points FROM fans WHERE telegram_id = %s", (telegram_id,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE fans SET tier = %s WHERE telegram_id = %s", (get_rank(row[0]), telegram_id))
        conn.commit()
    finally:
        release_db(conn)
    return pts

def register_fan(telegram_id, username, referrer_id=None):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT telegram_id FROM fans WHERE telegram_id = %s", (telegram_id,))
        if cur.fetchone():
            return False
        cur.execute("INSERT INTO fans (telegram_id, username, referrer_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    (telegram_id, username, referrer_id))
        if referrer_id:
            cur.execute("UPDATE fans SET invites = invites + 1 WHERE telegram_id = %s", (referrer_id,))
        conn.commit()
        return True
    finally:
        release_db(conn)

def get_user_lang(uid):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT language FROM fans WHERE telegram_id = %s", (uid,))
        row = cur.fetchone()
        return row[0] if row and row[0] else "en"
    finally:
        release_db(conn)

def set_user_lang(uid, lang):
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

def update_listener(uid):
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

def get_listener_count():
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM radio_sessions WHERE last_ping > NOW() - INTERVAL '30 minutes'")
        return cur.fetchone()[0]
    finally:
        release_db(conn)

async def check_referral_milestones(uid, username, context):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT invites FROM fans WHERE telegram_id = %s", (uid,))
        row = cur.fetchone()
        if not row:
            return
        invites = row[0]
    finally:
        release_db(conn)

    if invites == 5:
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT title, file_id FROM beats ORDER BY id LIMIT 1")
            beat = cur.fetchone()
        finally:
            release_db(conn)
        await context.bot.send_message(uid, "REFERRAL MILESTONE 5 SOLDIERS\n\nBAZRAGOD rewards loyalty.\nYou just unlocked an exclusive beat.")
        if beat:
            await context.bot.send_audio(uid, beat[1], caption=f"{beat[0]}\n\nExclusive unlock Parish 14 Nation")

    elif invites == 10:
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT id, title, file_id FROM vault ORDER BY required_points LIMIT 1")
            vault_item = cur.fetchone()
        finally:
            release_db(conn)
        if vault_item:
            conn = get_db()
            cur  = conn.cursor()
            try:
                cur.execute("INSERT INTO vault_unlocks (telegram_id, vault_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (uid, vault_item[0]))
                conn.commit()
            finally:
                release_db(conn)
            await context.bot.send_message(uid, "VAULT UNLOCKED 10 SOLDIERS\n\nThe vault doors are open.\nBAZRAGOD drops an exclusive.")
            await context.bot.send_audio(uid, vault_item[2], caption=f"{vault_item[1]}\n\nVault Exclusive Parish 14 Nation")
        else:
            await context.bot.send_message(uid, "VAULT REWARD 10 SOLDIERS\n\nVault access unlocked. More content coming soon.")

    elif invites == 25:
        expires = date.today() + timedelta(days=7)
        conn    = get_db()
        cur     = conn.cursor()
        try:
            cur.execute("UPDATE fans SET is_supporter = TRUE, supporter_expires = %s WHERE telegram_id = %s",
                        (expires, uid))
            conn.commit()
        finally:
            release_db(conn)
        award_points(uid, "supporter_sub", username)
        await context.bot.send_message(uid,
            f"SUPPORTER ACTIVATED FREE 25 SOLDIERS\n\n7-day Parish 14 Supporter status.\nExpires {expires.strftime('%B %d %Y')}\n\nBAZRAGOD rewards those who build the army.")

    elif invites == 50:
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("UPDATE fans SET tier = 'Nation Elite', is_supporter = TRUE WHERE telegram_id = %s", (uid,))
            conn.commit()
        finally:
            release_db(conn)
        await context.bot.send_message(uid,
            "NATION ELITE PERMANENT 50 SOLDIERS\n\nYou have built the movement.\nBAZRAGOD sees you. The nation is yours.\n\nNation Elite. Permanent. No expiry.")

main_menu = ReplyKeyboardMarkup(
    [
        ["BAZRAGOD MUSIC",   "BazraGod Radio"],
        ["Mood Radio",       "Lyric Cipher"],
        ["Top Charts",       "Trending"],
        ["Request Track",    "Supporter"],
        ["Charity",          "Song Stats"],
        ["Beats",            "Drops"],
        ["Secret Vault",     "Submit Track"],
        ["Leaderboard",      "My Points"],
        ["My Profile",       "Daily Mission"],
        ["Support Artist",   "Social"],
        ["Music Store",      "Parish 14"],
        ["Wisdom",           "Fitness"],
        ["Share Location",   "Refer a Friend"],
        ["Fan Radar",        "Booking"],
        ["Voice Wall",       "Astro Reading"],
        ["Language",         "MAXIMUS AI"],
        ["Community",        "Help"],
    ],
    resize_keyboard=True,
)

def get_username(update):
    u = update.effective_user
    return u.username or u.first_name or str(u.id)

def is_admin(uid):
    return uid == OWNER_ID

def lang_selector_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=f"lang:{code}")]
        for code, label in SUPPORTED_LANGUAGES.items()
    ])

async def maximus_speak(context, chat_id, text):
    if not openai_client:
        return
    try:
        response = openai_client.audio.speech.create(model="tts-1", voice="onyx", input=text[:500], speed=0.95)
        buf = BytesIO(response.content)
        buf.name = "maximus.ogg"
        await context.bot.send_voice(chat_id=chat_id, voice=buf)
    except Exception as e:
        print(f"Voice error: {e}")

async def maximus_speak_direct(bot, chat_id, text):
    if not openai_client:
        return
    try:
        response = openai_client.audio.speech.create(model="tts-1", voice="onyx", input=text[:500], speed=0.95)
        buf = BytesIO(response.content)
        buf.name = "maximus.ogg"
        await bot.send_voice(chat_id=chat_id, voice=buf)
    except Exception as e:
        print(f"Voice direct error: {e}")

async def dj_speak(context, chat_id, text):
    now  = datetime.now()
    last = RADIO_LAST_ANNOUNCE.get(chat_id)
    if last and (now - last) < timedelta(minutes=15):
        return
    RADIO_LAST_ANNOUNCE[chat_id] = now
    if not openai_client:
        return
    try:
        response = openai_client.audio.speech.create(model="tts-1", voice="onyx", input=text[:500], speed=0.92)
        buf = BytesIO(response.content)
        buf.name = "dj.ogg"
        await context.bot.send_voice(chat_id=chat_id, voice=buf)
    except Exception as e:
        print(f"DJ voice error: {e}")

async def generate_dj_line(dj, song_title=None, action="intro"):
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
            messages=[{"role": "system", "content": dj["style"]}, {"role": "user", "content": prompt}],
            max_tokens=80,
        )
        return response.choices[0].message.content
    except Exception:
        return random.choice(dj["intros"])

async def maybe_prophecy(uid, username, context):
    if not openai_client:
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT points, tier, prophecy_tiers FROM fans WHERE telegram_id = %s", (uid,))
        row = cur.fetchone()
        if not row:
            return
        points, tier, sent_tiers = row
        sent_tiers = sent_tiers or ""
        if tier == "Fan" or tier in sent_tiers:
            return
        cur.execute("UPDATE fans SET prophecy_tiers = prophecy_tiers || %s WHERE telegram_id = %s", (f"{tier}|", uid))
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
        await context.bot.send_message(uid, f"SOVEREIGN PROPHECY\n\nBAZRAGOD sees you.\n\n{prophecy}\n\nRank: {tier}")
        await maximus_speak(context, uid, prophecy)
    except Exception as e:
        print(f"Prophecy error: {e}")

async def language_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_user_lang(uid)
    await update.message.reply_text(t(lang, "select_lang"), reply_markup=lang_selector_kb())

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
    if INTRO_FILE_ID:
        await query.message.reply_text(f"{lang_name} {t(lang, 'lang_saved')}\n\nBefore you enter press play. Real fans only.")
        await query.message.reply_voice(
            INTRO_FILE_ID,
            caption="BAZRAGOD The Vision\nI.A.A.I.M.O",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Enter The Platform", callback_data="intro:play")]]),
        )
    else:
        await query.message.reply_text(f"{lang_name} {t(lang, 'lang_saved')}\n\n{t(lang, 'welcome_inside')}", reply_markup=main_menu)

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
            await context.bot.send_message(referrer,
                f"New soldier joined your link!\n+{POINTS['invite_friend']} pts credited\n\n"
                f"Check milestone rewards 5 10 25 50 invites unlock big prizes!")
            award_points(referrer, "invite_friend")
            await check_referral_milestones(referrer, name, context)
        except Exception:
            pass
    ufo = (
        "       UFO\n\n"
        "B A Z R A G O D\n"
        "I.A.A.I.M.O\n"
        "PARISH 14 COMMAND\n\n"
        "Initiating entry sequence..."
    )
    await update.message.reply_text(ufo)
    if is_new:
        await update.message.reply_text("PARISH 14 NETWORK\n\nSelect your language to enter:", reply_markup=lang_selector_kb())
    elif INTRO_FILE_ID:
        await update.message.reply_text("Welcome back. Press play.")
        await update.message.reply_voice(
            INTRO_FILE_ID,
            caption="BAZRAGOD The Vision\nI.A.A.I.M.O",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Enter The Platform", callback_data="intro:play")]]),
        )
    else:
        await update.message.reply_text(f"WELCOME TO I.A.A.I.M.O\n\nParish 14 Nation\n\n+{pts} pts", reply_markup=main_menu)

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
    pts     = row[0] if row else 0
    tier    = row[1] if row else "Fan"
    station = get_station_rank(pts)
    channel_line = f"\nLive Radio: t.me/c/{str(RADIO_CHANNEL_ID).replace('-100', '')}" if RADIO_CHANNEL_ID else ""
    await query.message.reply_text(
        f"{t(lang, 'welcome_inside')}\n\nNation Tier: {tier}\nStation Rank: {station}\nPoints: {pts}{channel_line}\n\nThe platform is yours.",
        reply_markup=main_menu,
    )

async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    update_listener(uid)
    listeners = get_listener_count()
    pts       = award_points(uid, "radio", name)
    await _play_next_for_user(uid, name, pts, listeners, update.message, context)
    await maybe_prophecy(uid, name, context)

async def radio_next_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Loading next...")
    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name
    update_listener(uid)
    listeners = get_listener_count()
    pts       = award_points(uid, "radio", name)
    await _play_next_for_user(uid, name, pts, listeners, query.message, context)
    await maybe_prophecy(uid, name, context)

async def _play_next_for_user(uid, name, pts, listeners, msg, context):
    item = get_next_playlist_item(uid)
    dj   = get_current_dj()
    now  = datetime.now().strftime("%I:%M %p")

    if item["type"] == "empty":
        await msg.reply_text("Radio loading... Upload songs first.", reply_markup=main_menu)
        return

    if item["type"] == "ad":
        await msg.reply_text(
            f"BazraGod Radio {now}\n\n{random.choice(AD_MESSAGES)}\n\n{listeners} listeners tuned in",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Continue Radio", callback_data="radio:next")]]),
        )
        return

    if item["type"] == "announcement" and item["file_id"]:
        await msg.reply_audio(
            item["file_id"],
            caption=f"{item['title']}\nBazraGod Radio {now}\n\n+{pts} pts",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Next Track", callback_data="radio:next")]]),
        )
        return

    if item["type"] == "drop" and item["file_id"]:
        await msg.reply_audio(
            item["file_id"],
            caption=f"{dj['name']}\nBazraGod Radio {now}\n\n+{pts} pts",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Next Track", callback_data="radio:next")]]),
        )
        return

    if item["type"] == "beat" and item["file_id"]:
        await dj_speak(context, uid, f"BazraGod Radio. {now}. Feel this beat. Parish 14.")
        await msg.reply_audio(
            item["file_id"],
            caption=f"BAZRAGOD BEAT {item['title']}\nBazraGod Radio {now}\n\n{listeners} listeners\n\n+{pts} pts",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Next Track", callback_data="radio:next")]]),
        )
        return

    if item["type"] == "song" and item["file_id"]:
        title    = item["title"]
        file_id  = item["file_id"]
        rotation = item.get("rotation", "C")
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("UPDATE songs SET plays = plays + 1 WHERE title = %s", (title,))
            cur.execute("SELECT id, plays, likes, donations FROM songs WHERE title = %s", (title,))
            row = cur.fetchone()
            conn.commit()
        finally:
            release_db(conn)
        sid       = row[0] if row else 0
        plays     = row[1] if row else 0
        likes     = row[2] if row else 0
        donations = row[3] if row else 0
        heat      = calculate_heat(likes, donations, plays)
        rot_badge = {"A": "Hot", "B": "Mid", "C": "Deep"}.get(rotation, "")
        dj_line   = await generate_dj_line(dj, title, "intro")
        if random.random() < 0.25:
            await dj_speak(context, uid, random.choice(DJ_TRANSITIONS))
        await dj_speak(context, uid, dj_line)
        await msg.reply_audio(
            file_id,
            caption=(
                f"BazraGod Radio {now}\n\n"
                f"{title}  {rot_badge}\nBAZRAGOD\n\n"
                f"{heat}  {plays:,} plays  {likes} likes  {donations} donations\n\n"
                f"{listeners} listeners tuned in\n\n+{pts} pts"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Next Track",  callback_data="radio:next"),
                InlineKeyboardButton("Like",        callback_data=f"like:{sid}"),
                InlineKeyboardButton("Donate",      callback_data=f"donate:{sid}"),
            ]]),
        )

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
    keyboard = [[InlineKeyboardButton(f"{s[1]}  {calculate_heat(s[3], s[4], s[2])}", callback_data=f"song:{s[0]}")] for s in songs]
    await update.message.reply_text(
        f"BAZRAGOD CATALOG\nParish 14 Nation {len(songs)} tracks\n\nSelect a track",
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
        cur.execute("SELECT title, file_id, plays, likes, donations FROM songs WHERE id = %s", (song_id,))
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
            caption=f"{title}\nBAZRAGOD\n\n{heat}  {plays:,} plays  {likes} likes\n\n+{pts} pts",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Like",   callback_data=f"like:{song_id}"),
                InlineKeyboardButton("Donate", callback_data=f"donate:{song_id}"),
            ]]),
        )
        await maybe_prophecy(uid, name, context)

async def like_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        song_id = int(query.data.split(":")[1])
    except Exception:
        await query.answer()
        return
    if song_id == 0:
        await query.answer("Tap a song from the catalog to like it!", show_alert=False)
        return
    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("INSERT INTO song_likes (telegram_id, song_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, song_id))
        if cur.rowcount > 0:
            cur.execute("UPDATE songs SET likes = likes + 1 WHERE id = %s", (song_id,))
            conn.commit()
            award_points(uid, "like_song", name)
            await query.answer("Liked! +3 pts", show_alert=False)
        else:
            await query.answer("Already liked", show_alert=False)
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
    await query.message.reply_text(
        f"SUPPORT THE ARTIST\n\nEvery donation powers independent music.\nParish 14 Nation.\n\n+{POINTS['donate_song']} pts",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]),
    )
    if total_donations >= CHARITY_THRESHOLD:
        try:
            await context.bot.send_message(OWNER_ID, f"CHARITY THRESHOLD REACHED!\n\nTotal: {total_donations}\n${CHARITY_THRESHOLD} hit!")
        except Exception:
            pass

async def top_charts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dj = get_current_dj()
    await update.message.reply_text(
        f"PARISH 14 CHARTS\n\n{dj['name']} presents the charts.\n\nSelect",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Top Played",  callback_data="chart:played")],
            [InlineKeyboardButton("Most Liked",  callback_data="chart:liked")],
            [InlineKeyboardButton("Trending",    callback_data="chart:trending")],
        ]),
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
            label = "TOP PLAYED"
        elif chart_type == "liked":
            cur.execute("SELECT title, plays, likes, donations FROM songs ORDER BY likes DESC LIMIT 10")
            label = "MOST LIKED"
        else:
            cur.execute("SELECT title, plays, likes, donations FROM songs ORDER BY (plays/1000.0 + likes*5 + donations*10) DESC LIMIT 10")
            label = "TRENDING"
        songs = cur.fetchall()
    finally:
        release_db(conn)
    medals = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    text   = f"PARISH 14 {label}\n\n"
    for i, (title, plays, likes, donations) in enumerate(songs):
        text += f"{medals[i]}. {title}\n{calculate_heat(likes, donations, plays)}  {plays:,} plays  {likes} likes\n\n"
    await query.message.reply_text(text)

async def trending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT title, plays, likes, donations FROM songs ORDER BY (plays/1000.0 + likes*5 + donations*10) DESC LIMIT 10")
        songs = cur.fetchall()
    finally:
        release_db(conn)
    text = "TRENDING ON PARISH 14\n\n"
    for i, (title, plays, likes, donations) in enumerate(songs):
        text += f"{i+1}. {title}\n{plays:,} plays  {calculate_heat(likes, donations, plays)}\n\n"
    await update.message.reply_text(text)

async def song_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT title, plays, likes, donations, rotation FROM songs ORDER BY plays DESC LIMIT 10")
        songs = cur.fetchall()
    finally:
        release_db(conn)
    rb   = {"A": "Hot", "B": "Mid", "C": "Deep"}
    text = "SONG STATISTICS\n\n"
    for title, plays, likes, donations, rotation in songs:
        text += f"{title}  {rb.get(rotation,'')}\nPlays: {plays:,}  Likes: {likes}  Donations: {donations}\nHeat: {calculate_heat(likes, donations, plays)}\n\n"
    await update.message.reply_text(text)

async def beats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, title FROM beats ORDER BY id")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    if not rows:
        await update.message.reply_text("No beats uploaded yet.")
        return
    keyboard = [[InlineKeyboardButton(r[1], callback_data=f"beat:{r[0]}")] for r in rows]
    await update.message.reply_text(f"BAZRAGOD BEATS\n{len(rows)} available", reply_markup=InlineKeyboardMarkup(keyboard))

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
        await query.message.reply_audio(beat[1], caption=f"{beat[0]}\n\n+{pts} pts")

async def drops_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, title FROM drops ORDER BY id")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    if not rows:
        await update.message.reply_text("No drops yet. Stay tuned.")
        return
    keyboard = [[InlineKeyboardButton(r[1], callback_data=f"drop:{r[0]}")] for r in rows]
    await update.message.reply_text(f"RADIO DROPS\n{len(rows)} available", reply_markup=InlineKeyboardMarkup(keyboard))

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
        await query.message.reply_audio(drop[1], caption=drop[0])

async def vault_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT points FROM fans WHERE telegram_id = %s", (uid,))
        fan_row    = cur.fetchone()
        fan_points = fan_row[0] if fan_row else 0
        cur.execute("SELECT id, title, required_points FROM vault ORDER BY required_points")
        items = cur.fetchall()
        cur.execute("SELECT vault_id FROM vault_unlocks WHERE telegram_id = %s", (uid,))
        unlocked = {r[0] for r in cur.fetchall()}
    finally:
        release_db(conn)
    if not items:
        await update.message.reply_text(
            f"SECRET VAULT\n\nYour Points: {fan_points:,}\n\nThe vault is loading with exclusive content.\n\n"
            f"Earn points by listening, missions, inviting friends, supporting the artist."
        )
        return
    keyboard = []
    for vid, title, req_pts in items:
        if vid in unlocked or fan_points >= req_pts:
            btn_label = f"UNLOCKED {title}"
        else:
            btn_label = f"LOCKED {title} {req_pts:,} pts"
        keyboard.append([InlineKeyboardButton(btn_label, callback_data=f"vault:{vid}")])
    await update.message.reply_text(
        f"SECRET VAULT\n\nYour Points: {fan_points:,}\n\nExclusive BAZRAGOD content.\nUnlock with Parish 14 points.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    award_points(uid, "vault_unlock", name)

async def vault_item_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name
    try:
        vault_id = int(query.data.split(":")[1])
    except Exception:
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT title, file_id, required_points FROM vault WHERE id = %s", (vault_id,))
        item = cur.fetchone()
        cur.execute("SELECT points FROM fans WHERE telegram_id = %s", (uid,))
        fan_row    = cur.fetchone()
        fan_points = fan_row[0] if fan_row else 0
        cur.execute("SELECT 1 FROM vault_unlocks WHERE telegram_id = %s AND vault_id = %s", (uid, vault_id))
        already_unlocked = cur.fetchone() is not None
    finally:
        release_db(conn)
    if not item:
        await query.answer("Item not found.", show_alert=True)
        return
    title, file_id, req_pts = item
    if already_unlocked or fan_points >= req_pts:
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("INSERT INTO vault_unlocks (telegram_id, vault_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, vault_id))
            conn.commit()
        finally:
            release_db(conn)
        await query.message.reply_audio(
            file_id,
            caption=f"VAULT UNLOCKED\n\n{title}\nBAZRAGOD Exclusive\n\nParish 14 Nation.",
        )
        await maybe_prophecy(uid, name, context)
    else:
        needed = req_pts - fan_points
        await query.answer(f"Need {needed:,} more points to unlock this.", show_alert=True)

async def submit_track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    submission_sessions[uid] = True
    await update.message.reply_text(
        "SUBMIT YOUR TRACK\n\n"
        "Send your audio file now with the caption:\n\nArtistName - SongTitle\n\n"
        "Example:\nDJ Rankin - War Ready\n\n"
        "BAZRAGOD will personally review every submission.\n"
        "Approved tracks go live on BazraGod Radio.\n\n"
        f"Reward: +{POINTS['submit_track']} pts\n\nType /cancel to go back."
    )

async def handle_artist_submission_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    submission_sessions.pop(uid, None)
    audio       = update.message.audio
    caption     = (update.message.caption or "").strip()
    parts       = caption.split("-", 1)
    artist_name = parts[0].strip() if parts else name
    song_title  = parts[1].strip() if len(parts) > 1 else (audio.title or "Untitled")
    file_id     = audio.file_id
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO artist_submissions (telegram_id, username, artist_name, song_title, file_id) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (uid, name, artist_name, song_title, file_id),
        )
        sub_id = cur.fetchone()[0]
        conn.commit()
    finally:
        release_db(conn)
    pts = award_points(uid, "submit_track", name)
    await update.message.reply_text(
        f"SUBMISSION RECEIVED!\n\nArtist: {artist_name}\nTrack: {song_title}\nRef: {sub_id}\n\n"
        f"BAZRAGOD reviews every submission personally.\nApproved tracks go live on BazraGod Radio.\n\n+{pts} pts",
        reply_markup=main_menu,
    )
    try:
        await context.bot.send_message(OWNER_ID,
            f"ARTIST SUBMISSION #{sub_id}\n\nArtist: {artist_name}\nTrack: {song_title}\nFan: @{name} ({uid})\n\n"
            f"/approve_submission {sub_id}\n/reject_submission {sub_id}")
        await context.bot.forward_message(chat_id=OWNER_ID, from_chat_id=uid, message_id=update.message.message_id)
    except Exception:
        pass

async def approve_submission_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /approve_submission <id>")
        return
    sub_id = int(args[0])
    conn   = get_db()
    cur    = conn.cursor()
    try:
        cur.execute(
            "UPDATE artist_submissions SET status = 'approved' WHERE id = %s RETURNING telegram_id, artist_name, song_title, file_id",
            (sub_id,),
        )
        row = cur.fetchone()
        if row:
            tid, artist, song, file_id = row
            cur.execute("INSERT INTO songs (title, file_id) VALUES (%s, %s) ON CONFLICT (title) DO NOTHING", (f"{artist} {song}", file_id))
            conn.commit()
            invalidate_playlist_cache()
        else:
            conn.commit()
    finally:
        release_db(conn)
    if row:
        await update.message.reply_text(f"Submission #{sub_id} approved.\n{row[1]} {row[2]} added to BazraGod Radio.")
        try:
            await context.bot.send_message(row[0],
                f"YOUR TRACK WAS APPROVED!\n\n{row[1]} {row[2]}\n\nNow live on BazraGod Radio.\n\nParish 14 Nation. BAZRAGOD.")
        except Exception:
            pass
    else:
        await update.message.reply_text("Submission not found.")

async def reject_submission_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /reject_submission <id>")
        return
    sub_id = int(args[0])
    conn   = get_db()
    cur    = conn.cursor()
    try:
        cur.execute("UPDATE artist_submissions SET status = 'rejected' WHERE id = %s RETURNING id", (sub_id,))
        row = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)
    await update.message.reply_text(f"Submission #{sub_id} rejected." if row else "Not found.")

async def list_submissions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, artist_name, song_title, status, submitted_at FROM artist_submissions ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    if not rows:
        await update.message.reply_text("No submissions yet.")
        return
    text = "ARTIST SUBMISSIONS\n\n"
    for r in rows:
        badge = "approved" if r[3] == "approved" else "rejected" if r[3] == "rejected" else "pending"
        text += f"[{r[0]}] {badge} {r[1]} {r[2]}\n{r[4].strftime('%d/%m %H:%M')}\n\n"
    await update.message.reply_text(text)

async def mood_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mood_sessions[uid] = True
    await update.message.reply_text(
        "MOOD RADIO\n\nMAXIMUS reads your energy and selects the perfect BAZRAGOD track.\n\n"
        "How are you feeling right now?\n\nExamples:\nmotivated\nreflective\nfocused\ncelebrating\n\nType your mood"
    )

async def mood_radio_handler(uid, text, update, context):
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
    await update.message.reply_text(f"MAXIMUS reading your energy...\n\nMood: {text}")
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
            caption=f"MOOD RADIO\n\nYour energy: {text}\nMAXIMUS selected: {title}\n{heat}  {plays:,} plays\n\n+{pts} pts",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Like",   callback_data=f"like:{sid}"),
                InlineKeyboardButton("Donate", callback_data=f"donate:{sid}"),
            ]]),
        )
        await maybe_prophecy(uid, name, context)
    return True

async def lyric_cipher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cipher_sessions[uid] = True
    await update.message.reply_text(
        "LYRIC CIPHER\n\nYou vs MAXIMUS.\n\nDrop your verse below. MAXIMUS responds in BAZRAGOD style.\n\nWrite your bars\n\nType /cancel to exit."
    )

async def cipher_handler(uid, text, update, context):
    if uid not in cipher_sessions:
        return False
    cipher_sessions.pop(uid)
    name = get_username(update)
    await update.message.reply_text("MAXIMUS is writing the response...")
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are MAXIMUS writing bars in BAZRAGOD lyric style. Jamaican-influenced. Sovereign, confident, Patois influence, spiritual power. Exactly 4 bars. No explicit language."},
                {"role": "user",   "content": f"Fan verse:\n{text}\n\nRespond with 4 bars in BAZRAGOD style."},
            ],
            max_tokens=200,
        )
        verse = response.choices[0].message.content
        pts   = award_points(uid, "cipher", name)
        await update.message.reply_text(f"BAZRAGOD CIPHER\n\nYou:\n{text}\n\nMAXIMUS:\n{verse}\n\n+{pts} pts")
        await maximus_speak(context, uid, verse)
        await maybe_prophecy(uid, name, context)
    except Exception as e:
        await update.message.reply_text(f"Cipher error: {str(e)}")
    return True

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
    song_list = "\n".join([f"{s[0]}" for s in songs])
    await update.message.reply_text(
        f"REQUEST A TRACK\n\nType the song name.\n\nAvailable:\n{song_list}\n\nMAXIMUS will spin it on air.\n\nType /cancel to go back."
    )

async def request_handler(uid, text, update, context):
    if uid not in request_sessions:
        return False
    request_sessions.pop(uid)
    name = get_username(update)
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("INSERT INTO song_requests (telegram_id, username, song_title) VALUES (%s, %s, %s) RETURNING id", (uid, name, text))
        req_id = cur.fetchone()[0]
        conn.commit()
    finally:
        release_db(conn)
    pts = award_points(uid, "request_song", name)
    await update.message.reply_text(
        f"REQUEST QUEUED!\n\nSong: {text}\nRequest #{req_id}\n\nMAXIMUS will spin it on air.\n\n+{pts} pts",
        reply_markup=main_menu,
    )
    return True

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
    bar      = "X" * filled + "." * (10 - filled)
    await update.message.reply_text(
        f"PARISH 14 CHARITY FUND\n\nProgress to ${CHARITY_THRESHOLD} milestone:\n[{bar}] {progress}/{CHARITY_THRESHOLD}\n\nEvery donation powers the movement.\n\nPay then tap below",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"CashApp ${CHARITY_PRICE:.2f}", url=CASHAPP)],
            [InlineKeyboardButton(f"PayPal ${CHARITY_PRICE:.2f}",  url=PAYPAL)],
            [InlineKeyboardButton("I've Donated", callback_data="charity:confirm")],
        ]),
    )

async def charity_confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name
    pts  = award_points(uid, "charity", name)
    await query.message.reply_text(f"THANK YOU!\n\nYour contribution supports independent music.\nParish 14 Nation.\n\n+{pts} pts")

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
            f"PARISH 14 SUPPORTER\n\nActive!\nExpires: {exp_str}\n\n"
            f"Benefits:\nNation Elite badge\nPriority radio shoutouts\nEarly access songs\nLeaderboard priority\n\nThank you."
        )
        return
    await update.message.reply_text(
        f"PARISH 14 SUPPORTER\n\n${SUPPORTER_PRICE:.2f}/month\n\n"
        f"Benefits:\nNation Elite badge\nPriority radio shoutouts\nEarly access songs\nLeaderboard priority\n\n"
        f"Tip: Invite 25 friends and get 7-day Supporter FREE!\n\nPay then tap below",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"CashApp ${SUPPORTER_PRICE:.2f}/mo", url=CASHAPP)],
            [InlineKeyboardButton(f"PayPal ${SUPPORTER_PRICE:.2f}/mo",  url=PAYPAL)],
            [InlineKeyboardButton("I've Paid Activate Me", callback_data="supporter:verify")],
        ]),
    )

async def supporter_verify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name
    await query.message.reply_text("Payment submitted. Admin will activate your status.")
    try:
        await context.bot.send_message(OWNER_ID, f"SUPPORTER REQUEST\nFan: @{name} ({uid})\n\n/activate_supporter {uid}")
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
        cur.execute("UPDATE fans SET is_supporter = TRUE, tier = 'Nation Elite', supporter_expires = %s WHERE telegram_id = %s RETURNING username",
                    (expires, fan_id))
        row = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)
    if row:
        award_points(fan_id, "supporter_sub")
        await update.message.reply_text(f"@{row[0]} activated. Expires: {expires}")
        try:
            await context.bot.send_message(fan_id,
                f"PARISH 14 SUPPORTER ACTIVATED!\n\nNation Elite unlocked.\nExpires: {expires.strftime('%B %d, %Y')}\n\nBAZRAGOD sees you.")
        except Exception:
            pass
    else:
        await update.message.reply_text("Fan not found.")

async def voice_wall_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["voice_wall_active"] = True
    await update.message.reply_text(
        "FAN VOICE WALL\n\nRecord a voice message and send it here.\n\nApproved shoutouts play LIVE on BazraGod Radio!\n\n"
        "Tips:\nShout out BAZRAGOD\nSay your city\nBig up Parish 14 Nation\nUnder 30 seconds\n\nRecord and send now\n\nType /cancel to go back."
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
        cur.execute("INSERT INTO voice_wall (telegram_id, username, file_id) VALUES (%s, %s, %s) RETURNING id", (uid, name, voice.file_id))
        sid = cur.fetchone()[0]
        conn.commit()
    finally:
        release_db(conn)
    pts = award_points(uid, "voice_wall", name)
    await update.message.reply_text(f"Submission #{sid} received!\nApproved voices play on BazraGod Radio.\n\n+{pts} pts", reply_markup=main_menu)
    try:
        await context.bot.send_message(OWNER_ID, f"VOICE #{sid}\nFan: @{name} ({uid})\n/approve_voice {sid}\n/reject_voice {sid}")
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
        await update.message.reply_text(f"Voice #{vid} approved.")
        try:
            await context.bot.send_message(row[0], "YOUR VOICE WAS APPROVED!\nIt plays live on BazraGod Radio.\nParish 14.")
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
    await update.message.reply_text(f"Voice #{vid} rejected." if row else "Not found.")

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
    text = "VOICE WALL\n\n"
    for r in rows:
        text += f"[{r[0]}] @{r[1]} {r[3].strftime('%d/%m')} {r[2]}\n"
    await update.message.reply_text(text)

async def handle_audio_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid   = update.effective_user.id
    audio = update.message.audio
    if not audio:
        return
    if not is_admin(uid):
        if submission_sessions.get(uid):
            await handle_artist_submission_audio(update, context)
        return
    title   = audio.title or audio.file_name or (update.message.caption or "").strip() or "Untitled"
    file_id = audio.file_id
    caption = (update.message.caption or "").strip().lower()

    vault_match = re.search(r"#vault\s+(\d+)", caption)
    if vault_match:
        req_pts = int(vault_match.group(1))
        await _save_vault_audio(update.message, file_id, title, req_pts)
        invalidate_playlist_cache()
        return

    tag_map = {
        "#song":     ("songs",         "Song"),
        "#beat":     ("beats",         "Beat"),
        "#drop":     ("drops",         "Drop"),
        "#promo":    ("promos",        "Audio Promo"),
        "#announce": ("announcements", "Announcement"),
        "#aurora":   ("dj:aurora",     "DJ Aurora Drop"),
        "#colorred": ("dj:colorred",   "DJ Color Red Drop"),
        "#maximus":  ("dj:maximus",    "DJ Maximus Drop"),
        "#eclipse":  ("dj:eclipse",    "DJ Eclipse Drop"),
    }
    for tag, (dest, label) in tag_map.items():
        if tag in caption:
            await _save_classified_audio(update.message, file_id, title, dest, label)
            invalidate_playlist_cache()
            return

    upload_sessions[uid] = {"file_id": file_id, "title": title}
    await update.message.reply_text(
        f"CLASSIFY UPLOAD\n\nTitle: {title}\n\nWhat type is this audio?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Song",              callback_data="upload:songs")],
            [InlineKeyboardButton("Beat",              callback_data="upload:beats")],
            [InlineKeyboardButton("Drop",              callback_data="upload:drops")],
            [InlineKeyboardButton("Audio Promo",       callback_data="upload:promos")],
            [InlineKeyboardButton("Announcement",      callback_data="upload:announcements")],
            [InlineKeyboardButton("Vault 1000 pts",    callback_data="upload:vault:1000")],
            [InlineKeyboardButton("Vault 2500 pts",    callback_data="upload:vault:2500")],
            [InlineKeyboardButton("Vault 5000 pts",    callback_data="upload:vault:5000")],
            [InlineKeyboardButton("DJ Aurora Drop",    callback_data="upload:dj:aurora")],
            [InlineKeyboardButton("DJ Color Red Drop", callback_data="upload:dj:colorred")],
            [InlineKeyboardButton("DJ Maximus Drop",   callback_data="upload:dj:maximus")],
            [InlineKeyboardButton("DJ Eclipse Drop",   callback_data="upload:dj:eclipse")],
        ]),
    )

async def _save_vault_audio(msg, file_id, title, required_points):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("INSERT INTO vault (title, file_id, required_points) VALUES (%s, %s, %s) RETURNING id", (title, file_id, required_points))
        new_id = cur.fetchone()[0]
        conn.commit()
    finally:
        release_db(conn)
    await msg.reply_text(f"Vault item added. ID: {new_id}\nTitle: {title}\nRequired: {required_points:,} pts")

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
    if dest.startswith("vault:"):
        req_pts = int(dest.split(":")[1])
        await _save_vault_audio(query.message, session["file_id"], session["title"], req_pts)
        invalidate_playlist_cache()
        return
    label_map = {
        "songs": "Song", "beats": "Beat", "drops": "Drop",
        "promos": "Audio Promo", "announcements": "Announcement",
        "dj:aurora": "DJ Aurora", "dj:colorred": "DJ Color Red",
        "dj:maximus": "DJ Maximus", "dj:eclipse": "DJ Eclipse",
    }
    await _save_classified_audio(query.message, session["file_id"], session["title"], dest, label_map.get(dest, "Added"))
    invalidate_playlist_cache()

async def _save_classified_audio(msg, file_id, title, dest, label):
    conn = get_db()
    cur  = conn.cursor()
    try:
        if dest.startswith("dj:"):
            dj_key = dest.split(":")[1]
            cur.execute("INSERT INTO dj_drops (dj, title, file_id) VALUES (%s, %s, %s) RETURNING id", (dj_key, title, file_id))
            new_id = cur.fetchone()[0]
            conn.commit()
            text = f"{label} added. ID: {new_id}\nTitle: {title}"
        elif dest == "songs":
            cur.execute("SELECT id FROM songs WHERE LOWER(title) = LOWER(%s)", (title,))
            if cur.fetchone():
                text = f"Song '{title}' already exists. Skipped."
            else:
                cur.execute("INSERT INTO songs (title, file_id) VALUES (%s, %s) RETURNING id", (title, file_id))
                new_id = cur.fetchone()[0]
                conn.commit()
                text = f"{label} added. ID: {new_id}\nTitle: {title}"
        else:
            cur.execute(f"INSERT INTO {dest} (title, file_id) VALUES (%s, %s) RETURNING id", (title, file_id))
            new_id = cur.fetchone()[0]
            conn.commit()
            text = f"{label} added. ID: {new_id}\nTitle: {title}"
    finally:
        release_db(conn)
    await msg.reply_text(text)

async def youtube_detector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    if not re.search(r"youtube\.com|youtu\.be", text):
        return False
    dj  = get_current_dj()
    now = datetime.now().strftime("%I:%M %p")
    msg = f"NEW BAZRAGOD VIDEO DETECTED\n\n{dj['name']} {now}\n\nNew BAZRAGOD video just landed. Go watch it NOW.\n\n{text}"
    await dj_speak(context, update.effective_user.id, "Attention Parish 14 Nation. New BAZRAGOD video dropped. Go watch it now.")
    await update.message.reply_text(msg)
    try:
        await _broadcast_to_all(context, msg)
    except Exception:
        pass
    return True

async def social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    pts = award_points(uid, "follow_social", get_username(update))
    await update.message.reply_text(
        f"BAZRAGOD SOCIAL\n\nFollow on every platform.\n\n+{pts} pts",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(p, url=u)] for p, u in SOCIALS.items()]),
    )

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    pts = award_points(uid, "support_artist", get_username(update))
    await update.message.reply_text(
        f"SUPPORT BAZRAGOD\n\nNo label takes a cut here.\nEvery dollar goes directly to the music.\n\n+{pts} pts",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]),
    )

async def merch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "PARISH 14 MERCH\n\nOfficial BAZRAGOD clothing.\nWear the nation.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{MERCH_ITEMS['tshirt'][0]} ${MERCH_ITEMS['tshirt'][1]}",     callback_data="merch:tshirt")],
            [InlineKeyboardButton(f"{MERCH_ITEMS['pullover'][0]} ${MERCH_ITEMS['pullover'][1]}", callback_data="merch:pullover")],
        ]),
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
    await query.message.reply_text(
        f"PARISH 14 ORDER\n\nItem: {item_name}\nPrice: ${price}\n\nAfter payment send admin:\nYour size\nShipping address\nPayment proof\n\nParish 14.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]),
    )

async def music_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "BAZRAGOD MUSIC STORE\n\nDirect from the artist.\nNo streaming cuts. No label fees.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{STORE_ITEMS['single'][0]} ${STORE_ITEMS['single'][1]}",       callback_data="store:single")],
            [InlineKeyboardButton(f"{STORE_ITEMS['bundle'][0]} ${STORE_ITEMS['bundle'][1]}",       callback_data="store:bundle")],
            [InlineKeyboardButton(f"{STORE_ITEMS['exclusive'][0]} ${STORE_ITEMS['exclusive'][1]}", callback_data="store:exclusive")],
        ]),
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
        cur.execute("INSERT INTO purchases (telegram_id, item, price) VALUES (%s, %s, %s) RETURNING id", (uid, item_name, price))
        purchase_id = cur.fetchone()[0]
        conn.commit()
    finally:
        release_db(conn)
    await query.message.reply_text(
        f"ORDER #{purchase_id}\n\nItem: {item_name}\nPrice: ${price}\n\nSend payment then message admin with proof.\nDownload unlocked.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]),
    )
    try:
        await context.bot.send_message(OWNER_ID, f"NEW PURCHASE\n\nOrder: #{purchase_id}\nFan: @{name} ({uid})\nItem: {item_name}\nPrice: ${price}")
    except Exception:
        pass

async def booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"BOOK BAZRAGOD\n\nContact:\n{BOOKING_EMAIL}\n\nInclude:\nEvent type\nDate and location\nBudget\nContact number\n\nBAZRAGOD is global. Parish 14 Nation."
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
        await update.message.reply_text("No fans mapped yet. Share your location!")
        return
    text = f"PARISH 14 FAN RADAR\n\nTotal fans mapped: {total}\n\n"
    for i, (country, fans) in enumerate(rows):
        text += f"{i+1}. {country} {fans} fans\n"
    text += "\nThis is where BAZRAGOD's army stands."
    await update.message.reply_text(text)

async def wisdom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    pts = award_points(uid, "wisdom", get_username(update))
    await update.message.reply_text(f"Royal Wisdom\n\n{random.choice(QUOTES)}\n\n+{pts} pts")

async def fitness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    pts = award_points(uid, "fitness", get_username(update))
    await update.message.reply_text(f"{FITNESS_MSG}\n\n+{pts} pts")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "PARISH 14 LEADERBOARD\n\nChoose time period",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Today",    callback_data="lb:today"),
            InlineKeyboardButton("Week",     callback_data="lb:week"),
            InlineKeyboardButton("All Time", callback_data="lb:alltime"),
        ]]),
    )

async def leaderboard_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        lb_type = query.data.split(":")[1]
    except Exception:
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        if lb_type == "today":
            cur.execute("""
                SELECT f.username, COALESCE(SUM(pl.pts), 0) as pts, f.tier, f.is_supporter
                FROM fans f
                LEFT JOIN point_log pl ON f.telegram_id = pl.telegram_id
                    AND pl.logged_at > NOW() - INTERVAL '24 hours'
                GROUP BY f.username, f.tier, f.is_supporter
                ORDER BY pts DESC LIMIT 10
            """)
            label = "TODAY TOP FANS"
        elif lb_type == "week":
            cur.execute("""
                SELECT f.username, COALESCE(SUM(pl.pts), 0) as pts, f.tier, f.is_supporter
                FROM fans f
                LEFT JOIN point_log pl ON f.telegram_id = pl.telegram_id
                    AND pl.logged_at > NOW() - INTERVAL '7 days'
                GROUP BY f.username, f.tier, f.is_supporter
                ORDER BY pts DESC LIMIT 10
            """)
            label = "THIS WEEK TOP FANS"
        else:
            cur.execute("SELECT username, points, tier, is_supporter FROM fans ORDER BY points DESC LIMIT 10")
            label = "ALL TIME LEGENDS"
        rows = cur.fetchall()
    finally:
        release_db(conn)
    text = f"PARISH 14 {label}\n\n"
    for i, (username, points, tier, is_sup) in enumerate(rows):
        label_str = f"@{username}" if username else "Anonymous"
        badge     = " Supporter" if is_sup else ""
        text     += f"{i+1}. {label_str}{badge}\n{points:,} pts {tier}\n\n"
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Today",    callback_data="lb:today"),
            InlineKeyboardButton("Week",     callback_data="lb:week"),
            InlineKeyboardButton("All Time", callback_data="lb:alltime"),
        ]]),
    )

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
    pts, invites, tier = row if row else (0, 0, "Fan")
    station  = get_station_rank(pts)
    next_msg = get_next_station_rank_info(pts)
    next_tier_msg = ""
    for threshold, label in sorted(REFERRAL_TIERS.items()):
        if invites < threshold:
            next_tier_msg = f"Invite {threshold - invites} more friends to reach {label}"
            break
    await update.message.reply_text(
        f"YOUR STATS\n\n"
        f"Points: {pts:,}\nGlobal Rank: #{rank}\n"
        f"Nation Tier: {tier}\nStation Rank: {station}\nInvites: {invites}\n\n"
        f"{next_msg}\n{next_tier_msg}\n\nKeep grinding to climb"
    )

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
        cur.execute("SELECT COUNT(*) FROM vault_unlocks WHERE telegram_id = %s", (uid,))
        vault_count = cur.fetchone()[0]
    finally:
        release_db(conn)
    if not row:
        await update.message.reply_text("Send /start first.")
        return
    username, points, invites, tier, city, country, joined_at, is_sup, sup_exp, lang = row
    display      = f"@{username}" if username else name
    location     = f"{city}, {country}" if city else "Not shared yet"
    joined       = joined_at.strftime("%B %Y") if joined_at else "Unknown"
    sup_badge    = " Supporter" if is_sup else ""
    sup_line     = f"\nExpires: {sup_exp.strftime('%d %b %Y')}" if is_sup and sup_exp else ""
    lang_name    = SUPPORTED_LANGUAGES.get(lang, "English")
    station      = get_station_rank(points)
    next_station = get_next_station_rank_info(points)
    await update.message.reply_text(
        f"FAN PROFILE\n\n"
        f"Name: {display}{sup_badge}\n"
        f"Nation Tier: {tier}\nStation Rank: {station}\n"
        f"Points: {points:,}\nGlobal Rank: #{rank_pos}\n"
        f"Invites: {invites}\nVault Items: {vault_count} unlocked\n"
        f"City: {location}\nLanguage: {lang_name}\nJoined: {joined}{sup_line}\n\n"
        f"{next_station}"
    )

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
        await update.message.reply_text("DAILY MISSION\n\nAlready completed today!\n\nCome back tomorrow.")
        return
    mission_text = random.choice(MISSIONS)
    await update.message.reply_text(
        f"DAILY MISSION\n\n{mission_text}\n\nReward: +{POINTS['mission']} pts\n\nComplete it then tap below",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Mark Complete", callback_data=f"mission:complete:{uid}")]]),
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
            await query.message.reply_text("Already completed today!")
            return
        cur.execute("INSERT INTO missions (telegram_id, mission_date, completed) VALUES (%s, %s, TRUE) ON CONFLICT (telegram_id, mission_date) DO UPDATE SET completed = TRUE", (uid, today))
        conn.commit()
    finally:
        release_db(conn)
    name = query.from_user.username or query.from_user.first_name
    pts  = award_points(uid, "mission", name)
    lang = get_user_lang(uid)
    await query.message.reply_text(f"MISSION COMPLETE!\n\n+{pts} points\n\n{t(lang, 'mission_done')}")
    await maybe_prophecy(uid, name, context)

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
    invites    = row[0] if row else 0
    tier       = row[1] if row else "Fan"
    milestones = (
        f"1 invite   +{POINTS['invite_friend']} pts\n"
        f"5 invites  Exclusive beat unlock\n"
        f"10 invites Vault song unlock\n"
        f"25 invites 7-day Supporter FREE\n"
        f"50 invites Nation Elite PERMANENT"
    )
    await update.message.reply_text(
        f"REFERRAL SYSTEM\n\nYour invite link:\n{link}\n\nInvites: {invites}\nTier: {tier}\n\n"
        f"MILESTONE REWARDS:\n{milestones}\n\nEvery invite = +{POINTS['invite_friend']} pts\nBuild the Parish 14 army.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Share Link", url=f"https://t.me/share/url?url={link}&text=Join+Parish+14+Nation+on+BazraGod+Radio")
        ]]),
    )

async def location_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("Send Location", request_location=True)], ["Back to Menu"]],
        resize_keyboard=True, one_time_keyboard=True,
    )
    await update.message.reply_text(f"Share your location.\n\nPut your city on the Parish 14 fan map.\nEarn +{POINTS['share_location']} pts", reply_markup=kb)

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

async def astro_reading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not openai_client:
        await update.message.reply_text("ASTRO READING\n\nMAXIMUS offline. OPENAI_API_KEY required.")
        return
    uid = update.effective_user.id
    astro_sessions[uid] = {"step": "birth_date"}
    await update.message.reply_text("MAXIMUS ASTRO READING\n\nStep 1 of 3\n\nEnter your birth date:\nFormat: DD/MM/YYYY\n\nExample: 15/03/1990")

async def astro_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = get_username(update)
    if uid not in astro_sessions:
        return False
    session = astro_sessions[uid]
    text    = update.message.text.strip()
    step    = session.get("step")
    if step == "birth_date":
        session["birth_date"] = text
        session["step"]       = "birth_time"
        await update.message.reply_text("Birth date saved.\n\nStep 2 of 3\n\nEnter birth time:\nFormat: HH:MM AM/PM\n\nType unknown if unsure.")
        return True
    if step == "birth_time":
        session["birth_time"] = text
        session["step"]       = "location"
        await update.message.reply_text("Birth time saved.\n\nStep 3 of 3\n\nEnter birth city and current city:\n\nFormat: BirthCity, CurrentCity")
        return True
    if step == "location":
        session["step"] = "generating"
        await update.message.reply_text("MAXIMUS is reading your stars...\n\nStand by.")
        try:
            parts        = text.split(",")
            birth_city   = parts[0].strip() if parts else "Unknown"
            current_city = parts[1].strip() if len(parts) > 1 else birth_city
            response     = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are MAXIMUS astrocartography reader. Generate a powerful documentary-style reading in 4 paragraphs: current location energy, best for creativity and music, best for business and wealth, power advice now. No fear language. End with a sovereign statement."},
                    {"role": "user",   "content": f"Birth Date: {session.get('birth_date')}\nBirth Time: {session.get('birth_time')}\nBirth City: {birth_city}\nCurrent City: {current_city}\n\nGenerate a full astrocartography reading."},
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
            await update.message.reply_text(f"YOUR ASTRO READING\n\n{reading}\n\n+{pts} pts")
            await maximus_speak(context, uid, reading[:500])
            await maybe_prophecy(uid, name, context)
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}\n\nTry again later.")
        finally:
            astro_sessions.pop(uid, None)
        return True
    return False

async def ai_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not openai_client:
        await update.message.reply_text("MAXIMUS is offline. OPENAI_API_KEY not set.")
        return
    uid  = update.effective_user.id
    name = get_username(update)
    context.user_data["ai_active"]  = True
    context.user_data["ai_history"] = context.user_data.get("ai_history", [])
    pts = award_points(uid, "ai_chat", name)
    await update.message.reply_text(
        f"MAXIMUS ONLINE\n\nRoyal AI of BAZRAGOD.\nManager. Publicist. Radio DJ. Strategist.\n\nAsk me anything.\nType /menu to return.\n\n+{pts} pts"
    )

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("ai_active") or not openai_client:
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
        await update.message.reply_text(f"MAXIMUS\n\n{reply}")
        await maximus_speak(context, uid, reply)
        await maybe_prophecy(uid, name, context)
    except Exception as e:
        await update.message.reply_text(f"MAXIMUS error: {str(e)}")
    return True

async def community(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"
    await update.message.reply_text(
        "PARISH 14 COMMUNITY\n\nThe nation lives here. Connect through the movement.\n\n"
        "Every fan who joins is a soldier.\nEvery share grows the army.\n\n"
        f"Share your invite link:\n{link}\n\nFollow BAZRAGOD on all platforms.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Instagram", url=SOCIALS["Instagram"])],
            [InlineKeyboardButton("TikTok",    url=SOCIALS["TikTok"])],
            [InlineKeyboardButton("YouTube",   url=SOCIALS["YouTube"])],
            [InlineKeyboardButton("X",          url=SOCIALS["X"])],
        ]),
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "PARISH 14 HELP\n\n"
        "Music catalog    BAZRAGOD MUSIC\n"
        "Live radio       BazraGod Radio\n"
        "Points and rank  My Points\n"
        "Exclusive content Secret Vault\n"
        "Submit your track Submit Track\n"
        "Grow the army    Refer a Friend\n"
        "Supporter        Supporter\n"
        "Language         Language\n\n"
        "COMMANDS\n"
        "/start  Enter the platform\n"
        "/menu   Return to main menu\n"
        "/cancel Cancel current action\n"
        "/lang   Change language\n"
        "/vault  Secret vault\n"
        "/submit Submit your track\n"
        "/help   This help menu\n\n"
        f"Booking: {BOOKING_EMAIL}\n\n"
        "Parish 14 Nation. BAZRAGOD."
    )

async def send_weekly_intel():
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM fans");                                                        total_fans      = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fans WHERE joined_at > NOW() - INTERVAL '7 days'");           new_fans        = cur.fetchone()[0]
        cur.execute("SELECT SUM(points) FROM fans");                                                     total_pts       = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM fan_locations");                                               mapped          = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(country,'Unknown'), COUNT(*) FROM fan_locations GROUP BY country ORDER BY 2 DESC LIMIT 3"); top_countries = cur.fetchall()
        cur.execute("SELECT username, points FROM fans ORDER BY points DESC LIMIT 3");                   top_fans        = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM purchases WHERE status = 'pending'");                          pending         = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM voice_wall WHERE status = 'pending'");                         pending_voices  = cur.fetchone()[0]
        cur.execute("SELECT title, plays, likes, donations FROM songs ORDER BY plays DESC LIMIT 3");     top_songs       = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM fans WHERE is_supporter = TRUE");                              supporters      = cur.fetchone()[0]
        cur.execute("SELECT SUM(donations) FROM songs");                                                 total_donations = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM radio_sessions WHERE last_ping > NOW() - INTERVAL '30 minutes'"); live         = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM vault");                                                       vault_items     = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM artist_submissions WHERE status = 'pending'");                 pending_subs    = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM radio_history WHERE played_at > NOW() - INTERVAL '7 days'");  songs_aired     = cur.fetchone()[0]
    finally:
        release_db(conn)
    countries_text = "\n".join([f"  {c} {f} fans" for c, f in top_countries]) or "  None yet"
    fans_text      = "\n".join([f"  @{f} {p} pts" for f, p in top_fans if f]) or "  None yet"
    songs_text     = "\n".join([f"  {t_} {p_:,} plays {calculate_heat(l_, d_, p_)}" for t_, p_, l_, d_ in top_songs]) or "  None"
    report = (
        f"WEEKLY INTEL REPORT\n"
        f"Week: {datetime.now().strftime('%d %B %Y')}\n\n"
        f"Live Now:            {live}\n"
        f"Total Fans:          {total_fans}\n"
        f"New This Week:       {new_fans}\n"
        f"Total Points:        {total_pts:,}\n"
        f"Supporters:          {supporters}\n"
        f"Fans Mapped:         {mapped}\n"
        f"Total Donations:     {total_donations}\n"
        f"Pending Orders:      {pending}\n"
        f"Pending Voices:      {pending_voices}\n"
        f"Pending Submissions: {pending_subs}\n"
        f"Vault Items:         {vault_items}\n"
        f"Songs Aired:         {songs_aired} this week\n\n"
        f"TOP COUNTRIES:\n{countries_text}\n\n"
        f"TOP FANS:\n{fans_text}\n\n"
        f"TOP SONGS:\n{songs_text}\n\n"
        f"MAXIMUS INTEL SYSTEM v15.000"
    )
    try:
        await telegram_app.bot.send_message(OWNER_ID, report)
        await maximus_speak_direct(telegram_app.bot, OWNER_ID,
            f"Weekly intel ready. {new_fans} new fans this week. {total_fans} total soldiers. The movement grows.")
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
    playlist = get_cached_playlist()
    rotation_preview = " ".join([
        {"song": "SONG", "drop": "DROP", "beat": "BEAT", "ad": "AD", "announcement": "ANN"}.get(p["type"], "?")
        for p in playlist[:10]
    ]) if playlist else "Empty"
    await update.message.reply_text(
        f"I.A.A.I.M.O ADMIN PANEL v15.000\n\n"
        f"Channel Radio: {'ACTIVE' if radio_loop_running else 'STANDBY'}\n"
        f"Channel ID: {RADIO_CHANNEL_ID or 'NOT SET'}\n"
        f"Playlist Cache: {len(playlist)} items\n\n"
        f"ROTATION PREVIEW:\n{rotation_preview}\n\n"
        f"ANALYTICS\n/stats  /radar  /weekly  /orders\n\n"
        f"CONTENT\n/list_songs   /delete_song id\n/list_beats   /delete_beat id\n"
        f"/list_drops   /delete_drop id\n/list_dj_drops\n\n"
        f"VAULT\n/list_vault\n/delete_vault id\n\n"
        f"SUBMISSIONS\n/list_submissions\n/approve_submission id\n/reject_submission id\n\n"
        f"PREMIERE\n/premiere song_id\n\nRADIO\n/start_radio\n\n"
        f"VOICE WALL\n/list_voices\n/approve_voice id\n/reject_voice id\n\n"
        f"REQUESTS\n/list_requests\n\n"
        f"SUPPORTERS\n/activate_supporter telegram_id\n\n"
        f"BROADCAST\n/broadcast\n/shoutout @username\n/announce message\n\n"
        f"UPLOAD\nSend audio smart classify menu\n"
        f"Caption tags: #song #beat #drop #promo #announce\n"
        f"#vault 2000 adds to vault at 2000 pts\n"
        f"#aurora #colorred #maximus #eclipse"
    )

async def start_radio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not RADIO_CHANNEL_ID:
        await update.message.reply_text("RADIO_CHANNEL_ID not set.\n\nAdd in Railway:\nRADIO_CHANNEL_ID = -100XXXXXXXXX\n\nGet channel ID via @userinfobot.")
        return
    if radio_loop_running:
        await update.message.reply_text("Channel radio loop is already running.")
        return
    asyncio.run_coroutine_threadsafe(channel_radio_loop(), loop)
    playlist = get_cached_playlist()
    await update.message.reply_text(
        f"Channel radio loop STARTED.\n\nBroadcasting to: {RADIO_CHANNEL_ID}\n"
        f"Playlist items: {len(playlist)}\nCache TTL: {PLAYLIST_CACHE_TTL}s\n"
        f"Anti-repeat: Last 8 songs excluded\n\nStation is live. Parish 14 Nation."
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM fans");                                                  total_fans  = cur.fetchone()[0]
        cur.execute("SELECT SUM(points) FROM fans");                                               total_pts   = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM songs");                                                 total_songs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM beats");                                                 total_beats = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM drops");                                                 total_drops = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM announcements");                                         total_ann   = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM vault");                                                 vault_items = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM artist_submissions WHERE status = 'pending'");           pending_subs= cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM dj_drops");                                             total_dj    = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fan_locations");                                        mapped      = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM purchases WHERE status = 'pending'");                   pending     = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM voice_wall WHERE status = 'pending'");                  pv          = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fans WHERE is_supporter = TRUE");                       supporters  = cur.fetchone()[0]
        cur.execute("SELECT SUM(donations) FROM songs");                                          total_donations = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM radio_sessions WHERE last_ping > NOW() - INTERVAL '30 minutes'"); live = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM song_requests WHERE played = FALSE");                   pending_reqs= cur.fetchone()[0]
        cur.execute("SELECT title, plays FROM songs ORDER BY plays DESC LIMIT 1");                top_song    = cur.fetchone()
        cur.execute("SELECT username, points FROM fans ORDER BY points DESC LIMIT 1");            top_fan     = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM radio_history");                                        total_hist  = cur.fetchone()[0]
    finally:
        release_db(conn)
    dj       = get_current_dj()
    playlist = get_cached_playlist()
    await update.message.reply_text(
        f"MISERBOT STATS v15.000\n\n"
        f"On Air: {dj['name']}\n"
        f"Channel Radio: {'ACTIVE' if radio_loop_running else 'STANDBY'}\n"
        f"Playlist Items: {len(playlist)} cached\n"
        f"Songs Aired Total: {total_hist}\n"
        f"Live Listeners: {live}\n\n"
        f"Total Fans: {total_fans}\n"
        f"Supporters: {supporters}\n"
        f"Points Given: {total_pts:,}\n"
        f"Total Donations: {total_donations}\n\n"
        f"Songs: {total_songs}\n"
        f"Beats: {total_beats}\n"
        f"Drops: {total_drops}\n"
        f"Announcements: {total_ann}\n"
        f"Vault Items: {vault_items}\n"
        f"Pending Submissions: {pending_subs}\n"
        f"DJ Drops: {total_dj}\n\n"
        f"Fans Mapped: {mapped}\n"
        f"Pending Orders: {pending}\n"
        f"Pending Voices: {pv}\n"
        f"Pending Requests: {pending_reqs}\n\n"
        f"Top Song: {top_song[0] if top_song else 'None'} {top_song[1]:,} plays\n"
        f"Top Fan: @{top_fan[0] if top_fan else 'None'} {top_fan[1] if top_fan else 0} pts"
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
    text = f"TOUR INTELLIGENCE RADAR\nTotal mapped: {total}\n\n"
    for country, fans in rows:
        text += f"{country} {fans} fans\n"
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
        await update.message.reply_text("No pending orders.")
        return
    text = "PENDING ORDERS\n\n"
    for r in rows:
        text += f"Order #{r[0]} {r[2]} ${r[3]}\nFan: {r[1]}\n{r[4].strftime('%d/%m %H:%M')}\n\n"
    await update.message.reply_text(text)

async def weekly_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("Generating weekly intel...")
    await send_weekly_intel()
    await update.message.reply_text("Weekly intel sent.")

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
        row = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)
    if not row:
        await update.message.reply_text("Song not found.")
        return
    title = row[0]
    dj    = get_current_dj()
    now   = datetime.now().strftime("%I:%M %p")
    msg   = (f"WORLD PREMIERE\n\n{dj['name']} BazraGod Radio {now}\n\n"
             f"You are hearing '{title}' for the first time.\n\nBAZRAGOD drops it here first.\nNo label. No middleman. Parish 14 Nation.")
    sent  = await _broadcast_to_all(context, msg)
    invalidate_playlist_cache()
    await update.message.reply_text(f"Premiere broadcast sent to {sent} fans.\nSong '{title}' set to Hot rotation.")

async def list_vault_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, title, required_points FROM vault ORDER BY required_points")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    if not rows:
        await update.message.reply_text("Vault is empty.")
        return
    text = f"VAULT ITEMS {len(rows)}\n\n"
    for r in rows:
        text += f"[{r[0]}] {r[1]} {r[2]:,} pts required\n"
    await update.message.reply_text(text)

async def delete_vault_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /delete_vault <id>")
        return
    row_id = int(args[0])
    conn   = get_db()
    cur    = conn.cursor()
    try:
        cur.execute("DELETE FROM vault WHERE id = %s RETURNING title", (row_id,))
        row = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)
    await update.message.reply_text(f"Vault item deleted: {row[0]}" if row else "Not found.")

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
    text = "SONG REQUESTS\n\n"
    for r in rows:
        text += f"[{r[0]}] {'done' if r[3] else 'pending'} @{r[1]} {r[2]}\n"
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
    text = "DJ DROPS\n\n"
    for r in rows:
        text += f"[{r[0]}] {r[1]} {r[2]}\n"
    await update.message.reply_text(text)

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    pending_broadcasts[OWNER_ID] = True
    await update.message.reply_text("BROADCAST MODE\n\nSend your message now.\n/cancel to abort.")

async def shoutout_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /shoutout @username")
        return
    msg  = f"SHOUTOUT FROM BAZRAGOD\n\nBig up {args[0]} real Parish 14 energy!\n\nI.A.A.I.M.O"
    sent = await _broadcast_to_all(context, msg, speak=True)
    await update.message.reply_text(f"Shoutout sent to {sent} fans.")

async def announce_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /announce <message>")
        return
    msg  = f"OFFICIAL ANNOUNCEMENT\n\n{text}\n\nBAZRAGOD"
    sent = await _broadcast_to_all(context, msg, speak=True)
    await update.message.reply_text(f"Sent to {sent} fans.")

async def _broadcast_to_all(context, text, speak=False):
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
    for d in [pending_broadcasts, astro_sessions, mood_sessions, cipher_sessions, upload_sessions, request_sessions, submission_sessions]:
        d.pop(uid, None)
    context.user_data["ai_active"]         = False
    context.user_data["voice_wall_active"] = False
    await update.message.reply_text("Cancelled.", reply_markup=main_menu)

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    for d in [astro_sessions, mood_sessions, cipher_sessions, upload_sessions, request_sessions, submission_sessions]:
        d.pop(uid, None)
    context.user_data["ai_active"]         = False
    context.user_data["ai_history"]        = []
    context.user_data["voice_wall_active"] = False
    await update.message.reply_text("Main Menu", reply_markup=main_menu)

async def list_songs_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT id, title, plays, likes, donations, rotation FROM songs ORDER BY id")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    rb   = {"A": "Hot", "B": "Mid", "C": "Deep"}
    text = f"SONGS {len(rows)}\n\n"
    for r in rows:
        text += f"[{r[0]}] {rb.get(r[5],'')} {r[1]}\n{calculate_heat(r[3],r[4],r[2])} {r[2]:,} plays  {r[3]} likes  {r[4]} donations\n"
    await update.message.reply_text(text or "Empty.")

async def list_beats_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    await _list_simple(update, "beats", "BEATS")

async def list_drops_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    await _list_simple(update, "drops", "DROPS")

async def _list_simple(update, table, label):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(f"SELECT id, title FROM {table} ORDER BY id")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    text = f"{label} {len(rows)}\n\n"
    for r in rows:
        text += f"[{r[0]}] {r[1]}\n"
    await update.message.reply_text(text or "Empty.")

async def delete_song_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    await _delete_from(update, context, "songs")

async def delete_beat_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    await _delete_from(update, context, "beats")

async def delete_drop_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
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
    invalidate_playlist_cache()
    await update.message.reply_text(f"Deleted: {row[0]}" if row else "Not found.")

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    uid  = update.effective_user.id

    if uid in astro_sessions:
        if await astro_input_handler(update, context):
            return
    if uid in mood_sessions:
        if await mood_radio_handler(uid, text, update, context):
            return
    if uid in cipher_sessions:
        if await cipher_handler(uid, text, update, context):
            return
    if uid in request_sessions:
        if await request_handler(uid, text, update, context):
            return
    if context.user_data.get("ai_active"):
        if await ai_chat_handler(update, context):
            return
    if re.search(r"youtube\.com|youtu\.be", text):
        if await youtube_detector(update, context):
            return
    if uid == OWNER_ID and pending_broadcasts.get(OWNER_ID):
        pending_broadcasts.pop(OWNER_ID)
        sent = await _broadcast_to_all(context, text)
        await update.message.reply_text(f"Broadcast sent to {sent} fans.")
        return

    routes = {
        "BAZRAGOD MUSIC":  music,
        "BazraGod Radio":  radio,
        "Mood Radio":      mood_radio,
        "Lyric Cipher":    lyric_cipher,
        "Top Charts":      top_charts,
        "Trending":        trending,
        "Song Stats":      song_stats,
        "Request Track":   request_track,
        "Supporter":       supporter,
        "Charity":         charity,
        "Beats":           beats,
        "Drops":           drops_menu,
        "Secret Vault":    vault_menu,
        "Submit Track":    submit_track,
        "Leaderboard":     leaderboard,
        "My Points":       my_points,
        "My Profile":      my_profile,
        "Daily Mission":   daily_mission,
        "Support Artist":  support,
        "Social":          social,
        "Music Store":     music_store,
        "Parish 14":       merch,
        "Wisdom":          wisdom,
        "Fitness":         fitness,
        "Share Location":  location_prompt,
        "Refer a Friend":  refer,
        "Fan Radar":       fan_radar,
        "Booking":         booking,
        "Voice Wall":      voice_wall_prompt,
        "Astro Reading":   astro_reading,
        "Language":        language_select,
        "MAXIMUS AI":      ai_assistant,
        "Community":       community,
        "Help":            help_cmd,
        "Back to Menu":    menu_cmd,
    }
    handler = routes.get(text)
    if handler:
        await handler(update, context)

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start",               start))
telegram_app.add_handler(CommandHandler("menu",                menu_cmd))
telegram_app.add_handler(CommandHandler("cancel",              cancel_cmd))
telegram_app.add_handler(CommandHandler("lang",                language_select))
telegram_app.add_handler(CommandHandler("vault",               vault_menu))
telegram_app.add_handler(CommandHandler("submit",              submit_track))
telegram_app.add_handler(CommandHandler("help",                help_cmd))
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
telegram_app.add_handler(CommandHandler("list_vault",          list_vault_cmd))
telegram_app.add_handler(CommandHandler("delete_vault",        delete_vault_cmd))
telegram_app.add_handler(CommandHandler("list_submissions",    list_submissions_cmd))
telegram_app.add_handler(CommandHandler("approve_submission",  approve_submission_cmd))
telegram_app.add_handler(CommandHandler("reject_submission",   reject_submission_cmd))
telegram_app.add_handler(CommandHandler("delete_song",         delete_song_cmd))
telegram_app.add_handler(CommandHandler("delete_beat",         delete_beat_cmd))
telegram_app.add_handler(CommandHandler("delete_drop",         delete_drop_cmd))
telegram_app.add_handler(CommandHandler("list_voices",         list_voices_cmd))
telegram_app.add_handler(CommandHandler("approve_voice",       approve_voice_cmd))
telegram_app.add_handler(CommandHandler("reject_voice",        reject_voice_cmd))
telegram_app.add_handler(CommandHandler("activate_supporter",  activate_supporter_cmd))

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
telegram_app.add_handler(CallbackQueryHandler(leaderboard_cb,      pattern="^lb:"))
telegram_app.add_handler(CallbackQueryHandler(vault_item_cb,       pattern="^vault:"))

telegram_app.add_handler(MessageHandler(filters.LOCATION, location_handler))
telegram_app.add_handler(MessageHandler(filters.VOICE,    voice_wall_submit))
telegram_app.add_handler(MessageHandler(filters.AUDIO,    handle_audio_upload))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

loop = asyncio.new_event_loop()

def start_bot():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    if RADIO_CHANNEL_ID:
        loop.create_task(channel_radio_loop())
    loop.run_forever()

threading.Thread(target=start_bot, daemon=True).start()

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    data   = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), loop)
    return "ok"

@app.route("/")
def health():
    playlist     = get_cached_playlist()
    radio_status = "BROADCASTING" if radio_loop_running else "STANDBY"
    return f"I.A.A.I.M.O ONLINE v15.000 RADIO {radio_status} PLAYLIST {len(playlist)} items", 200

if __name__ == "__main__":
    init_pool()
    init_db()
    auto_classify_rotation()
    threading.Thread(target=weekly_intel_thread, daemon=True).start()
    playlist = get_cached_playlist()
    print("I.A.A.I.M.O MISERBOT v15.000")
    print("VIRAL GROWTH ENGINE ACTIVE")
    print(f"Songs: {len(SEED_SONGS)}")
    print(f"Beats: {len(SEED_BEATS)}")
    print(f"Drops: {len(SEED_DROPS)}")
    print(f"Playlist: {len(playlist)} items cached")
    print(f"Channel: {RADIO_CHANNEL_ID or 'NOT SET'}")
    print("Vault: ACTIVE")
    print("Submissions: ACTIVE")
    print("Anti-Repeat: ACTIVE last 8 songs excluded")
    print("Status: ONLINE")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
