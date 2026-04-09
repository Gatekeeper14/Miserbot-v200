"""
╔══════════════════════════════════════════════════════════════╗
║         I.A.A.I.M.O — MASTER SYSTEM v12.000                 ║
║  Independent Artists Artificial Intelligence Music Ops       ║
║  Bot:     Miserbot                                           ║
║  Owner:   BAZRAGOD                                           ║
║  Nation:  Parish 14                                          ║
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

BOOKING_EMAIL     = "Miserbot.ai@gmail.com"
CASHAPP           = "https://cash.app/$BAZRAGOD"
PAYPAL            = "https://paypal.me/bazragod1"
SUPPORTER_PRICE   = 19.99
CHARITY_PRICE     = 1.00
CHARITY_THRESHOLD = 500

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
        "location_saved": "📍 ¡Ubicación registrada!\n\nTu ciudad está en el mapa 🌍\n\nBAZRAGOD ve dónde está su ejército. 👑",
        "mission_done":   "🎯 ¡MISIÓN COMPLETADA!\n\nVuelve mañana. Parish 14 nunca para. 👑",
    },
    "fr": {
        "select_lang":    "🌍 Sélectionnez votre langue pour entrer sur la plateforme.",
        "lang_saved":     "✅ Langue sauvegardée.",
        "welcome_inside": "🛸 VOUS ÊTES MAINTENANT À L'INTÉRIEUR\n\nI.A.A.I.M.O — Nation Parish 14.\nSans labels. Sans intermédiaires. Juste le mouvement.\n\nVous faites partie de l'histoire. 🔥",
        "no_songs":       "Catalogue en chargement... revenez bientôt.",
        "location_saved": "📍 Localisation enregistrée!\n\nVotre ville est sur la carte 🌍\n\nBAZRAGOD voit où se tient son armée. 👑",
        "mission_done":   "🎯 MISSION ACCOMPLIE!\n\nReviens demain. Parish 14 ne s'arrête jamais. 👑",
    },
    "pt": {
        "select_lang":    "🌍 Selecione seu idioma para entrar na plataforma.",
        "lang_saved":     "✅ Idioma salvo.",
        "welcome_inside": "🛸 VOCÊ ESTÁ DENTRO\n\nI.A.A.I.M.O — Nação Parish 14.\nSem gravadoras. Sem intermediários. Só o movimento.\n\nVocê faz parte da história. 🔥",
        "no_songs":       "Catálogo carregando... volte em breve.",
        "location_saved": "📍 Localização registrada!\n\nSua cidade está no mapa 🌍\n\nBAZRAGOD vê onde seu exército está. 👑",
        "mission_done":   "🎯 MISSÃO COMPLETA!\n\nVolte amanhã. Parish 14 nunca para. 👑",
    },
    "de": {
        "select_lang":    "🌍 Wähle deine Sprache, um die Plattform zu betreten.",
        "lang_saved":     "✅ Sprache gespeichert.",
        "welcome_inside": "🛸 DU BIST JETZT DRIN\n\nI.A.A.I.M.O — Parish 14 Nation.\nKein Label. Kein Mittelsmann. Nur die Bewegung.\n\nDu bist Teil der Geschichte. 🔥",
        "no_songs":       "Katalog wird geladen... bald verfügbar.",
        "location_saved": "📍 Standort gespeichert!\n\nDeine Stadt ist auf der Karte 🌍\n\nBAZRAGOD sieht wo seine Armee steht. 👑",
        "mission_done":   "🎯 MISSION ABGESCHLOSSEN!\n\nKomm morgen wieder. Parish 14 hört nie auf. 👑",
    },
    "jm": {
        "select_lang":    "🌍 Select yu language fi enter di platform.",
        "lang_saved":     "✅ Language saved, massive.",
        "welcome_inside": "🛸 YU INSIDE NOW\n\nI.A.A.I.M.O — Parish 14 Nation.\nNo label. No middleman. Just di movement.\n\nYu part of history. 🔥",
        "no_songs":       "Catalog loading... check back soon.",
        "location_saved": "📍 Location saved!\n\nYu city pon di map 🌍\n\nBAZRAGOD si where di army stand. 👑",
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
# ║                🎙️ DJ PERSONALITY SYSTEM                      ║
# ╚══════════════════════════════════════════════════════════════╝

DJS = {
    "aurora": {
        "name":    "DJ Aurora",
        "emoji":   "🌅",
        "hours":   range(5, 12),
        "db_key":  "aurora",
        "style":   (
            "You are DJ Aurora, morning energy host of BazraGod Radio. "
            "Uplifting, motivational, sunrise vibes, warm Jamaican energy. "
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
        "db_key":  "colorred",
        "style":   (
            "You are DJ Color Red, afternoon hype host of BazraGod Radio. "
            "High energy, hype, confident, street culture. "
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
        "db_key":  "maximus",
        "style":   (
            "You are DJ Maximus, prime time commander of BazraGod Radio. "
            "Sovereign, deep, authoritative, luxury. "
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
        "db_key":  "eclipse",
        "style":   (
            "You are DJ Eclipse, late night atmosphere host of BazraGod Radio. "
            "Deep, mysterious, cinematic, introspective. "
            "Keep commentary under 2 sentences. Dark and atmospheric."
        ),
        "intros": [
            "Late night. DJ Eclipse in the dark. BazraGod Radio never sleeps.",
            "Past midnight. The real ones are awake. DJ Eclipse.",
            "Eclipse on the frequency. No sleep for the sovereign. Parish 14.",
        ],
    },
}

DJ_TRANSITIONS = [
    "That was heavy. Parish 14 stays winning.",
    "Another BazraGod classic just touched the airwaves.",
    "Keep it locked. BazraGod Radio never sleeps.",
    "You are listening to the sovereign frequency.",
    "The nation grows stronger every day.",
    "Only real ones tuned in right now.",
    "Parish 14 worldwide. Stay with us.",
    "Independent music taking over the airwaves.",
    "No label. No limit. Just the music.",
    "BazraGod built this from nothing. That is power.",
    "This is what independence sounds like.",
    "Parish 14 Nation. Worldwide. Forever.",
]

STATION_IDS = [
    "BazraGod Radio. Parish 14 Nation. Independent music lives here.",
    "You are tuned in to BazraGod Radio. I.A.A.I.M.O. No label. No limit.",
    "This is BazraGod Radio. The sovereign station. Parish 14 worldwide.",
    "BazraGod Radio. Where the real ones listen. All day. Every day.",
    "I.A.A.I.M.O Radio. Independent Artists. Artificial Intelligence. Music Operations.",
]

def get_current_dj() -> dict:
    hour = datetime.now().hour
    for key, dj in DJS.items():
        if hour in dj["hours"]:
            return dj
    return DJS["maximus"]

# ╔══════════════════════════════════════════════════════════════╗
# ║              🎛️ AI PROGRAM DIRECTOR + ROTATION              ║
# ╚══════════════════════════════════════════════════════════════╝

RADIO_MEMORY:        dict = {}
RADIO_LAST_ANNOUNCE: dict = {}
MIN_PROMO_GAP              = 5
events_since_promo         = 0

def calculate_heat(likes: int, donations: int, plays: int) -> str:
    score = (likes * 5) + (donations * 10) + (plays / 1000)
    if score >= 250: return "🔥🔥🔥🔥🔥"
    if score >= 100: return "🔥🔥🔥🔥"
    if score >=  50: return "🔥🔥🔥"
    if score >=  10: return "🔥🔥"
    return "🔥"

def auto_classify_rotation():
    """Auto-update song rotation on boot based on heat score."""
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
        print(f"Rotation classify error: {e}")
    finally:
        release_db(conn)


def get_rotation_song(uid: int, preferred: str = None) -> tuple | None:
    conn = get_db()
    cur  = conn.cursor()
    try:
        memory = RADIO_MEMORY.get(uid, [])

        if preferred is None:
            preferred = random.choices(["A", "B", "C"], weights=[60, 30, 10], k=1)[0]

        exclude = memory if memory else [0]

        cur.execute(
            "SELECT id, title, file_id, plays, likes, donations, rotation "
            "FROM songs WHERE rotation = %s AND id != ALL(%s) ORDER BY RANDOM() LIMIT 1",
            (preferred, exclude),
        )
        song = cur.fetchone()

        if not song:
            cur.execute(
                "SELECT id, title, file_id, plays, likes, donations, rotation "
                "FROM songs WHERE id != ALL(%s) ORDER BY RANDOM() LIMIT 1",
                (exclude,),
            )
            song = cur.fetchone()

        if not song:
            RADIO_MEMORY[uid] = []
            cur.execute(
                "SELECT id, title, file_id, plays, likes, donations, rotation "
                "FROM songs ORDER BY RANDOM() LIMIT 1"
            )
            song = cur.fetchone()

        if song:
            RADIO_MEMORY[uid] = memory + [song[0]]
            cur.execute("UPDATE songs SET plays = plays + 1 WHERE id = %s", (song[0],))
            conn.commit()

        return song
    finally:
        release_db(conn)


async def ai_program_director(uid: int, dj: dict, now: str) -> str:
    """GPT decides what plays next on the radio."""
    if not openai_client:
        return random.choices(
            ["song_a", "song_b", "song_c", "dj_commentary",
             "fan_shoutout", "chart_announcement", "promo", "beat"],
            weights=[40, 20, 10, 10, 7, 5, 5, 3],
            k=1,
        )[0]

    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM songs WHERE rotation = 'A'")
        a_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM song_requests WHERE played = FALSE")
        requests = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM radio_sessions "
            "WHERE last_ping > NOW() - INTERVAL '30 minutes'"
        )
        listeners = cur.fetchone()[0]
    finally:
        release_db(conn)

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the AI Program Director of BazraGod Radio. "
                        "Decide what plays next to keep listeners engaged. "
                        f"Time: {now}. DJ: {dj['name']}. "
                        f"Live listeners: {listeners}. "
                        f"Hot rotation songs: {a_count}. "
                        f"Pending requests: {requests}. "
                        "Reply with ONLY ONE of: "
                        "song_a, song_b, song_c, dj_commentary, "
                        "fan_shoutout, chart_announcement, promo, beat"
                    ),
                },
                {"role": "user", "content": "What plays next?"},
            ],
            max_tokens=10,
        )
        decision = response.choices[0].message.content.strip().lower()
        valid = [
            "song_a", "song_b", "song_c", "dj_commentary",
            "fan_shoutout", "chart_announcement", "promo", "beat",
        ]
        return decision if decision in valid else "song_a"
    except Exception:
        return "song_a"


async def get_live_fan_shoutout() -> str:
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT f.username, fl.city, fl.country
            FROM fans f
            LEFT JOIN fan_locations fl ON f.telegram_id = fl.telegram_id
            WHERE f.username IS NOT NULL
            ORDER BY RANDOM() LIMIT 1
        """)
        row = cur.fetchone()
    finally:
        release_db(conn)

    if not row:
        return random.choice(DJ_TRANSITIONS)

    username, city, country = row
    location = city or country or "the world"
    templates = [
        f"Shoutout to @{username} tuning in from {location}. Parish 14 Nation.",
        f"Big up @{username} in {location}. Real soldier. Keep listening.",
        f"This one goes to @{username} from {location}. You are part of history.",
        f"@{username} from {location} — BAZRAGOD sees you. Parish 14.",
        f"Love from BazraGod Radio to @{username} in {location}. Stay locked in.",
    ]
    return random.choice(templates)


async def get_chart_announcement() -> str:
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT title, plays, likes, donations,
                   (plays / 1000.0 + likes * 5 + donations * 10) as score
            FROM songs ORDER BY score DESC LIMIT 1
        """)
        top = cur.fetchone()
        cur.execute(
            "SELECT COUNT(*) FROM radio_sessions "
            "WHERE last_ping > NOW() - INTERVAL '30 minutes'"
        )
        listeners = cur.fetchone()[0]
    finally:
        release_db(conn)

    if not top:
        return "BazraGod Radio. Parish 14 charts are heating up."

    title, plays, likes, donations, _ = top
    heat = calculate_heat(likes, donations, plays)

    templates = [
        f"Chart update. {title} is the hottest track right now. {plays:,} plays. {heat}.",
        f"Breaking. {title} by BAZRAGOD is dominating the Parish 14 charts. {plays:,} plays.",
        f"Number one on BazraGod Radio right now — {title}. {listeners} listeners hearing it live.",
        f"Parish 14 chart leader: {title}. {plays:,} plays and climbing. Independent music wins.",
    ]
    return random.choice(templates)

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
    "like_song":      3,
    "supporter_sub": 50,
    "request_song":   3,
    "charity":       10,
    "donate_song":   10,
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

RADIO_PROMOS_TEXT = [
    "Support independent music. Hit the Support button.",
    "Parish 14 merch available now. Rep the nation.",
    "Invite your friends. Parish 14 grows stronger every day.",
    "I.A.A.I.M.O — no label, no middleman, just BAZRAGOD.",
    "Book BAZRAGOD for your event. Contact Miserbot.ai@gmail.com",
    "Become a Parish 14 Supporter for $19.99 a month.",
    "Stream BAZRAGOD on Spotify. Search BAZRAGOD.",
    "Drop your verse in the Lyric Cipher. Challenge MAXIMUS.",
    "Request your track. Tap 📀 Request Track.",
]

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
    "Never outshine the master.",
    "Appear weak when you are strong.",
    "The obstacle is the way.",
    "A lion does not concern himself with the opinions of sheep.",
    "Kings are not born — they are made through discipline.",
    "Do not pray for an easy life. Pray for strength to endure a difficult one.",
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
        for col, definition in [
            ("prophecy_tiers", "TEXT DEFAULT ''"),
            ("is_supporter",   "BOOLEAN DEFAULT FALSE"),
            ("supporter_expires", "DATE"),
            ("language",       "TEXT DEFAULT 'en'"),
        ]:
            cur.execute(
                f"ALTER TABLE fans ADD COLUMN IF NOT EXISTS {col} {definition}"
            )

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
        for col, definition in [
            ("plays",     "INTEGER DEFAULT 30000"),
            ("likes",     "INTEGER DEFAULT 0"),
            ("donations", "INTEGER DEFAULT 0"),
            ("rotation",  "TEXT DEFAULT 'C'"),
        ]:
            cur.execute(
                f"ALTER TABLE songs ADD COLUMN IF NOT EXISTS {col} {definition}"
            )

        cur.execute("""
            CREATE TABLE IF NOT EXISTS beats (
                id SERIAL PRIMARY KEY, title TEXT, file_id TEXT,
                uploaded_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS drops (
                id SERIAL PRIMARY KEY, title TEXT, file_id TEXT,
                uploaded_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id SERIAL PRIMARY KEY, title TEXT, file_id TEXT,
                uploaded_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS promos (
                id SERIAL PRIMARY KEY, title TEXT, file_id TEXT,
                uploaded_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS radio_promos (
                id SERIAL PRIMARY KEY, text TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dj_drops (
                id SERIAL PRIMARY KEY, dj TEXT, title TEXT, file_id TEXT,
                uploaded_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fan_locations (
                telegram_id BIGINT PRIMARY KEY, city TEXT, country TEXT,
                latitude FLOAT, longitude FLOAT,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS point_log (
                id SERIAL PRIMARY KEY, telegram_id BIGINT,
                action TEXT, pts INT, logged_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                telegram_id BIGINT, mission_date DATE,
                completed BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (telegram_id, mission_date)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id SERIAL PRIMARY KEY, telegram_id BIGINT,
                item TEXT, price FLOAT, status TEXT DEFAULT 'pending',
                purchased_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS astro_profiles (
                telegram_id BIGINT PRIMARY KEY, birth_date TEXT,
                birth_time TEXT, birth_city TEXT, current_city TEXT,
                last_reading TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS voice_wall (
                id SERIAL PRIMARY KEY, telegram_id BIGINT, username TEXT,
                file_id TEXT, status TEXT DEFAULT 'pending',
                submitted_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS song_likes (
                telegram_id BIGINT, song_id INT,
                PRIMARY KEY (telegram_id, song_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS song_requests (
                id SERIAL PRIMARY KEY, telegram_id BIGINT, username TEXT,
                song_title TEXT, played BOOLEAN DEFAULT FALSE,
                requested_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS radio_sessions (
                telegram_id BIGINT PRIMARY KEY,
                joined_at TIMESTAMP DEFAULT NOW(),
                last_ping TIMESTAMP DEFAULT NOW()
            )
        """)

        # Seed songs only if table is empty
        cur.execute("SELECT COUNT(*) FROM songs")
        if cur.fetchone()[0] == 0:
            for title, file_id in SEED_SONGS:
                cur.execute(
                    "INSERT INTO songs (title, file_id) VALUES (%s, %s) "
                    "ON CONFLICT (title) DO NOTHING",
                    (title, file_id),
                )

        conn.commit()
        print("I.A.A.I.M.O DATABASE READY — v12.000")
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
        cur.execute(
            "UPDATE fans SET language = %s WHERE telegram_id = %s",
            (lang, uid),
        )
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
            model="tts-1", voice="onyx", input=text[:500], speed=0.95,
        )
        audio_file = BytesIO(response.content)
        audio_file.name = "maximus.ogg"
        await bot.send_voice(chat_id=chat_id, voice=audio_file)
    except Exception as e:
        print(f"Voice direct error: {e}")


async def dj_speak(context, chat_id: int, text: str):
    """Respect 15-min timer per user."""
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
            prompt = f"Give a 1-2 sentence DJ commentary about '{song_title}' by BAZRAGOD that just played."
        elif action == "reaction" and song_title:
            prompt = f"Give a 1 sentence hot reaction to '{song_title}' by BAZRAGOD."
        elif action == "intro" and song_title:
            prompt = f"Introduce the next track '{song_title}' by BAZRAGOD in 1-2 sentences."
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
                    f"Fan: {name_display}\nRank achieved: {tier}\nPoints: {points}\n\n"
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
# ║              🌍 LANGUAGE HANDLERS                            ║
# ╚══════════════════════════════════════════════════════════════╝

async def language_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=f"lang:{code}")]
        for code, label in SUPPORTED_LANGUAGES.items()
    ])
    uid  = update.effective_user.id
    lang = get_user_lang(uid)
    await update.message.reply_text(
        t(lang, "select_lang"),
        reply_markup=keyboard,
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

    uid       = query.from_user.id
    lang_name = SUPPORTED_LANGUAGES[lang]
    set_user_lang(uid, lang)

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

    # New fans see language selector first
    if is_new:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(label, callback_data=f"lang:{code}")]
            for code, label in SUPPORTED_LANGUAGES.items()
        ])
        await update.message.reply_text(
            "🌍 PARISH 14 NETWORK\n\nSelect your language to enter:",
            reply_markup=keyboard,
        )
    elif INTRO_FILE_ID:
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

    await query.message.reply_text(
        f"{t(lang, 'welcome_inside')}\n\nRank:   {tier}\nPoints: {pts}\n\n"
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
        cur.execute(
            "SELECT id, title, plays, likes, donations, rotation FROM songs ORDER BY id"
        )
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
                f"{heat}  {plays:,} plays  ❤️ {likes}  💰 {donations}\n\n"
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
                f"💝 CHARITY THRESHOLD REACHED!\n\nTotal donations: {total_donations}\n"
                f"${CHARITY_THRESHOLD} milestone hit. Parish 14 came through! 👑",
            )
        except Exception:
            pass

# ╔══════════════════════════════════════════════════════════════╗
# ║                📊 CHARTS                                     ║
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
            cur.execute(
                "SELECT title, plays, likes, donations FROM songs ORDER BY plays DESC LIMIT 10"
            )
            label = "🔥 TOP PLAYED"
        elif chart_type == "liked":
            cur.execute(
                "SELECT title, plays, likes, donations FROM songs ORDER BY likes DESC LIMIT 10"
            )
            label = "❤️ MOST LIKED"
        else:
            cur.execute("""
                SELECT title, plays, likes, donations
                FROM songs
                ORDER BY (plays / 1000.0 + likes * 5 + donations * 10) DESC LIMIT 10
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
            FROM songs
            ORDER BY (plays / 1000.0 + likes * 5 + donations * 10) DESC LIMIT 10
        """)
        songs = cur.fetchall()
    finally:
        release_db(conn)

    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    text   = "🔥 TRENDING ON PARISH 14\n\n"
    for i, (title, plays, likes, donations) in enumerate(songs):
        heat = calculate_heat(likes, donations, plays)
        text += f"{medals[i]} {title}\n   {plays:,} plays  {heat}\n\n"
    await update.message.reply_text(text)


async def song_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT title, plays, likes, donations, rotation FROM songs ORDER BY plays DESC LIMIT 10"
        )
        songs = cur.fetchall()
    finally:
        release_db(conn)

    text = "📈 SONG STATISTICS\n\n"
    rotation_badge = {"A": "🔴 Hot", "B": "🟡 Mid", "C": "🟢 Deep"}
    for title, plays, likes, donations, rotation in songs:
        heat  = calculate_heat(likes, donations, plays)
        badge = rotation_badge.get(rotation, "")
        text += (
            f"🎵 {title}  {badge}\n"
            f"Plays:     {plays:,}\n"
            f"Likes:     {likes}\n"
            f"Donations: {donations}\n"
            f"Heat:      {heat}\n\n"
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
# ║    📻 RADIO ENGINE — AI PROGRAM DIRECTOR + ROTATION          ║
# ╚══════════════════════════════════════════════════════════════╝

async def radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global events_since_promo

    uid  = update.effective_user.id
    name = get_username(update)
    now  = datetime.now().strftime("%I:%M %p")
    dj   = get_current_dj()

    update_listener(uid)
    listeners = get_listener_count()
    pts       = award_points(uid, "radio", name)

    # AI Program Director decides
    decision = await ai_program_director(uid, dj, now)

    # Promo spacing guard
    if decision == "promo" and events_since_promo < MIN_PROMO_GAP:
        decision = "song_a"
    events_since_promo = 0 if decision == "promo" else events_since_promo + 1

    # Transition (25% chance)
    if random.random() < 0.25:
        await dj_speak(context, uid, random.choice(DJ_TRANSITIONS))

    # ── FAN SHOUTOUT ───────────────────────────────────────────
    if decision == "fan_shoutout":
        shout = await get_live_fan_shoutout()
        await dj_speak(context, uid, shout)
        await update.message.reply_text(
            f"📻 {dj['emoji']} {dj['name']} — {now}\n\n🎤 {shout}\n\n"
            f"👥 {listeners} listeners\n\n+{pts} pts"
        )
        return

    # ── CHART ANNOUNCEMENT ─────────────────────────────────────
    if decision == "chart_announcement":
        ann = await get_chart_announcement()
        await dj_speak(context, uid, ann)
        await update.message.reply_text(
            f"📻 {dj['emoji']} {dj['name']} — {now}\n\n📊 {ann}\n\n"
            f"👥 {listeners} listeners\n\n+{pts} pts"
        )
        return

    # ── DJ COMMENTARY ──────────────────────────────────────────
    if decision == "dj_commentary":
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT title FROM songs ORDER BY plays DESC LIMIT 5")
            rows = cur.fetchall()
        finally:
            release_db(conn)
        title = random.choice(rows)[0] if rows else "BAZRAGOD"
        line  = await generate_dj_line(dj, title, "commentary")
        await dj_speak(context, uid, line)
        await update.message.reply_text(
            f"📻 {dj['emoji']} {dj['name']} — {now}\n\n💬 {line}\n\n+{pts} pts"
        )
        return

    # ── PROMO ──────────────────────────────────────────────────
    if decision == "promo":
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT title, file_id FROM promos ORDER BY RANDOM() LIMIT 1")
            item = cur.fetchone()
        finally:
            release_db(conn)
        if item:
            await update.message.reply_audio(
                item[1],
                caption=f"📣 {item[0]}\n📻 {dj['emoji']} BazraGod Radio — {now}",
            )
        else:
            promo = random.choice(RADIO_PROMOS_TEXT)
            await dj_speak(context, uid, f"BazraGod Radio — {now}. {promo}")
            await update.message.reply_text(
                f"📻 {dj['emoji']} {dj['name']} — {now}\n\n🎙️ {promo}\n\n"
                f"👥 {listeners} listeners\n\n+{pts} pts"
            )
        return

    # ── BEAT ───────────────────────────────────────────────────
    if decision == "beat":
        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute("SELECT title, file_id FROM beats ORDER BY RANDOM() LIMIT 1")
            item = cur.fetchone()
        finally:
            release_db(conn)
        if item:
            await dj_speak(context, uid, f"BazraGod Radio. {now}. This beat called {item[0]}. Feel it.")
            await update.message.reply_audio(
                item[1],
                caption=f"📻 {dj['emoji']} BazraGod Radio — {now}\n\n🥁 BEAT: {item[0]}\n\n+{pts} pts",
            )
            return

    # ── SONG with rotation + request queue ─────────────────────
    rotation_map = {"song_a": "A", "song_b": "B", "song_c": "C"}
    preferred    = rotation_map.get(decision)

    req  = None
    song = None

    if random.random() < 0.10:
        req = await _get_pending_request()
        if req:
            conn = get_db()
            cur  = conn.cursor()
            try:
                cur.execute(
                    "SELECT id, title, file_id, plays, likes, donations, rotation "
                    "FROM songs WHERE LOWER(title) LIKE LOWER(%s) LIMIT 1",
                    (f"%{req['title']}%",),
                )
                song = cur.fetchone()
                if song:
                    cur.execute("UPDATE songs SET plays = plays + 1 WHERE id = %s", (song[0],))
                    conn.commit()
            finally:
                release_db(conn)

    if not song:
        song = get_rotation_song(uid, preferred)
        req  = None

    if not song:
        await update.message.reply_text("📻 Radio loading... no songs found.")
        return

    sid, title, file_id, plays, likes, donations, rotation = song
    heat          = calculate_heat(likes, donations, plays)
    rotation_badge = {"A": "🔴 Hot", "B": "🟡 Mid", "C": "🟢 Deep Cut"}.get(rotation, "")

    dj_txt = (
        f"Honoring a request from {req['username']}. "
        f"Now playing {title} by BAZRAGOD. BazraGod Radio — {now}."
        if req else await generate_dj_line(dj, title, "intro")
    )

    await dj_speak(context, uid, dj_txt)

    req_line = f"\n🎯 Requested by @{req['username']}!" if req else ""

    await update.message.reply_audio(
        file_id,
        caption=(
            f"📻 {dj['emoji']} BazraGod Radio — {now}\n\n"
            f"🎵 {title}  {rotation_badge}\n"
            f"{heat}  {plays:,} plays  ❤️{likes}  💰{donations}"
            f"{req_line}\n\n"
            f"👥 {listeners} listeners tuned in\n\n"
            f"+{pts} pts 🔥"
        ),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❤️ Like",   callback_data=f"like:{sid}"),
            InlineKeyboardButton("💰 Donate", callback_data=f"donate:{sid}"),
        ]]),
    )
    await maybe_prophecy(uid, name, context)

# ╔══════════════════════════════════════════════════════════════╗
# ║                🧠 MOOD RADIO                                 ║
# ╚══════════════════════════════════════════════════════════════╝

async def mood_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    mood_sessions[uid] = True
    await update.message.reply_text(
        "🧠 MOOD RADIO\n\nMAXIMUS reads your energy and selects\n"
        "the perfect BAZRAGOD track for your soul.\n\n"
        "How are you feeling right now?\n\n"
        "Examples:\n• motivated and on fire\n• sad and reflective\n"
        "• locked in and focused\n• celebrating a win\n\n"
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

    await update.message.reply_text(f"🧠 MAXIMUS is reading your energy...\n\nMood: {text}")

    try:
        song_list = "\n".join([f"{s[0]}. {s[1]}" for s in songs])
        response  = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are MAXIMUS, music selector. Reply with ONLY the song ID number."},
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
        cur.execute(
            "SELECT id, title, file_id, plays, likes, donations FROM songs WHERE id = %s",
            (song_id,),
        )
        song = cur.fetchone()
        if not song:
            cur.execute(
                "SELECT id, title, file_id, plays, likes, donations FROM songs ORDER BY RANDOM() LIMIT 1"
            )
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
        "Drop your verse below.\nMAXIMUS responds in BAZRAGOD's style.\n\n"
        "Write your bars 👇\n\nType /cancel to exit."
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
                {"role": "system", "content": "You are MAXIMUS writing bars in BAZRAGOD's lyric style. Jamaican-influenced. Sovereign, confident, raw, Patois influence, wealth mindset, spiritual power. Write exactly 4 bars. No explicit language."},
                {"role": "user", "content": f"Fan verse:\n{text}\n\nRespond with 4 bars in BAZRAGOD style."},
            ],
            max_tokens=200,
        )
        verse = response.choices[0].message.content
        pts   = award_points(uid, "cipher", name)
        await update.message.reply_text(
            f"⚔️ BAZRAGOD CIPHER\n{'═' * 20}\n\nYou:\n{text}\n\n"
            f"MAXIMUS:\n{verse}\n\n{'═' * 20}\n+{pts} pts 🔥"
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


async def request_handler(
    uid: int, text: str, update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
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


async def _get_pending_request() -> dict | None:
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT id, telegram_id, username, song_title
            FROM song_requests WHERE played = FALSE
            ORDER BY requested_at ASC LIMIT 1
        """)
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE song_requests SET played = TRUE WHERE id = %s", (row[0],))
            conn.commit()
            return {"id": row[0], "uid": row[1], "username": row[2], "title": row[3]}
        return None
    finally:
        release_db(conn)

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
        f"💝 THANK YOU!\n\nYour contribution supports independent music.\n"
        f"Parish 14 Nation appreciates you. 👑\n\n+{pts} pts 🔥"
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║                💎 SUPPORTER TIER                             ║
# ╚══════════════════════════════════════════════════════════════╝

async def supporter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT is_supporter, supporter_expires FROM fans WHERE telegram_id = %s", (uid,)
        )
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
            f"🎧 Early access songs\n🎤 Exclusive drops\n👑 Leaderboard priority\n\n"
            f"Thank you for funding the movement. 👑"
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
        f"🎧 Early access songs\n🎤 Exclusive drops\n👑 Leaderboard priority\n\n"
        f"Pay then tap below 👇",
        reply_markup=keyboard,
    )


async def supporter_verify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    name = query.from_user.username or query.from_user.first_name
    await query.message.reply_text(
        "💎 Payment submitted for review.\nAdmin will activate your status. 👑"
    )
    try:
        await context.bot.send_message(
            OWNER_ID,
            f"💎 SUPPORTER REQUEST\n\nFan: @{name} ({uid})\n\n/activate_supporter {uid}",
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
    fan_id  = int(args[0])
    expires = date.today() + timedelta(days=30)
    conn    = get_db()
    cur     = conn.cursor()
    try:
        cur.execute(
            "UPDATE fans SET is_supporter = TRUE, tier = '🌍  Nation Elite', "
            "supporter_expires = %s WHERE telegram_id = %s RETURNING username",
            (expires, fan_id),
        )
        row = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)
    if row:
        award_points(fan_id, "supporter_sub")
        await update.message.reply_text(
            f"✅ @{row[0]} activated as Parish 14 Supporter 💎\nExpires: {expires}"
        )
        try:
            await context.bot.send_message(
                fan_id,
                f"💎 PARISH 14 SUPPORTER ACTIVATED!\n\n🌍 Nation Elite badge unlocked.\n"
                f"Expires: {expires.strftime('%B %d, %Y')}\n\nBAZRAGOD sees you. 👑",
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
        "Tips:\n• Shout out BAZRAGOD\n• Say your city\n"
        "• Big up Parish 14 Nation\n• Under 30 seconds\n\n"
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
        f"🎙️ Submission #{sid} received!\n\nMAXIMUS will review it.\n"
        f"Approved voices play on BazraGod Radio. 🔥\n\n+{pts} pts 👑",
        reply_markup=main_menu,
    )
    try:
        await context.bot.send_message(
            OWNER_ID,
            f"🎙️ VOICE SUBMISSION #{sid}\nFan: @{name} ({uid})\n\n"
            f"/approve_voice {sid}\n/reject_voice {sid}",
        )
        await context.bot.forward_message(
            chat_id=OWNER_ID, from_chat_id=uid,
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
            "UPDATE voice_wall SET status = 'approved' WHERE id = %s "
            "RETURNING telegram_id, username",
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
                "🎙️ YOUR VOICE WAS APPROVED!\nIt plays live on BazraGod Radio. 🔥\nParish 14. 👑"
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
# ║      🎚️ SMART AUDIO UPLOAD CLASSIFICATION                    ║
# ╚══════════════════════════════════════════════════════════════╝

async def handle_audio_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

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

    # Robust title extraction
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
        [InlineKeyboardButton("📡 Station ID",        callback_data="upload:station_id")],
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
        "station_id": "📡 Station ID",
    }
    await _save_classified_audio(
        query.message, session["file_id"], session["title"],
        dest, label_map.get(dest, "✅")
    )


async def _save_classified_audio(msg, file_id: str, title: str, dest: str, label: str):
    conn = get_db()
    cur  = conn.cursor()
    try:
        if dest.startswith("dj:"):
            dj_key = dest.split(":")[1]
            cur.execute(
                "INSERT INTO dj_drops (dj, title, file_id) VALUES (%s, %s, %s) RETURNING id",
                (dj_key, title, file_id),
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            text = f"✅ {label} added. ID: {new_id}\nTitle: {title}"

        elif dest == "station_id":
            cur.execute("INSERT INTO radio_promos (text) VALUES (%s) RETURNING id", (title,))
            new_id = cur.fetchone()[0]
            conn.commit()
            text = f"✅ {label} stored. ID: {new_id}"

        elif dest == "songs":
            cur.execute("SELECT id FROM songs WHERE LOWER(title) = LOWER(%s)", (title,))
            if cur.fetchone():
                text = f"⚠️ Song '{title}' already exists. Upload skipped."
            else:
                cur.execute(
                    "INSERT INTO songs (title, file_id) VALUES (%s, %s) RETURNING id",
                    (title, file_id),
                )
                new_id = cur.fetchone()[0]
                conn.commit()
                text = f"✅ {label} added. ID: {new_id}\nTitle: {title}"

        else:
            cur.execute(
                f"INSERT INTO {dest} (title, file_id) VALUES (%s, %s) RETURNING id",
                (title, file_id),
            )
            new_id = cur.fetchone()[0]
            conn.commit()
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
    await dj_speak(
        context, update.effective_user.id,
        "Attention Parish 14 Nation. New BAZRAGOD video dropped. Go watch it now."
    )
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
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(p, url=u)] for p, u in SOCIALS.items()
    ])
    await update.message.reply_text(
        f"🌐 BAZRAGOD SOCIAL\n\nFollow on every platform.\nBring more soldiers to the nation 🔥\n\n+{pts} pts",
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
        f"💰 SUPPORT BAZRAGOD\n\nNo label takes a cut here.\nEvery dollar goes directly to the music.\n\n+{pts} pts 👑",
        reply_markup=keyboard,
    )

# ╔══════════════════════════════════════════════════════════════╗
# ║                  MERCH + MUSIC STORE                         ║
# ╚══════════════════════════════════════════════════════════════╝

async def merch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"👕 {MERCH_ITEMS['tshirt'][0]} — ${MERCH_ITEMS['tshirt'][1]}",
            callback_data="merch:tshirt"
        )],
        [InlineKeyboardButton(
            f"🧥 {MERCH_ITEMS['pullover'][0]} — ${MERCH_ITEMS['pullover'][1]}",
            callback_data="merch:pullover"
        )],
    ])
    await update.message.reply_text(
        "👕 PARISH 14 MERCH\n\nOfficial BAZRAGOD clothing.\nWear the nation.\n\nSelect your item 👇",
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
        f"After payment send admin:\n• Your size\n• Shipping address\n"
        f"• Payment proof\n\nParish 14. 👑",
        reply_markup=keyboard,
    )


async def music_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"🎵 {STORE_ITEMS['single'][0]} — ${STORE_ITEMS['single'][1]}",
            callback_data="store:single"
        )],
        [InlineKeyboardButton(
            f"📦 {STORE_ITEMS['bundle'][0]} — ${STORE_ITEMS['bundle'][1]}",
            callback_data="store:bundle"
        )],
        [InlineKeyboardButton(
            f"👑 {STORE_ITEMS['exclusive'][0]} — ${STORE_ITEMS['exclusive'][1]}",
            callback_data="store:exclusive"
        )],
    ])
    await update.message.reply_text(
        "🛒 BAZRAGOD MUSIC STORE\n\nDirect from the artist.\nNo streaming cuts. No label fees.\n\nSelect your purchase 👇",
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
            f"💰 NEW PURCHASE\n\nOrder: #{purchase_id}\nFan: @{name} ({uid})\n"
            f"Item: {item_name}\nPrice: ${price}",
        )
    except Exception:
        pass

# ╔══════════════════════════════════════════════════════════════╗
# ║                  BOOKING + FAN RADAR                         ║
# ╚══════════════════════════════════════════════════════════════╝

async def booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📅 BOOK BAZRAGOD\n\nShows, features, events, collabs.\n\n"
        f"Contact:\n{BOOKING_EMAIL}\n\nInclude:\n• Event type\n• Date and location\n"
        f"• Budget\n• Contact number\n\nBAZRAGOD is global. Parish​​​​​​​​​​​​​​​​
