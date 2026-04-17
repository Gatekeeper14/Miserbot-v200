import os

BOT_TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("ROYAL_BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OWNER_ID = int(os.environ.get("OWNER_ID", "8741545426"))
RADIO_CHANNEL_ID = os.environ.get("RADIO_CHANNEL_ID", "")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
BOT_USERNAME = "BazragodMiserbot_bot"
INTRO_FILE_ID = os.environ.get("INTRO_FILE_ID", "")
FIRST_MESSAGE_FILE_ID = os.environ.get("FIRST_MESSAGE_FILE_ID", "")
PARISH_LOUNGE = os.environ.get("PARISH_LOUNGE", "https://t.me/parish14lounge")
RADIO_CHANNEL_LINK = os.environ.get("RADIO_CHANNEL", "https://t.me/bazragodradio")
BOOKING_EMAIL = "Miserbot.ai@gmail.com"
CASHAPP = "https://cash.app/$BAZRAGOD"
PAYPAL = "https://paypal.me/bazragod1"
SUPPORTER_PRICE = 19.99
VAULT_UNLOCK_PRICE = 50
VAULT_SUPERFAN_PRICE = 500
DEDICATION_COST = 50
CHARITY_THRESHOLD = 500
STAKE_TIERS = {7: 1.2, 14: 1.35, 30: 1.5}
DAILY_DRIP = 10
STREAK_BONUSES = {3: 25, 7: 75, 30: 300}
STREAK_BADGES = {3: "3-Day Streak", 7: "Week Warrior", 30: "Legendary Listener"}
RADIO_SONG_DELAY = 200
RADIO_BEAT_DELAY = 120
RADIO_DROP_DELAY = 35
RADIO_AD_DELAY = 25
RADIO_ANNOUNCE_DELAY = 30
PLAYLIST_TTL = 300
SONG_PRICE = 5
ALBUM_PRICE = 50
ALBUM_COUNT = 7

SOFT_GATE = [
    ("BazraGod Radio", RADIO_CHANNEL_LINK),
    ("Parish 14 Lounge", PARISH_LOUNGE),
    ("Instagram", "https://www.instagram.com/bazragod_timeless"),
    ("TikTok", "https://www.tiktok.com/@bazragod_official"),
    ("YouTube", "https://youtube.com/@bazragodmusictravelandleis8835"),
    ("X Twitter", "https://x.com/toligarch65693"),
    ("Snapchat", "https://snapchat.com/t/L7djDwfj"),
    ("Twitch", "https://twitch.tv/bazra14"),
    ("Spotify", "https://open.spotify.com/artist/2IwaaLobpi2NSGD3B5xapK"),
]

SUPPORTED_LANGUAGES = {
    "en": "English", "es": "Espanol", "fr": "Francais",
    "pt": "Portugues", "de": "Deutsch", "jm": "Patois",
}

TRANSLATIONS = {
    "en": {
        "select_lang": "Select your language to enter the platform.",
        "lang_saved": "Language saved.",
        "welcome_inside": "YOU ARE NOW INSIDE\n\nI.A.A.I.M.O - Parish 14 Nation.\nNo labels. No middlemen. Just the movement.\n\nYou are part of history.",
        "no_songs": "Catalog loading... check back soon.",
        "location_saved": "Location recorded. Your city is on the map.",
        "mission_done": "MISSION COMPLETE. Come back tomorrow. Parish 14 never stops.",
    },
    "es": {
        "select_lang": "Selecciona tu idioma.",
        "lang_saved": "Idioma guardado.",
        "welcome_inside": "AHORA ESTAS DENTRO\n\nI.A.A.I.M.O - Nacion Parish 14.",
        "no_songs": "Catalogo cargando...",
        "location_saved": "Ubicacion registrada.",
        "mission_done": "MISION COMPLETADA.",
    },
    "fr": {
        "select_lang": "Selectionnez votre langue.",
        "lang_saved": "Langue sauvegardee.",
        "welcome_inside": "VOUS ETES A L INTERIEUR\n\nI.A.A.I.M.O - Nation Parish 14.",
        "no_songs": "Catalogue en chargement...",
        "location_saved": "Localisation enregistree.",
        "mission_done": "MISSION ACCOMPLIE.",
    },
    "pt": {
        "select_lang": "Selecione seu idioma.",
        "lang_saved": "Idioma salvo.",
        "welcome_inside": "VOCE ESTA DENTRO\n\nI.A.A.I.M.O - Nacao Parish 14.",
        "no_songs": "Catalogo carregando...",
        "location_saved": "Localizacao registrada.",
        "mission_done": "MISSAO COMPLETA.",
    },
    "de": {
        "select_lang": "Wahle deine Sprache.",
        "lang_saved": "Sprache gespeichert.",
        "welcome_inside": "DU BIST JETZT DRIN\n\nI.A.A.I.M.O - Parish 14 Nation.",
        "no_songs": "Katalog wird geladen...",
        "location_saved": "Standort gespeichert.",
        "mission_done": "MISSION ABGESCHLOSSEN.",
    },
    "jm": {
        "select_lang": "Select yu language fi enter di platform.",
        "lang_saved": "Language saved massive.",
        "welcome_inside": "YU INSIDE NOW\n\nI.A.A.I.M.O - Parish 14 Nation.\nNo label. No middleman. Just di movement.",
        "no_songs": "Catalog loading...",
        "location_saved": "Location saved. Yu city pon di map.",
        "mission_done": "MISSION COMPLETE. Come back tomorrow. Parish 14 nuh stop.",
    },
}

def t(lang, key):
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))

RANKS = [
    (0, "Fan"), (100, "Supporter"), (500, "Recruiter"),
    (1000, "Commander"), (2500, "General"),
    (5000, "Nation Elite"), (10000, "Parish Legend"),
]
LISTENER_RANKS = [
    (0, "Listener"), (500, "Supporter"), (2000, "Ambassador"),
    (5000, "Commander"), (10000, "Legend"),
]

def get_rank(pts):
    r = "Fan"
    for th, lb in RANKS:
        if pts >= th: r = lb
    return r

def get_station_rank(pts):
    r = "Listener"
    for th, lb in LISTENER_RANKS:
        if pts >= th: r = lb
    return r

def get_next_rank(pts):
    for th, lb in RANKS:
        if pts < th: return f"{th - pts} coins to reach {lb}"
    return "Maximum rank. Parish Legend."

POINTS = {
    "start": 5, "play_song": 8, "play_beat": 6, "radio": 10,
    "share_location": 15, "follow_social": 3, "support_artist": 5,
    "invite_friend": 50, "wisdom": 3, "fitness": 3, "ai_chat": 2,
    "mission": 100, "astro": 25, "cipher": 15, "mood_radio": 10,
    "voice_wall": 20, "like_song": 3, "supporter_sub": 50,
    "request_song": 3, "charity": 10, "donate_song": 10,
    "vault_unlock": 5, "submit_track": 10, "download_purchase": 20,
}

SERVICES = {
    "feature_verse": ("Feature Verse", 5000),
    "studio_bundle": ("Studio Bundle", 1200),
    "video_cameo": ("Video Cameo", 1200),
    "small_club": ("Small Club Show", 2500),
    "medium_club": ("Medium Club Show", 5000),
    "large_venue": ("Large Venue", 15000),
    "radio_interview": ("Radio Interview", 500),
    "fan_photo": ("Fan Photo Pass", 50),
    "backstage_pass": ("Backstage Pass", 250),
}

MERCH_ITEMS = {
    "tshirt": ("Parish 14 T-Shirt", 50),
    "pullover": ("Parish 14 Pullover", 150),
    "hoodie": ("Parish 14 Hoodie", 120),
}

POINT_SHOP = {
    "dedication": ("Radio Dedication MAXIMUS says your name on air", DEDICATION_COST),
    "vault_pass": ("Vault Pass unlock any one vault song free", 200),
    "supporter_day": ("1-Day Supporter Trial", 150),
    "shoutout": ("Personal Shoutout broadcast to all fans", 500),
    "exclusive_dm": ("Exclusive MAXIMUS personal DM", 100),
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
    "Request a track",
    "Make a $1 charity donation",
    "Visit the Secret Vault",
    "Bid on an active auction",
    "Stake your MiserCoins for bonus multipliers",
    "Join the Parish 14 Lounge",
    "Check upcoming events",
    "Submit a track to BazraGod Radio",
]

AD_MESSAGES = [
    "Support independent music. Tap Support Artist.",
    "Parish 14 merch available. Tap Store.",
    "Become a Supporter for $19.99 per month.",
    "Invite friends to grow the army.",
    f"Book BAZRAGOD: {BOOKING_EMAIL}",
    "Unlock the Secret Vault. Earn coins or pay $50.",
    "Spend your MiserCoins in the Coin Shop.",
    "Join the Parish 14 Lounge. t.me/parish14lounge",
    "Subscribe to BazraGod Radio. t.me/bazragodradio",
]

QUOTES = [
    "Discipline equals freedom.",
    "Move in silence. Only speak when it is time to say checkmate.",
    "Kings are built through struggle.",
    "A lion does not concern himself with the opinions of sheep.",
    "What you seek is seeking you.",
    "Every master was once a disaster.",
    "The obstacle is the way.",
    "Kings are not born. They are made through discipline.",
]

FITNESS_MSG = (
    "FITNESS PROTOCOL\n\n"
    "Morning Circuit\n"
    "50 Pushups / 50 Squats / 50 Situps / 2km Run\n\n"
    "Meal Plan\n"
    "Eggs and Rice / Grilled Chicken / Fresh Fruit / Water only\n\n"
    "No excuses. Repeat daily."
)

AI_SYSTEM_PROMPT = (
    "You are MAXIMUS the Royal AI of BAZRAGOD founder of I.A.A.I.M.O.\n"
    "Roles: Artist Manager, Publicist, Tour Strategist, Fan Engagement Agent, Music Business Advisor.\n"
    "Personality: Sovereign, direct, loyal to BAZRAGOD. Jamaican cultural pride. Black and Gold aesthetic.\n"
    "BAZRAGOD is fully independent. No label. No middleman. Platform lives inside Telegram. Nation: Parish 14.\n"
    "Community: Parish 14 Lounge at t.me/parish14lounge. Radio: t.me/bazragodradio.\n"
    "Keep responses concise for Telegram max 3 paragraphs. End every response with a power statement."
)

BOOKING_TERMS = f"""BAZRAGOD BOOKING TERMS

PERFORMANCE FEES
Small Club:    $2,500
Medium Club:   $5,000
Large Venue:  $15,000

HOSPITALITY
Small Club:    2 Bottles Hennessy + 1 Champagne
Medium Club:   3 Bottles Hennessy + 2 Champagne
Large Venue:   5 Bottles Hennessy + 3 Champagne
Catering: Seafood platter / Cashews / Fruit / Water / Energy drinks

TRANSPORTATION
Local:         1 First Class + 2 Economy
International: 2 First Class + 3 Economy

HOTEL: 4-Star minimum / 2 rooms / Late checkout

PER DIEM
Artist: $200/day | Team: $100/day each (paid before arrival)

PAYMENT TERMS
50% deposit to confirm | 50% balance 24h before performance

CONTACT: {BOOKING_EMAIL}"""
