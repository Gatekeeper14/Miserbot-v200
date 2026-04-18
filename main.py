import os, re, time, random, asyncio, threading
from datetime import datetime, date, timedelta
from io import BytesIO
from flask import Flask, request as flask_request
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from openai import OpenAI
from database import init_pool, init_db, get_db, release_db
from config import (
    BOT_TOKEN, OWNER_ID, RADIO_CHANNEL_ID, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET,
    OPENAI_API_KEY, BOT_USERNAME, INTRO_FILE_ID, FIRST_MESSAGE_FILE_ID,
    PARISH_LOUNGE, RADIO_CHANNEL_LINK, BOOKING_EMAIL, CASHAPP, PAYPAL,
    SOFT_GATE, SERVICES, MERCH, POINTS, RANKS, MISSIONS, AD_MESSAGES, QUOTES,
    AI_SYSTEM_PROMPT, BOOKING_CARD, SUPPORTED_LANGUAGES,
    SUPPORTER_PRICE, VAULT_UNLOCK_PRICE, VAULT_SUPERFAN_PRICE,
    SONG_PRICE, ALBUM_PRICE, ALBUM_COUNT,
    RADIO_SONG_DELAY, RADIO_BEAT_DELAY, RADIO_DROP_DELAY,
    RADIO_AD_DELAY, RADIO_ANNOUNCE_DELAY, PLAYLIST_TTL,
    tx, get_rank, get_next_rank,
)

try:
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    STRIPE_OK = True
except Exception:
    STRIPE_OK = False

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
flask_app = Flask(__name__)

pending_broadcasts = {}
skill_sessions = {}
_PLAYLIST_CACHE = []
_PLAYLIST_LAST_BUILD = 0.0
radio_loop_running = False
ENTRY_CACHE = {}
GATE_CACHE = {}

main_menu = ReplyKeyboardMarkup([
    ["MUSIC", "STORE"],
    ["COMMUNITY", "FAN ECONOMY"],
    ["SOCIAL", "MAXIMUS AI"],
    ["BazraGod Radio", "My Passport"],
    ["Secret Vault", "Help"],
], resize_keyboard=True)

def is_admin(uid): return uid == OWNER_ID
def uname(update): u = update.effective_user; return u.username or u.first_name or str(u.id)

def award_points(tid, action, username=None, category="earn"):
    base = POINTS.get(action, 1)
    if base == 0: return 0
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO users (telegram_id, username, points)
            VALUES (%s,%s,%s) ON CONFLICT (telegram_id) DO UPDATE
            SET points=users.points+EXCLUDED.points,
                username=COALESCE(EXCLUDED.username, users.username)""",
            (tid, username, base))
        cur.execute("INSERT INTO fan_points (telegram_id, action, pts, category) VALUES (%s,%s,%s,%s)",
            (tid, action, base, category))
        cur.execute("SELECT points FROM users WHERE telegram_id=%s", (tid,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE users SET tier=%s WHERE telegram_id=%s", (get_rank(row[0]), tid))
        conn.commit()
    finally:
        release_db(conn)
    return base

def deduct_points(tid, amount, action="spend"):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points FROM users WHERE telegram_id=%s", (tid,))
        row = cur.fetchone()
        if not row or row[0] < amount: return False
        cur.execute("UPDATE users SET points=points-%s WHERE telegram_id=%s", (amount, tid))
        cur.execute("INSERT INTO fan_points (telegram_id, action, pts, category) VALUES (%s,%s,%s,'spend')", (tid, action, -amount))
        conn.commit(); return True
    finally:
        release_db(conn)

def register_user(tid, username, referrer_id=None):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT telegram_id FROM users WHERE telegram_id=%s", (tid,))
        if cur.fetchone(): return False
        pnum = f"P14-{tid % 100000:05d}"
        cur.execute("INSERT INTO users (telegram_id, username, referrer_id, passport_number) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (tid, username, referrer_id, pnum))
        if referrer_id and referrer_id != tid:
            cur.execute("UPDATE users SET invites=invites+1 WHERE telegram_id=%s", (referrer_id,))
            cur.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (%s,%s)", (referrer_id, tid))
        conn.commit(); return True
    finally:
        release_db(conn)

def get_lang(uid):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT language FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone(); return row[0] if row and row[0] else "en"
    finally:
        release_db(conn)

def set_lang(uid, lang):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET language=%s WHERE telegram_id=%s", (lang, uid)); conn.commit()
    finally:
        release_db(conn)

def mark_entry(uid):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET entry_completed=TRUE WHERE telegram_id=%s", (uid,)); conn.commit()
    finally:
        release_db(conn)
    ENTRY_CACHE[uid] = True

def mark_gate(uid):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET gate_completed=TRUE WHERE telegram_id=%s", (uid,)); conn.commit()
    finally:
        release_db(conn)
    GATE_CACHE[uid] = True

def has_entry(uid):
    if ENTRY_CACHE.get(uid): return True
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT entry_completed FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
        if row and row[0]: ENTRY_CACHE[uid] = True; return True
        return False
    finally:
        release_db(conn)

def has_gate(uid):
    if GATE_CACHE.get(uid): return True
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT gate_completed FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
        if row and row[0]: GATE_CACHE[uid] = True; return True
        return False
    finally:
        release_db(conn)

def heat(likes, plays):
    score = (likes * 5) + (plays / 1000)
    if score >= 250: return "FIRE x5"
    if score >= 100: return "FIRE x4"
    if score >= 50: return "FIRE x3"
    if score >= 10: return "FIRE x2"
    return "FIRE"

def check_duplicate(file_id, title, table):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(f"SELECT id FROM {table} WHERE file_id=%s OR LOWER(title)=LOWER(%s)", (file_id, title))
        return cur.fetchone() is not None
    finally:
        release_db(conn)

def create_checkout(uid, username, product_type, amount_usd, product_name, product_id=""):
    if not STRIPE_OK or not STRIPE_SECRET_KEY: return None
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price_data": {"currency": "usd", "product_data": {"name": product_name}, "unit_amount": int(amount_usd * 100)}, "quantity": 1}],
            mode="payment",
            success_url=f"https://t.me/{BOT_USERNAME}",
            cancel_url=f"https://t.me/{BOT_USERNAME}",
            metadata={"telegram_id": str(uid), "username": username or "", "product_type": product_type, "product_id": product_id},
        )
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO stripe_sessions (telegram_id, session_id, product_type, product_id, amount) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (uid, session.id, product_type, product_id, int(amount_usd)))
            conn.commit()
        finally:
            release_db(conn)
        return session.url
    except Exception as e:
        print(f"Stripe error: {e}"); return None

async def handle_stripe_payment(session_data, bot):
    uid = int(session_data.get("metadata", {}).get("telegram_id", 0))
    product_type = session_data.get("metadata", {}).get("product_type", "")
    product_id = session_data.get("metadata", {}).get("product_id", "")
    session_id = session_data.get("id", "")
    username = session_data.get("metadata", {}).get("username", "fan")
    if not uid: return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE stripe_sessions SET status='completed' WHERE session_id=%s", (session_id,)); conn.commit()
    finally:
        release_db(conn)
    try:
        if product_type == "single_song":
            song_id = int(product_id) if product_id else 0
            if song_id:
                conn = get_db(); cur = conn.cursor()
                try:
                    cur.execute("INSERT INTO downloads (telegram_id, song_id, purchased) VALUES (%s,%s,TRUE) ON CONFLICT (telegram_id,song_id) DO UPDATE SET purchased=TRUE", (uid, song_id))
                    cur.execute("SELECT title, file_id FROM songs WHERE id=%s", (song_id,))
                    song = cur.fetchone(); conn.commit()
                finally:
                    release_db(conn)
                if song:
                    await bot.send_audio(uid, song[1], caption=f"DOWNLOAD DELIVERED\n\n{song[0]}\nBAZRAGOD\n\nYours to keep. Parish 14 Nation.")
                    award_points(uid, "download_purchase", username)
        elif product_type == "single_beat":
            beat_id = int(product_id) if product_id else 0
            if beat_id:
                conn = get_db(); cur = conn.cursor()
                try:
                    cur.execute("SELECT title, file_id FROM beats WHERE id=%s", (beat_id,))
                    beat = cur.fetchone()
                finally:
                    release_db(conn)
                if beat:
                    await bot.send_audio(uid, beat[1], caption=f"BEAT DELIVERED\n\n{beat[0]}\nBAZRAGOD\n\nYours to use. Parish 14 Nation.")
                    award_points(uid, "download_purchase", username)
        elif product_type == "cart_album":
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("SELECT s.id, s.title, s.file_id FROM cart c JOIN songs s ON c.song_id=s.id WHERE c.telegram_id=%s", (uid,))
                items = cur.fetchall()
                for song_id, title, file_id in items:
                    cur.execute("INSERT INTO downloads (telegram_id, song_id, purchased) VALUES (%s,%s,TRUE) ON CONFLICT (telegram_id,song_id) DO UPDATE SET purchased=TRUE", (uid, song_id))
                    await bot.send_audio(uid, file_id, caption=f"{title} - BAZRAGOD")
                cur.execute("DELETE FROM cart WHERE telegram_id=%s", (uid,))
                conn.commit()
            finally:
                release_db(conn)
            await bot.send_message(uid, f"ALBUM DELIVERED\n\n{len(items)} tracks sent.\nBAZRAGOD\n\nParish 14 Nation.")
            award_points(uid, "download_purchase", username)
        elif product_type == "vault_single":
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("SELECT id FROM vault_songs LIMIT 1")
                v = cur.fetchone()
                if v:
                    cur.execute("INSERT INTO vault_access (telegram_id, vault_id, method) VALUES (%s,%s,'payment') ON CONFLICT DO NOTHING", (uid, v[0]))
                    conn.commit()
            finally:
                release_db(conn)
            await bot.send_message(uid, "VAULT UNLOCKED\n\nPick your song from Secret Vault.\n\nParish 14 Nation. BAZRAGOD.")
        elif product_type == "vault_superfan":
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("SELECT id FROM vault_songs")
                for (vid,) in cur.fetchall():
                    cur.execute("INSERT INTO vault_access (telegram_id, vault_id, method) VALUES (%s,%s,'payment') ON CONFLICT DO NOTHING", (uid, vid))
                conn.commit()
            finally:
                release_db(conn)
            await bot.send_message(uid, f"SUPER FAN BUNDLE UNLOCKED\n\nAll vault songs are yours.\n\nContact {BOOKING_EMAIL} with your address for merch.\n\nParish 14 Nation. BAZRAGOD.")
            try: await bot.send_message(OWNER_ID, f"SUPER FAN PURCHASE\n\nFan: @{username} ({uid})\nPrepare merch shipment.")
            except Exception: pass
        elif product_type == "supporter":
            expires = datetime.now() + timedelta(days=30)
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("UPDATE users SET is_supporter=TRUE, tier='Nation Elite', supporter_expires=%s WHERE telegram_id=%s", (expires.date(), uid))
                conn.commit()
            finally:
                release_db(conn)
            award_points(uid, "supporter_sub", username)
            await bot.send_message(uid, f"SUPPORTER ACTIVATED\n\nNation Elite access unlocked.\nExpires: {expires.strftime('%B %d, %Y')}\n\nBAZRAGOD sees you.")
        elif product_type in ("service", "booking", "ladies_hub"):
            service_name = product_id.replace("_", " ").title()
            await bot.send_message(uid, f"SERVICE BOOKING CONFIRMED\n\n{service_name}\n\nBAZRAGOD team contacts you within 24 hours.\n\nContact: {BOOKING_EMAIL}\n\nParish 14 Nation.")
            try: await bot.send_message(OWNER_ID, f"SERVICE BOOKING\n\nFan: @{username} ({uid})\nService: {service_name}")
            except Exception: pass
        elif product_type == "donation":
            amount = session_data.get("amount_total", 0) / 100
            await bot.send_message(uid, f"DONATION RECEIVED\n\n${amount:.2f} supports independent music directly.\nBAZRAGOD thanks you.\n\nParish 14 Nation.")
            award_points(uid, "charity", username)
    except Exception as e:
        print(f"Stripe delivery error: {e}")

def build_playlist():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT title, file_id, plays, likes FROM songs ORDER BY id")
        songs = cur.fetchall()
        cur.execute("SELECT title, file_id FROM drops ORDER BY id"); drops = cur.fetchall()
        cur.execute("SELECT title, file_id FROM beats ORDER BY id"); beats = cur.fetchall()
        cur.execute("SELECT title, file_id FROM announcements ORDER BY id"); ann = cur.fetchall()
    finally:
        release_db(conn)
    if not songs: return []
    pl = []; di = bi = ai = sc = 0
    for s in songs:
        title, file_id, plays, likes = s
        pl.append({"type": "song", "title": title, "file_id": file_id, "plays": plays, "likes": likes})
        sc += 1
        if drops: d = drops[di % len(drops)]; pl.append({"type": "drop", "title": d[0], "file_id": d[1]}); di += 1
        if sc % 2 == 0 and beats: b = beats[bi % len(beats)]; pl.append({"type": "beat", "title": b[0], "file_id": b[1]}); bi += 1
        if sc % 4 == 0:
            pl.append({"type": "ad", "title": "AD", "file_id": None})
            if ann: a = ann[ai % len(ann)]; pl.append({"type": "announcement", "title": a[0], "file_id": a[1]}); ai += 1
    return pl

def invalidate_cache():
    global _PLAYLIST_LAST_BUILD; _PLAYLIST_LAST_BUILD = 0.0

def save_queue(pl):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM radio_queue")
        for i, item in enumerate(pl):
            cur.execute("INSERT INTO radio_queue (file_id, title, item_type, position) VALUES (%s,%s,%s,%s)", (item.get("file_id"), item["title"], item["type"], i))
        conn.commit()
    finally:
        release_db(conn)

def get_queue():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT file_id, title, item_type FROM radio_queue ORDER BY position")
        rows = cur.fetchall()
        return [{"file_id": r[0], "title": r[1], "type": r[2]} for r in rows] if rows else []
    finally:
        release_db(conn)

def get_queue_pos():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT current_index FROM radio_state WHERE id=1")
        row = cur.fetchone(); return row[0] if row else 0
    finally:
        release_db(conn)

def save_queue_pos(pos):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE radio_state SET current_index=%s, last_updated=NOW() WHERE id=1", (pos,)); conn.commit()
    finally:
        release_db(conn)

def log_radio(file_id, title):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO radio_history (file_id, title) VALUES (%s,%s)", (file_id, title))
        cur.execute("DELETE FROM radio_history WHERE id NOT IN (SELECT id FROM radio_history ORDER BY played_at DESC LIMIT 50)")
        conn.commit()
    except Exception: pass
    finally:
        release_db(conn)

USER_RADIO_IDX = {}

def next_for_user(uid):
    pl = build_playlist()
    if not pl: return {"type": "empty", "title": "", "file_id": None}
    idx = USER_RADIO_IDX.get(uid, 0)
    if idx >= len(pl): idx = 0
    item = pl[idx]; USER_RADIO_IDX[uid] = idx + 1
    return item

async def channel_radio_loop(bot):
    global radio_loop_running
    if radio_loop_running: return
    radio_loop_running = True
    if not RADIO_CHANNEL_ID: radio_loop_running = False; return
    channel_id = int(RADIO_CHANNEL_ID)
    pl = build_playlist()
    if pl: save_queue(pl)
    while True:
        try:
            queue = get_queue()
            if not queue:
                pl = build_playlist(); save_queue(pl); queue = pl; save_queue_pos(0)
            pos = get_queue_pos()
            if pos >= len(queue):
                pos = 0; save_queue_pos(0); pl = build_playlist(); save_queue(pl); queue = pl
            item = queue[pos]; save_queue_pos(pos + 1)
            now = datetime.now().strftime("%I:%M %p")
            if item["type"] == "ad":
                await bot.send_message(chat_id=channel_id, text=f"BazraGod Radio {now}\n\n{random.choice(AD_MESSAGES)}\n\nt.me/{BOT_USERNAME}")
                await asyncio.sleep(RADIO_AD_DELAY)
            elif item["type"] in ("announcement", "drop", "beat") and item["file_id"]:
                await bot.send_audio(chat_id=channel_id, audio=item["file_id"], caption=f"{item['title']}\nBazraGod Radio {now}\n\nt.me/{BOT_USERNAME}")
                await asyncio.sleep(RADIO_DROP_DELAY if item["type"] == "drop" else RADIO_BEAT_DELAY)
            elif item["type"] == "song" and item["file_id"]:
                conn = get_db(); cur = conn.cursor()
                try:
                    cur.execute("UPDATE songs SET plays=plays+1 WHERE title=%s", (item["title"],))
                    cur.execute("SELECT plays, likes FROM songs WHERE title=%s", (item["title"],))
                    row = cur.fetchone(); conn.commit()
                finally:
                    release_db(conn)
                plays = row[0] if row else 0; likes = row[1] if row else 0
                await bot.send_audio(chat_id=channel_id, audio=item["file_id"],
                    caption=f"BazraGod Radio {now}\n\n{item['title']}\nBAZRAGOD\n\n{heat(likes, plays)}  {plays:,} plays\n\nJoin: t.me/{BOT_USERNAME}")
                log_radio(item["file_id"], item["title"])
                await asyncio.sleep(RADIO_SONG_DELAY)
        except Exception as e:
            print(f"Radio error: {e}"); await asyncio.sleep(15)

async def maximus_voice(bot, chat_id, text):
    if not openai_client: return
    try:
        resp = openai_client.audio.speech.create(model="tts-1", voice="onyx", input=text[:500], speed=0.95)
        buf = BytesIO(resp.content); buf.name = "maximus.ogg"
        await bot.send_voice(chat_id=chat_id, voice=buf)
    except Exception: pass

SPACESHIP = [
    "      *    *\n   *    [UFO]   *\n      *    *\n\n  . . scanning . . .",
    "   *  *    *   *\n    [UFO]\n  *    *    *\n\n  . . frequency locked .",
    "     *   *\n  *   [UFO]   *\n     *   *\n\n  . . Parish 14 detected .",
]

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; name = uname(update)
    args = context.args if hasattr(context, "args") and context.args else []
    referrer = None
    if args and args[0].isdigit():
        referrer = int(args[0])
        if referrer == uid: referrer = None
    is_new = register_user(uid, name, referrer)
    if is_new and referrer:
        try:
            await context.bot.send_message(referrer, f"New soldier joined your link!\n+{POINTS['invite_friend']} MiserCoins")
            award_points(referrer, "invite_friend")
        except Exception: pass
    award_points(uid, "start", name)
    for frame in SPACESHIP:
        try:
            msg = await update.message.reply_text(frame); await asyncio.sleep(0.8); await msg.delete()
        except Exception: pass
    await update.message.reply_text("B A Z R A G O D\nI.A.A.I.M.O\nPARISH 14\n\nFrequency locked.\nTransmission incoming...")
    await asyncio.sleep(1)
    if has_entry(uid) and has_gate(uid):
        await update.message.reply_text("Welcome back to Parish 14 Nation.", reply_markup=main_menu); return
    if INTRO_FILE_ID:
        await update.message.reply_text("Before you enter press play. This is not optional.")
        await update.message.reply_voice(INTRO_FILE_ID, caption="BAZRAGOD The Vision\nI.A.A.I.M.O",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ENTER ECOSYSTEM", callback_data="entry:step2")]]))
    else:
        await show_gate(update.message, uid)

async def entry_step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if FIRST_MESSAGE_FILE_ID:
        await q.message.reply_voice(FIRST_MESSAGE_FILE_ID, caption="I.A.A.I.M.O\nParish 14 Nation",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("JOIN ECOSYSTEM", callback_data="entry:step3")]]))
    else:
        await show_agreement(q.message)

async def entry_step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); await show_agreement(q.message)

async def show_agreement(msg):
    await msg.reply_text("PARISH 14 TERMS\n\nBy entering you agree to be part of the sovereign music nation.\n\nNo labels. No middlemen. Direct connection between artist and fan.\n\nDo you agree?",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("I AGREE ENTER", callback_data="entry:agreed")]]))

async def entry_agreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    mark_entry(q.from_user.id); await show_gate(q.message, q.from_user.id)

async def show_gate(msg, uid):
    kb = [[InlineKeyboardButton(f"Join {n}", url=u)] for n, u in SOFT_GATE]
    kb.append([InlineKeyboardButton("I Have Joined All ENTER", callback_data="entry:gate_done")])
    await msg.reply_text("LAST STEP\n\nJoin all Parish 14 channels to enter the platform.\n\nThis grows the nation and unlocks your full access.",
        reply_markup=InlineKeyboardMarkup(kb))

async def entry_gate_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; name = q.from_user.username or q.from_user.first_name or str(uid)
    mark_gate(uid)
    lang = get_lang(uid)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points, tier FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
    finally:
        release_db(conn)
    pts = row[0] if row else 0; tier = row[1] if row else "Fan"
    await q.message.reply_text(f"{tx(lang, 'welcome')}\n\nNation Tier:  {tier}\nMiserCoins:   {pts:,}\n\nThe platform is yours.", reply_markup=main_menu)

async def cmd_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"lang:{code}")] for code, label in SUPPORTED_LANGUAGES.items()])
    await update.message.reply_text("Select your language:", reply_markup=kb)

async def lang_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lang = q.data.split(":")[1]
    if lang in SUPPORTED_LANGUAGES:
        set_lang(q.from_user.id, lang)
        await q.message.reply_text(f"{SUPPORTED_LANGUAGES[lang]} saved.")

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled.", reply_markup=main_menu)

async def cmd_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; name = uname(update)
    award_points(uid, "play_song", name)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, plays, likes FROM songs ORDER BY id")
        songs = cur.fetchall()
    finally:
        release_db(conn)
    if not songs:
        await update.message.reply_text(tx(get_lang(uid), "no_songs")); return
    kb = [[InlineKeyboardButton(f"{s[1]}  {heat(s[3], s[2])}", callback_data=f"song:{s[0]}")] for s in songs]
    await update.message.reply_text(f"BAZRAGOD CATALOG\n{len(songs)} tracks\n\nSelect a track", reply_markup=InlineKeyboardMarkup(kb))

async def play_song_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; name = q.from_user.username or str(uid)
    song_id = int(q.data.split(":")[1])
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT title, file_id, plays, likes FROM songs WHERE id=%s", (song_id,))
        song = cur.fetchone()
        if song: cur.execute("UPDATE songs SET plays=plays+1 WHERE id=%s", (song_id,)); conn.commit()
    finally:
        release_db(conn)
    if not song: return
    title, file_id, plays, likes = song; plays += 1
    pts = award_points(uid, "play_song", name)
    await q.message.reply_audio(file_id,
        caption=f"{title}\nBAZRAGOD\n\n{heat(likes, plays)}  {plays:,} plays\n\n+{pts} MiserCoins",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Like", callback_data=f"like:{song_id}"),
            InlineKeyboardButton("Add to Cart", callback_data=f"cart_add:{song_id}"),
            InlineKeyboardButton("Buy $5", callback_data=f"buy_song:{song_id}"),
        ]]))

async def like_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id; song_id = int(q.data.split(":")[1])
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO song_likes (telegram_id, song_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (uid, song_id))
        if cur.rowcount > 0:
            cur.execute("UPDATE songs SET likes=likes+1 WHERE id=%s", (song_id,)); conn.commit()
            award_points(uid, "like_song"); await q.answer("Liked! +3 coins", show_alert=False)
        else:
            await q.answer("Already liked", show_alert=False)
    finally:
        release_db(conn)

async def cmd_beats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, plays FROM beats ORDER BY id")
        beats = cur.fetchall()
    finally:
        release_db(conn)
    if not beats:
        await update.message.reply_text("No beats available yet. Check back soon."); return
    kb = [[InlineKeyboardButton(f"{b[1]}  {b[2]:,} plays", callback_data=f"beat:{b[0]}")] for b in beats]
    await update.message.reply_text(f"BAZRAGOD BEATS\n{len(beats)} available\n\nSelect a beat", reply_markup=InlineKeyboardMarkup(kb))

async def beat_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; name = q.from_user.username or str(uid)
    beat_id = int(q.data.split(":")[1])
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT title, file_id, plays FROM beats WHERE id=%s", (beat_id,))
        beat = cur.fetchone()
        if beat: cur.execute("UPDATE beats SET plays=plays+1 WHERE id=%s", (beat_id,)); conn.commit()
    finally:
        release_db(conn)
    if not beat: return
    title, file_id, plays = beat; plays += 1
    pts = award_points(uid, "play_beat", name)
    await q.message.reply_audio(file_id,
        caption=f"BEAT: {title}\nBAZRAGOD\n\n{plays:,} plays\n\n+{pts} MiserCoins",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Buy Beat $50", callback_data=f"buy_beat:{beat_id}")]]))

async def buy_beat_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; name = q.from_user.username or str(uid)
    beat_id = int(q.data.split(":")[1])
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT title FROM beats WHERE id=%s", (beat_id,))
        beat = cur.fetchone()
    finally:
        release_db(conn)
    if not beat: return
    url = create_checkout(uid, name, "single_beat", 50, f"BAZRAGOD Beat - {beat[0]}", str(beat_id))
    kb = [[InlineKeyboardButton("Pay $50 via Stripe", url=url)]] if url else [[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]
    await q.message.reply_text(f"BUY BEAT\n\n{beat[0]}\nBAZRAGOD\n\nPrice: $50\n\nDelivered instantly after payment.", reply_markup=InlineKeyboardMarkup(kb))

async def buy_song_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; name = q.from_user.username or str(uid)
    song_id = int(q.data.split(":")[1])
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM downloads WHERE telegram_id=%s AND song_id=%s AND purchased=TRUE", (uid, song_id))
        already = cur.fetchone() is not None
        cur.execute("SELECT title FROM songs WHERE id=%s", (song_id,))
        song = cur.fetchone()
    finally:
        release_db(conn)
    if already: await q.answer("You already own this song.", show_alert=True); return
    if not song: return
    url = create_checkout(uid, name, "single_song", SONG_PRICE, f"BAZRAGOD - {song[0]}", str(song_id))
    donation_url = create_checkout(uid, name, "donation", 1, "Support BAZRAGOD $1")
    kb = []
    if donation_url: kb.append([InlineKeyboardButton("Add $1 Donation", url=donation_url)])
    if url: kb.append([InlineKeyboardButton(f"Pay ${SONG_PRICE} via Stripe", url=url)])
    else: kb += [[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]
    await q.message.reply_text(f"BUY SONG\n\n{song[0]}\nBAZRAGOD\n\nPrice: ${SONG_PRICE}\n\nBefore you pay - support the mission with $1?\nEvery dollar goes directly to BAZRAGOD.", reply_markup=InlineKeyboardMarkup(kb))

async def cart_add_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id; song_id = int(q.data.split(":")[1])
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO cart (telegram_id, song_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (uid, song_id))
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM cart WHERE telegram_id=%s", (uid,))
        count = cur.fetchone()[0]
    finally:
        release_db(conn)
    if count >= ALBUM_COUNT: await q.answer(f"Cart: {count} songs = ${ALBUM_PRICE} album deal!", show_alert=False)
    else: await q.answer(f"Added! {count}/{ALBUM_COUNT} for ${ALBUM_PRICE} album deal.", show_alert=False)

async def cmd_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT s.id, s.title FROM cart c JOIN songs s ON c.song_id=s.id WHERE c.telegram_id=%s ORDER BY c.added_at", (uid,))
        items = cur.fetchall()
    finally:
        release_db(conn)
    if not items:
        await update.message.reply_text("YOUR CART\n\nCart is empty.\n\nBrowse music and add songs."); return
    count = len(items)
    price = ALBUM_PRICE if count >= ALBUM_COUNT else count * SONG_PRICE
    deal = f"ALBUM DEAL ${ALBUM_PRICE}" if count >= ALBUM_COUNT else f"{count} song(s) = ${price}\n\nAdd {ALBUM_COUNT - count} more for ${ALBUM_PRICE} album deal"
    text = "YOUR CART\n\n" + "\n".join([f"  {t}" for _, t in items]) + f"\n\n{deal}"
    kb = [[InlineKeyboardButton(f"Remove {t[:20]}", callback_data=f"cart_remove:{i}")] for i, t in items]
    kb.append([InlineKeyboardButton(f"Checkout ${price}", callback_data="cart_checkout")])
    kb.append([InlineKeyboardButton("Clear Cart", callback_data="cart_clear")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def cart_remove_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id; song_id = int(q.data.split(":")[1])
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM cart WHERE telegram_id=%s AND song_id=%s", (uid, song_id)); conn.commit()
    finally:
        release_db(conn)
    await q.answer("Removed.")

async def cart_clear_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM cart WHERE telegram_id=%s", (q.from_user.id,)); conn.commit()
    finally:
        release_db(conn)
    await q.message.reply_text("Cart cleared.")

async def cart_checkout_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; name = q.from_user.username or str(uid)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM cart WHERE telegram_id=%s", (uid,))
        count = cur.fetchone()[0]
    finally:
        release_db(conn)
    if not count: await q.message.reply_text("Cart is empty."); return
    price = ALBUM_PRICE if count >= ALBUM_COUNT else count * SONG_PRICE
    url = create_checkout(uid, name, "cart_album", price, f"BAZRAGOD Custom Album {count} Songs")
    donation_url = create_checkout(uid, name, "donation", 1, "Support BAZRAGOD $1")
    kb = []
    if donation_url: kb.append([InlineKeyboardButton("Add $1 Donation", url=donation_url)])
    if url: kb.append([InlineKeyboardButton(f"Pay ${price} via Stripe", url=url)])
    else: kb += [[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]
    await q.message.reply_text(f"CHECKOUT\n\n{count} song(s)\nTotal: ${price}\n\nBefore you pay - support the mission with $1?\nEvery dollar goes directly to BAZRAGOD. No label. No cut.", reply_markup=InlineKeyboardMarkup(kb))

async def cmd_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; name = uname(update)
    pts = award_points(uid, "radio", name)
    await _play_radio(uid, name, pts, update.message, context)

async def radio_next_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer("Loading...")
    uid = q.from_user.id; name = q.from_user.username or str(uid)
    pts = award_points(uid, "radio", name)
    await _play_radio(uid, name, pts, q.message, context)

async def _play_radio(uid, name, pts, msg, context):
    item = next_for_user(uid)
    now = datetime.now().strftime("%I:%M %p")
    if item["type"] == "empty":
        await msg.reply_text("Radio loading... check back soon."); return
    if item["type"] == "ad":
        await msg.reply_text(f"BazraGod Radio {now}\n\n{random.choice(AD_MESSAGES)}\n\n+{pts} MiserCoins",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Next Track", callback_data="radio:next")]])); return
    if item["type"] in ("drop", "beat", "announcement") and item["file_id"]:
        await msg.reply_audio(item["file_id"], caption=f"BazraGod Radio {now}\n\n+{pts} MiserCoins",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Next Track", callback_data="radio:next")]])); return
    if item["type"] == "song" and item["file_id"]:
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("UPDATE songs SET plays=plays+1 WHERE title=%s", (item["title"],))
            cur.execute("SELECT id, plays, likes FROM songs WHERE title=%s", (item["title"],))
            row = cur.fetchone(); conn.commit()
        finally:
            release_db(conn)
        sid = row[0] if row else 0; plays = row[1] if row else 0; likes = row[2] if row else 0
        await msg.reply_audio(item["file_id"],
            caption=f"BazraGod Radio {now}\n\n{item['title']}\nBAZRAGOD\n\n{heat(likes, plays)}  {plays:,} plays\n\n+{pts} MiserCoins",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Next Track", callback_data="radio:next"),
                InlineKeyboardButton("Like", callback_data=f"like:{sid}"),
                InlineKeyboardButton("Buy $5", callback_data=f"buy_song:{sid}"),
            ]]))
        log_radio(item["file_id"], item["title"])

async def cmd_vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; name = uname(update)
    award_points(uid, "vault_unlock", name)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points FROM users WHERE telegram_id=%s", (uid,))
        fan = cur.fetchone(); fan_pts = fan[0] if fan else 0
        cur.execute("SELECT id, title, required_points FROM vault_songs ORDER BY required_points")
        items = cur.fetchall()
        cur.execute("SELECT vault_id FROM vault_access WHERE telegram_id=%s", (uid,))
        unlocked = {r[0] for r in cur.fetchall()}
    finally:
        release_db(conn)
    if not items:
        await update.message.reply_text(f"SECRET VAULT\n\nYour MiserCoins: {fan_pts:,}\n\nUnreleased BAZRAGOD music.\n\nUnlock by earning MiserCoins or pay ${VAULT_UNLOCK_PRICE} for any song or ${VAULT_SUPERFAN_PRICE} for the Super Fan Bundle.\n\nContent incoming. Stay tuned. Parish 14."); return
    text = f"SECRET VAULT\n\nYour MiserCoins: {fan_pts:,}\n\n"; kb = []
    for vid, title, req_pts in items:
        if vid in unlocked: btn = f"UNLOCKED {title}"
        elif fan_pts >= req_pts: btn = f"UNLOCK {title}"
        else: btn = f"LOCKED {title} - {req_pts:,} coins"
        kb.append([InlineKeyboardButton(btn, callback_data=f"vault:{vid}")])
    kb.append([InlineKeyboardButton(f"Unlock Any Song ${VAULT_UNLOCK_PRICE}", callback_data="vault_pay:single")])
    kb.append([InlineKeyboardButton(f"Super Fan Bundle ${VAULT_SUPERFAN_PRICE}", callback_data="vault_pay:bundle")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def vault_item_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; vault_id = int(q.data.split(":")[1])
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT title, file_id, required_points FROM vault_songs WHERE id=%s", (vault_id,))
        item = cur.fetchone()
        cur.execute("SELECT points FROM users WHERE telegram_id=%s", (uid,))
        fan = cur.fetchone(); fan_pts = fan[0] if fan else 0
        cur.execute("SELECT 1 FROM vault_access WHERE telegram_id=%s AND vault_id=%s", (uid, vault_id))
        already = cur.fetchone() is not None
    finally:
        release_db(conn)
    if not item: return
    title, file_id, req_pts = item
    if already or fan_pts >= req_pts:
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO vault_access (telegram_id, vault_id, method) VALUES (%s,%s,'coins') ON CONFLICT DO NOTHING", (uid, vault_id)); conn.commit()
        finally:
            release_db(conn)
        await q.message.reply_audio(file_id, caption=f"VAULT UNLOCKED\n\n{title}\nBAZRAGOD Exclusive\n\nParish 14 Nation.")
    else:
        await q.answer(f"Need {req_pts - fan_pts:,} more coins to unlock.", show_alert=True)

async def vault_pay_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; name = q.from_user.username or str(uid)
    pay_type = q.data.split(":")[1]
    if pay_type == "single":
        url = create_checkout(uid, name, "vault_single", VAULT_UNLOCK_PRICE, "BAZRAGOD Vault Song Unlock")
        price = VAULT_UNLOCK_PRICE; label = f"Unlock Any 1 Vault Song ${price}"
    else:
        url = create_checkout(uid, name, "vault_superfan", VAULT_SUPERFAN_PRICE, "BAZRAGOD Super Fan Bundle")
        price = VAULT_SUPERFAN_PRICE; label = f"Super Fan Bundle All Vault Songs + Merch ${price}"
    kb = [[InlineKeyboardButton(f"Pay ${price} via Stripe", url=url)]] if url else [[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]
    await q.message.reply_text(f"VAULT PAYMENT\n\n{label}\n\nDelivered instantly after payment.", reply_markup=InlineKeyboardMarkup(kb))

async def cmd_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("BAZRAGOD STORE AND SERVICES\n\nMusic. Beats. Features. Bookings. Everything.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Music Store", callback_data="store:music")],
            [InlineKeyboardButton("Beat Store", callback_data="store:beats")],
            [InlineKeyboardButton("Donate $1", callback_data="store:donate1")],
            [InlineKeyboardButton("Feature Verse $5,000", callback_data="service:feature_verse")],
            [InlineKeyboardButton("Video Cameo $1,200", callback_data="service:video_cameo")],
            [InlineKeyboardButton("Studio Bundle $1,200", callback_data="service:studio_bundle")],
            [InlineKeyboardButton("Club Booking", callback_data="store:club")],
            [InlineKeyboardButton("Ladies Hub", callback_data="store:ladies")],
            [InlineKeyboardButton("Merch", callback_data="store:merch")],
            [InlineKeyboardButton("Supporter $19.99/mo", callback_data="store:supporter")],
            [InlineKeyboardButton("Booking Card", callback_data="store:booking_card")],
        ]))

async def store_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; name = q.from_user.username or str(uid)
    action = q.data.split(":")[1]
    if action == "music":
        await cmd_music(update, context)
    elif action == "beats":
        await cmd_beats(update, context)
    elif action == "donate1":
        url = create_checkout(uid, name, "donation", 1, "Support BAZRAGOD $1")
        kb = [[InlineKeyboardButton("Donate $1 via Stripe", url=url)]] if url else [[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]
        await q.message.reply_text("SUPPORT $1\n\nEvery dollar goes directly to BAZRAGOD.\nNo label. No cut. Pure sovereign support.", reply_markup=InlineKeyboardMarkup(kb))
    elif action == "club":
        await q.message.reply_text("CLUB BOOKING\n\nBook BAZRAGOD for your event.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Small Club ${SERVICES['small_club'][1]:,}", callback_data="service:small_club")],
                [InlineKeyboardButton(f"Medium Club ${SERVICES['medium_club'][1]:,}", callback_data="service:medium_club")],
                [InlineKeyboardButton(f"Large Venue ${SERVICES['large_venue'][1]:,}", callback_data="service:large_venue")],
                [InlineKeyboardButton("Radio Interview $500", callback_data="service:radio_interview")],
            ]))
    elif action == "ladies":
        await q.message.reply_text("LADIES HUB\n\nExclusive female fan community for Parish 14 Nation.\n\nExperiences designed for the Queens of the movement.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Fan Photo Pass ${SERVICES['fan_photo'][1]}", callback_data="service:fan_photo")],
                [InlineKeyboardButton(f"Backstage Pass ${SERVICES['backstage_pass'][1]}", callback_data="service:backstage_pass")],
                [InlineKeyboardButton("Parish 14 Lounge", url=PARISH_LOUNGE)],
            ]))
    elif action == "merch":
        await q.message.reply_text("PARISH 14 MERCH\n\nOfficial BAZRAGOD clothing.\nSizes: M / L / XL",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"T-Shirt ${MERCH['tshirt'][1]}", callback_data="merch:tshirt")],
                [InlineKeyboardButton(f"Pullover ${MERCH['pullover'][1]}", callback_data="merch:pullover")],
                [InlineKeyboardButton(f"Hoodie ${MERCH['hoodie'][1]}", callback_data="merch:hoodie")],
            ]))
    elif action == "supporter":
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("SELECT is_supporter, supporter_expires FROM users WHERE telegram_id=%s", (uid,))
            row = cur.fetchone()
        finally:
            release_db(conn)
        active = row[0] if row else False; expires = row[1] if row else None
        if active:
            await q.message.reply_text(f"PARISH 14 SUPPORTER\n\nActive\nExpires: {expires.strftime('%B %d, %Y') if expires else 'Active'}\n\nBenefits:\nNation Elite badge\nPriority shoutouts\nEarly access songs\n\nThank you."); return
        url = create_checkout(uid, name, "supporter", SUPPORTER_PRICE, "Parish 14 Supporter $19.99/month", "elite")
        kb = [[InlineKeyboardButton(f"Subscribe ${SUPPORTER_PRICE:.2f}/mo via Stripe", url=url)]] if url else []
        kb += [[InlineKeyboardButton(f"CashApp ${SUPPORTER_PRICE:.2f}/mo", url=CASHAPP)], [InlineKeyboardButton(f"PayPal ${SUPPORTER_PRICE:.2f}/mo", url=PAYPAL)]]
        await q.message.reply_text(f"PARISH 14 SUPPORTER\n\n${SUPPORTER_PRICE:.2f}/month\n\nBenefits:\nNation Elite badge\nPriority radio shoutouts\nEarly access songs\nLeaderboard priority", reply_markup=InlineKeyboardMarkup(kb))
    elif action == "booking_card":
        await q.message.reply_text(BOOKING_CARD,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Book Small Club ${SERVICES['small_club'][1]:,}", callback_data="service:small_club")],
                [InlineKeyboardButton(f"Book Medium Club ${SERVICES['medium_club'][1]:,}", callback_data="service:medium_club")],
                [InlineKeyboardButton(f"Book Large Venue ${SERVICES['large_venue'][1]:,}", callback_data="service:large_venue")],
                [InlineKeyboardButton("Contact BAZRAGOD", url=f"https://t.me/{BOT_USERNAME}")],
            ]))

async def service_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; name = q.from_user.username or str(uid)
    key = q.data.split(":")[1]
    if key not in SERVICES: return
    service_name, price = SERVICES[key]
    url = create_checkout(uid, name, "service", price, f"BAZRAGOD - {service_name}", key)
    kb = [[InlineKeyboardButton(f"Pay ${price:,} via Stripe", url=url)]] if url else [[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]
    await q.message.reply_text(f"SERVICE BOOKING\n\n{service_name}\nPrice: ${price:,}\n\nBAZRAGOD team contacts you within 24 hours after payment.", reply_markup=InlineKeyboardMarkup(kb))

async def merch_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; name = q.from_user.username or str(uid)
    key = q.data.split(":")[1]
    if key not in MERCH: return
    item_name, price = MERCH[key]
    url = create_checkout(uid, name, "service", price, f"Parish 14 {item_name}", key)
    kb = [[InlineKeyboardButton(f"Pay ${price} via Stripe", url=url)]] if url else [[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]
    await q.message.reply_text(f"PARISH 14 ORDER\n\nItem: {item_name}\nPrice: ${price}\nSizes: M / L / XL\n\nAfter payment send: size + shipping address", reply_markup=InlineKeyboardMarkup(kb))
    try: await telegram_app.bot.send_message(OWNER_ID, f"MERCH ORDER\nFan: @{name} ({uid})\nItem: {item_name}\nPrice: ${price}")
    except Exception: pass
async def cmd_passport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; name = uname(update)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT username, points, invites, tier, city, country, joined_at, is_supporter, passport_number FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
        if not row: await update.message.reply_text("Send /start first."); return
        username, points, invites, tier, city, country, joined_at, is_sup, pnum = row
        cur.execute("SELECT COUNT(*) FROM users WHERE points > %s", (points,)); global_rank = cur.fetchone()[0] + 1
        cur.execute("SELECT COUNT(*) FROM downloads WHERE telegram_id=%s AND purchased=TRUE", (uid,)); downloads = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM vault_access WHERE telegram_id=%s", (uid,)); vaults = cur.fetchone()[0]
    finally:
        release_db(conn)
    display = f"@{username}" if username else name
    location = f"{city}, {country}" if city else "Not shared"
    joined = joined_at.strftime("%B %Y") if joined_at else "Unknown"
    sup_badge = "  SUPPORTER" if is_sup else ""
    pnum = pnum or f"P14-{uid % 100000:05d}"
    await update.message.reply_text(
        f"PARISH 14 PASSPORT\n\n"
        f"Passport:     {pnum}\n"
        f"Name:         {display}{sup_badge}\n"
        f"Nation Tier:  {tier}\n"
        f"MiserCoins:   {points:,}\n"
        f"Global Rank:  #{global_rank}\n"
        f"Invites:      {invites}\n"
        f"Downloads:    {downloads}\n"
        f"Vault:        {vaults} unlocked\n"
        f"City:         {location}\n"
        f"Joined:       {joined}\n\n"
        f"NEXT: {get_next_rank(points)}\n\n"
        f"- - - - - - - - - -\n\n"
        f"{BOOKING_CARD}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Book Small Club ${SERVICES['small_club'][1]:,}", callback_data="service:small_club")],
            [InlineKeyboardButton(f"Book Medium Club ${SERVICES['medium_club'][1]:,}", callback_data="service:medium_club")],
            [InlineKeyboardButton(f"Book Large Venue ${SERVICES['large_venue'][1]:,}", callback_data="service:large_venue")],
            [InlineKeyboardButton("Contact BAZRAGOD", url=f"https://t.me/{BOT_USERNAME}")],
        ]))

async def cmd_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points, tier, invites FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM users WHERE points > COALESCE((SELECT points FROM users WHERE telegram_id=%s),0)", (uid,))
        global_rank = cur.fetchone()[0] + 1
    finally:
        release_db(conn)
    pts, tier, invites = row if row else (0, "Fan", 0)
    await update.message.reply_text(
        f"YOUR MISERCOINS\n\nCoins:       {pts:,}\nGlobal Rank: #{global_rank}\nNation Tier: {tier}\nInvites:     {invites}\n\nNEXT: {get_next_rank(pts)}\n\nKeep grinding. Parish 14.")

async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("PARISH 14 LEADERBOARD",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Today", callback_data="lb:today"),
            InlineKeyboardButton("Week", callback_data="lb:week"),
            InlineKeyboardButton("All Time", callback_data="lb:alltime"),
        ]]))

async def leaderboard_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lb_type = q.data.split(":")[1]
    conn = get_db(); cur = conn.cursor()
    try:
        if lb_type == "today":
            cur.execute("SELECT u.username, COALESCE(SUM(fp.pts),0) as pts, u.tier FROM users u LEFT JOIN fan_points fp ON u.telegram_id=fp.telegram_id AND fp.logged_at>NOW()-INTERVAL '24 hours' GROUP BY u.username, u.tier ORDER BY pts DESC LIMIT 10")
            label = "TODAY"
        elif lb_type == "week":
            cur.execute("SELECT u.username, COALESCE(SUM(fp.pts),0) as pts, u.tier FROM users u LEFT JOIN fan_points fp ON u.telegram_id=fp.telegram_id AND fp.logged_at>NOW()-INTERVAL '7 days' GROUP BY u.username, u.tier ORDER BY pts DESC LIMIT 10")
            label = "THIS WEEK"
        else:
            cur.execute("SELECT username, points, tier FROM users ORDER BY points DESC LIMIT 10")
            label = "ALL TIME"
        rows = cur.fetchall()
    finally:
        release_db(conn)
    text = f"PARISH 14 {label}\n\n"
    for i, (username, points, tier) in enumerate(rows):
        text += f"{i+1}. @{username or 'Anonymous'}\n{points:,} coins  {tier}\n\n"
    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Today", callback_data="lb:today"),
            InlineKeyboardButton("Week", callback_data="lb:week"),
            InlineKeyboardButton("All Time", callback_data="lb:alltime"),
        ]]))
    except Exception:
        await q.message.reply_text(text)

async def cmd_missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    today = date.today()
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT completed FROM missions WHERE telegram_id=%s AND mission_date=%s", (uid, today))
        row = cur.fetchone()
    finally:
        release_db(conn)
    if row and row[0]:
        await update.message.reply_text("DAILY MISSIONS\n\nAlready completed today.\n\nCome back tomorrow. Parish 14."); return
    mission = random.choice(MISSIONS)
    await update.message.reply_text(
        f"DAILY MISSION\n\n{mission}\n\nReward: +{POINTS['mission']} MiserCoins\n\nComplete it then tap below.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Mark Complete", callback_data=f"mission:complete:{uid}")]]))

async def mission_complete_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = int(q.data.split(":")[2])
    if q.from_user.id != uid: return
    today = date.today()
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT completed FROM missions WHERE telegram_id=%s AND mission_date=%s", (uid, today))
        row = cur.fetchone()
        if row and row[0]: await q.message.reply_text("Already completed today."); return
        cur.execute("INSERT INTO missions (telegram_id, mission_date, completed) VALUES (%s,%s,TRUE) ON CONFLICT (telegram_id, mission_date) DO UPDATE SET completed=TRUE", (uid, today))
        conn.commit()
    finally:
        release_db(conn)
    name = q.from_user.username or str(uid)
    pts = award_points(uid, "mission", name)
    await q.message.reply_text(f"MISSION COMPLETE\n\n+{pts} MiserCoins\n\n{tx(get_lang(uid), 'mission_done')}")

async def cmd_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT invites FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone(); invites = row[0] if row else 0
    finally:
        release_db(conn)
    await update.message.reply_text(
        f"REFERRAL SYSTEM\n\nYour invite link:\n{link}\n\nInvites: {invites}\n\nMILESTONES\n1 invite = +{POINTS['invite_friend']} coins\n5 invites = +300 bonus coins\n10 invites = Vault access\n50 invites = Nation Elite",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Share Link", url=f"https://t.me/share/url?url={link}&text=Join+Parish+14+Nation")]]))

async def cmd_radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT COALESCE(country,'Unknown'), COUNT(*) FROM fan_locations GROUP BY country ORDER BY 2 DESC LIMIT 15")
        cr = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM fan_locations"); total_mapped = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users"); total_fans = cur.fetchone()[0]
        cur.execute("SELECT latitude, longitude FROM fan_locations WHERE telegram_id=%s", (uid,)); my_loc = cur.fetchone()
    finally:
        release_db(conn)
    if not cr:
        await update.message.reply_text("PARISH 14 FAN RADAR\n\nNo fans mapped yet.\n\nBe the first. Share your location.\n\nParish 14 Nation is global."); return
    pct = round((total_mapped / total_fans * 100), 1) if total_fans > 0 else 0
    text = f"PARISH 14 FAN RADAR\n\nFans mapped: {total_mapped} of {total_fans} ({pct}%)\n\nTOP COUNTRIES\n"
    for i, (country, fans) in enumerate(cr):
        text += f"{i+1}. {country}  {fans} fans\n"
    text += f"\nYOUR LOCATION: {'Mapped' if my_loc else 'Not shared. Tap Share Location.'}"
    text += "\n\nThis is where BAZRAGOD's army stands. Parish 14 Nation is worldwide."
    await update.message.reply_text(text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Share My Location", callback_data="action:share_location")]]))

async def location_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup([[KeyboardButton("Send Location", request_location=True)], ["Back to Menu"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(f"Share your location to put your city on the Parish 14 fan map.\n\nEarn +{POINTS['share_location']} MiserCoins", reply_markup=kb)

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; name = uname(update)
    loc = update.message.location
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO fan_locations (telegram_id, latitude, longitude, updated_at) VALUES (%s,%s,%s,NOW()) ON CONFLICT (telegram_id) DO UPDATE SET latitude=EXCLUDED.latitude, longitude=EXCLUDED.longitude, updated_at=NOW()", (uid, loc.latitude, loc.longitude))
        conn.commit()
    finally:
        release_db(conn)
    pts = award_points(uid, "share_location", name)
    await update.message.reply_text(f"{tx(get_lang(uid), 'location_saved')}\n\n+{pts} MiserCoins", reply_markup=main_menu)

async def cmd_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    skill_sessions[uid] = {"step": "skill_name"}
    await update.message.reply_text(
        "SKILLS HARVEST\n\nContribute your skills to Parish 14 Nation.\n\nWhat is your skill?\n\nExamples: Design, Video, Photography, Promotion, Web Dev, Translation, Music Production\n\nType your skill name now.")

async def cmd_volunteer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "VOLUNTEER MISSIONS\n\nEarn MiserCoins by contributing to the nation.\n\nAvailable missions:\n\nShare a BAZRAGOD post on your socials\nCreate a fan video or design\nTranslate content to your language\nPromote BazraGod Radio in your community\nRecruit new fans to Parish 14\n\nEach completed mission earns +100 MiserCoins.\n\nTap below to claim your mission reward.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Claim Mission Reward", callback_data="volunteer:claim")]]))

async def volunteer_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; name = q.from_user.username or str(uid)
    pts = award_points(uid, "volunteer_claim", name)
    await q.message.reply_text(f"VOLUNTEER CLAIM SUBMITTED\n\n+{pts} MiserCoins\n\nAdmin will verify your contribution.\n\nParish 14 Nation grows through you.")
    try: await telegram_app.bot.send_message(OWNER_ID, f"VOLUNTEER CLAIM\n\nFan: @{name} ({uid})\nVerify their contribution and confirm.")
    except Exception: pass

async def cmd_maximus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not openai_client:
        await update.message.reply_text("MAXIMUS is offline. OPENAI_API_KEY not set."); return
    uid = update.effective_user.id; name = uname(update)
    context.user_data["ai_active"] = True
    context.user_data["ai_history"] = []
    pts = award_points(uid, "ai_chat", name)
    await update.message.reply_text(f"MAXIMUS ONLINE\n\nRoyal AI of BAZRAGOD.\nManager. Publicist. Strategist.\n\nAsk me anything.\nType /cancel to return.\n\n+{pts} MiserCoins")

async def handle_maximus_chat(uid, text, update, context):
    if not context.user_data.get("ai_active"): return False
    if not openai_client: return False
    name = uname(update)
    history = context.user_data.get("ai_history", [])
    history.append({"role": "user", "content": text})
    if len(history) > 10: history = history[-10:]
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": AI_SYSTEM_PROMPT}, *history],
            max_tokens=400)
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        context.user_data["ai_history"] = history
        award_points(uid, "ai_chat", name)
        await update.message.reply_text(f"MAXIMUS\n\n{reply}")
        await maximus_voice(context.bot, uid, reply)
    except Exception as e:
        await update.message.reply_text(f"MAXIMUS error: {str(e)}")
    return True

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    audio = update.message.audio
    if not audio or not is_admin(uid): return
    title = audio.title or audio.file_name or (update.message.caption or "").strip() or "Untitled"
    file_id = audio.file_id
    caption = (update.message.caption or "").strip().lower()
    tag_map = {
        "#song": ("songs", "Song"),
        "#beat": ("beats", "Beat"),
        "#drop": ("drops", "Drop"),
        "#announce": ("announcements", "Announcement"),
    }
    if "#vault" in caption:
        req_pts = 1000
        match = re.search(r"#vault\s*(\d+)", caption)
        if match: req_pts = int(match.group(1))
        if check_duplicate(file_id, title, "vault_songs"):
            await update.message.reply_text(f"DUPLICATE DETECTED\n\n{title!r} already exists in Vault.\n\nUpload cancelled."); return
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO vault_songs (title, file_id, required_points) VALUES (%s,%s,%s) RETURNING id", (title, file_id, req_pts))
            new_id = cur.fetchone()[0]; conn.commit()
        finally:
            release_db(conn)
        await update.message.reply_text(f"VAULT SONG ADDED\n\nID: {new_id}\nTitle: {title}\nRequired: {req_pts:,} coins")
        invalidate_cache(); return
    for tag, (dest, label) in tag_map.items():
        if tag in caption:
            if check_duplicate(file_id, title, dest):
                await update.message.reply_text(f"DUPLICATE DETECTED\n\n{title!r} already exists in {label}s.\n\nUpload cancelled."); return
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute(f"INSERT INTO {dest} (title, file_id) VALUES (%s,%s) RETURNING id", (title, file_id))
                new_id = cur.fetchone()[0]; conn.commit()
            finally:
                release_db(conn)
            await update.message.reply_text(f"{label.upper()} ADDED\n\nID: {new_id}\nTitle: {title}")
            invalidate_cache(); pl = build_playlist(); save_queue(pl); return
    await update.message.reply_text(
        f"CLASSIFY UPLOAD\n\nTitle: {title}\n\nWhat type is this audio?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Song", callback_data=f"upload:songs:{file_id}:{title}")],
            [InlineKeyboardButton("Beat", callback_data=f"upload:beats:{file_id}:{title}")],
            [InlineKeyboardButton("Drop", callback_data=f"upload:drops:{file_id}:{title}")],
            [InlineKeyboardButton("Announcement", callback_data=f"upload:announcements:{file_id}:{title}")],
            [InlineKeyboardButton("Vault 1000 coins", callback_data=f"upload:vault:1000:{file_id}:{title}")],
        ]))

async def upload_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    parts = q.data.split(":")
    dest = parts[1]
    if dest == "vault":
        req_pts = int(parts[2]); file_id = parts[3]; title = ":".join(parts[4:])
        if check_duplicate(file_id, title, "vault_songs"):
            await q.message.reply_text(f"DUPLICATE DETECTED\n\n{title!r} already in Vault."); return
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO vault_songs (title, file_id, required_points) VALUES (%s,%s,%s) RETURNING id", (title, file_id, req_pts))
            new_id = cur.fetchone()[0]; conn.commit()
        finally:
            release_db(conn)
        await q.message.reply_text(f"VAULT SONG ADDED\n\nID: {new_id}\nTitle: {title}"); return
    file_id = parts[2]; title = ":".join(parts[3:])
    if check_duplicate(file_id, title, dest):
        await q.message.reply_text(f"DUPLICATE DETECTED\n\n{title!r} already exists."); return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(f"INSERT INTO {dest} (title, file_id) VALUES (%s,%s) RETURNING id", (title, file_id))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    if row:
        await q.message.reply_text(f"ADDED\n\nID: {row[0]}\nTitle: {title}")
        invalidate_cache(); pl = build_playlist(); save_queue(pl)

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text(
        f"ADMIN PANEL v18.000\n\n"
        f"Radio: {'ACTIVE' if radio_loop_running else 'STANDBY'}\n\n"
        f"UPLOAD\nSend audio with caption tag:\n#song #beat #drop #announce #vault 1000\nDuplicate protection active on all uploads.\n\n"
        f"COMMANDS\n/start_radio\n/premiere song_id\n/list_songs\n/delete_song id\n/list_vault\n/delete_vault id\n/vault_unlock uid single|bundle\n/unlock_download uid song_id\n/activate_supporter uid\n/broadcast\n/shoutout @username\n/announce message\n/add_event title desc YYYY-MM-DD location\n/stats\n/weekly")

async def cmd_start_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not RADIO_CHANNEL_ID: await update.message.reply_text("RADIO_CHANNEL_ID not set."); return
    if radio_loop_running: await update.message.reply_text("Radio already running."); return
    asyncio.run_coroutine_threadsafe(channel_radio_loop(telegram_app.bot), loop)
    await update.message.reply_text(f"Radio STARTED. Broadcasting to {RADIO_CHANNEL_ID}. Parish 14 Nation.")

async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    pending_broadcasts[OWNER_ID] = True
    await update.message.reply_text("BROADCAST MODE\n\nSend your message now.\n/cancel to abort.")

async def cmd_shoutout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if not args: await update.message.reply_text("Usage: /shoutout @username"); return
    msg = f"SHOUTOUT FROM BAZRAGOD\n\nBig up {args[0]} real Parish 14 energy.\n\nI.A.A.I.M.O"
    sent = await _do_broadcast(msg)
    await update.message.reply_text(f"Shoutout sent to {sent} fans.")

async def cmd_announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    text = " ".join(context.args)
    if not text: await update.message.reply_text("Usage: /announce <message>"); return
    sent = await _do_broadcast(f"OFFICIAL ANNOUNCEMENT\n\n{text}\n\nBAZRAGOD")
    await update.message.reply_text(f"Sent to {sent} fans.")

async def _do_broadcast(text):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT telegram_id FROM users"); fans = cur.fetchall()
    finally:
        release_db(conn)
    sent = 0
    for (fid,) in fans:
        try: await telegram_app.bot.send_message(fid, text); sent += 1
        except Exception: pass
    return sent

async def cmd_premiere(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if not args or not args[0].isdigit(): await update.message.reply_text("Usage: /premiere <song_id>"); return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE songs SET rotation='A' WHERE id=%s RETURNING title", (int(args[0]),))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    if not row: await update.message.reply_text("Song not found."); return
    invalidate_cache(); pl = build_playlist(); save_queue(pl)
    sent = await _do_broadcast(f"WORLD PREMIERE\n\n'{row[0]}' dropping now.\n\nBAZRAGOD drops it here first.\nNo label. No middleman. Parish 14 Nation.")
    await update.message.reply_text(f"Premiere sent to {sent} fans.")

async def cmd_list_songs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, plays, likes, rotation FROM songs ORDER BY id"); rows = cur.fetchall()
    finally:
        release_db(conn)
    rb = {"A": "Hot", "B": "Mid", "C": "Deep"}
    text = f"SONGS  {len(rows)}\n\n"
    for r in rows:
        text += f"[{r[0]}] {rb.get(r[4],'')} {r[1]}\n{heat(r[3], r[2])} {r[2]:,} plays\n"
    await update.message.reply_text(text or "No songs.")

async def cmd_delete_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if not args or not args[0].isdigit(): await update.message.reply_text("Usage: /delete_song <id>"); return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM songs WHERE id=%s RETURNING title", (int(args[0]),))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    invalidate_cache(); pl = build_playlist(); save_queue(pl)
    await update.message.reply_text(f"Deleted: {row[0]}" if row else "Not found.")

async def cmd_list_vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, required_points FROM vault_songs ORDER BY id"); rows = cur.fetchall()
    finally:
        release_db(conn)
    text = f"VAULT SONGS  {len(rows)}\n\n"
    for r in rows:
        text += f"[{r[0]}] {r[1]}\n{r[2]:,} coins\n"
    await update.message.reply_text(text or "Vault empty.")

async def cmd_delete_vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if not args or not args[0].isdigit(): await update.message.reply_text("Usage: /delete_vault <id>"); return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM vault_songs WHERE id=%s RETURNING title", (int(args[0]),))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    await update.message.reply_text(f"Deleted: {row[0]}" if row else "Not found.")

async def cmd_vault_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if len(args) < 2: await update.message.reply_text("Usage: /vault_unlock <uid> <single|bundle>"); return
    fan_id = int(args[0]); pay_type = args[1]
    conn = get_db(); cur = conn.cursor()
    try:
        if pay_type == "bundle":
            cur.execute("SELECT id FROM vault_songs")
            for (vid,) in cur.fetchall():
                cur.execute("INSERT INTO vault_access (telegram_id, vault_id, method) VALUES (%s,%s,'admin') ON CONFLICT DO NOTHING", (fan_id, vid))
        conn.commit()
    finally:
        release_db(conn)
    await update.message.reply_text(f"Vault unlocked for {fan_id}.")
    try:
        msg = "VAULT ACCESS GRANTED\n\nAll vault songs are yours.\n\nParish 14." if pay_type == "bundle" else "VAULT ACCESS GRANTED\n\nGo to Secret Vault to choose your song.\n\nParish 14."
        await context.bot.send_message(fan_id, msg)
    except Exception: pass

async def cmd_unlock_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if len(args) < 2: await update.message.reply_text("Usage: /unlock_download <uid> <song_id>"); return
    fan_id = int(args[0]); song_id = int(args[1])
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO downloads (telegram_id, song_id, purchased) VALUES (%s,%s,TRUE) ON CONFLICT (telegram_id,song_id) DO UPDATE SET purchased=TRUE", (fan_id, song_id))
        cur.execute("SELECT title, file_id FROM songs WHERE id=%s", (song_id,))
        song = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    if song:
        await update.message.reply_text(f"Download unlocked for {fan_id}: {song[0]}")
        try: await context.bot.send_audio(fan_id, song[1], caption=f"DOWNLOAD UNLOCKED\n\n{song[0]}\nBAZRAGOD\n\nYours to keep. Parish 14 Nation.")
        except Exception: pass

async def cmd_activate_supporter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if not args or not args[0].isdigit(): await update.message.reply_text("Usage: /activate_supporter <uid>"); return
    fan_id = int(args[0])
    expires = date.today() + timedelta(days=30)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET is_supporter=TRUE, tier='Nation Elite', supporter_expires=%s WHERE telegram_id=%s RETURNING username", (expires, fan_id))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    if row:
        award_points(fan_id, "supporter_sub")
        await update.message.reply_text(f"@{row[0]} activated. Expires: {expires}")
        try: await context.bot.send_message(fan_id, f"PARISH 14 SUPPORTER ACTIVATED\n\nNation Elite unlocked.\nExpires: {expires.strftime('%B %d, %Y')}\n\nBAZRAGOD sees you.")
        except Exception: pass
    else:
        await update.message.reply_text("Fan not found.")

async def cmd_add_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if len(args) < 4: await update.message.reply_text("Usage: /add_event <title> <desc> <YYYY-MM-DD> <location>"); return
    title = args[0].replace("_"," "); description = args[1].replace("_"," ")
    try: event_date = datetime.strptime(args[2], "%Y-%m-%d")
    except Exception: await update.message.reply_text("Date format: YYYY-MM-DD"); return
    location = args[3].replace("_"," ")
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO events (title, description, event_date, location) VALUES (%s,%s,%s,%s) RETURNING id", (title, description, event_date, location))
        eid = cur.fetchone()[0]; conn.commit()
    finally:
        release_db(conn)
    await update.message.reply_text(f"EVENT ADDED\n\nID: {eid}\nTitle: {title}\nDate: {event_date.strftime('%d/%m/%Y')}\nLocation: {location}")
    await _do_broadcast(f"NEW EVENT ANNOUNCED\n\n{title}\n{description}\nDate: {event_date.strftime('%d %B %Y')}\nLocation: {location}")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM users"); total_fans = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM songs"); total_songs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM beats"); total_beats = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(plays),0) FROM songs"); total_plays = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM downloads WHERE purchased=TRUE"); total_sales = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM stripe_sessions WHERE status='completed'"); stripe_sales = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fan_locations"); mapped = cur.fetchone()[0]
        if is_admin(uid):
            cur.execute("SELECT COUNT(*) FROM users WHERE is_supporter=TRUE"); supporters = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(points),0) FROM users"); total_pts = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM skills WHERE status='pending'"); pending_skills = cur.fetchone()[0]
    finally:
        release_db(conn)
    if is_admin(uid):
        await update.message.reply_text(
            f"MISERBOT STATS v18.000\n\n"
            f"Radio:         {'ACTIVE' if radio_loop_running else 'STANDBY'}\n"
            f"Total Fans:    {total_fans:,}\n"
            f"Supporters:    {supporters}\n"
            f"MiserCoins:    {total_pts:,}\n"
            f"Songs:         {total_songs}\n"
            f"Beats:         {total_beats}\n"
            f"Total Plays:   {total_plays:,}\n"
            f"Downloads:     {total_sales}\n"
            f"Stripe Sales:  {stripe_sales}\n"
            f"Fans Mapped:   {mapped}\n"
            f"Pending Skills:{pending_skills}")
    else:
        await update.message.reply_text(
            f"PLATFORM STATISTICS\n\n"
            f"Total fans:  {total_fans:,}\n"
            f"Songs:       {total_songs}\n"
            f"Beats:       {total_beats}\n"
            f"Total plays: {total_plays:,}\n"
            f"Fans mapped: {mapped}\n\n"
            f"Parish 14 Nation. BAZRAGOD.")

async def cmd_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM users"); total_fans = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE joined_at>NOW()-INTERVAL '7 days'"); new_fans = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(points),0) FROM users"); total_pts = cur.fetchone()[0]
        cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 3"); top_fans = cur.fetchall()
        cur.execute("SELECT title, plays FROM songs ORDER BY plays DESC LIMIT 3"); top_songs = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM stripe_sessions WHERE status='completed'"); stripe_done = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM downloads WHERE purchased=TRUE"); total_downloads = cur.fetchone()[0]
    finally:
        release_db(conn)
    fans_text = "\n".join([f"  @{f}  {p:,} coins" for f, p in top_fans if f]) or "  None yet"
    songs_text = "\n".join([f"  {t_}  {p_:,} plays" for t_, p_ in top_songs]) or "  None"
    await update.message.reply_text(
        f"WEEKLY INTEL REPORT\n{datetime.now().strftime('%d %B %Y')}\n\n"
        f"Total Fans:    {total_fans:,}\n"
        f"New This Week: {new_fans}\n"
        f"Total Coins:   {total_pts:,}\n"
        f"Stripe Sales:  {stripe_done}\n"
        f"Downloads:     {total_downloads}\n\n"
        f"TOP FANS\n{fans_text}\n\n"
        f"TOP SONGS\n{songs_text}\n\n"
        f"MAXIMUS INTEL v18.000")

async def cmd_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT title, description, event_date, location, ticket_url FROM events WHERE status='upcoming' AND event_date>NOW() ORDER BY event_date LIMIT 10")
        event_list = cur.fetchall()
    finally:
        release_db(conn)
    if not event_list:
        await update.message.reply_text("UPCOMING EVENTS\n\nNo events announced yet.\n\nStay tuned. Parish 14 Nation is global."); return
    text = "UPCOMING EVENTS\n\n"; kb = []
    for title, description, event_date, location, ticket_url in event_list:
        text += f"{title}\n{description}\nDate: {event_date.strftime('%d/%m/%Y')}\nLocation: {location}\n\n"
        if ticket_url: kb.append([InlineKeyboardButton(f"Tickets {title}", url=ticket_url)])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb) if kb else None)

async def cmd_social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; name = uname(update)
    pts = award_points(uid, "follow_social", name)
    kb = [[InlineKeyboardButton(n, url=u)] for n, u in SOFT_GATE]
    await update.message.reply_text(f"BAZRAGOD NETWORK\n\nJoin the Parish 14 movement.\n\n+{pts} MiserCoins", reply_markup=InlineKeyboardMarkup(kb))

async def cmd_donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; name = uname(update)
    url1 = create_checkout(uid, name, "donation", 1, "Support BAZRAGOD $1")
    url5 = create_checkout(uid, name, "donation", 5, "Support BAZRAGOD $5")
    kb = []
    if url1: kb.append([InlineKeyboardButton("Donate $1 via Stripe", url=url1)])
    if url5: kb.append([InlineKeyboardButton("Donate $5 via Stripe", url=url5)])
    kb += [[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]
    await update.message.reply_text("SUPPORT BAZRAGOD\n\nEvery dollar goes directly to the music.\nNo label. No cut. Pure sovereign support.", reply_markup=InlineKeyboardMarkup(kb))

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"PARISH 14 HELP\n\n"
        f"/start        Enter platform\n"
        f"/music        Music catalog\n"
        f"/beats        Beat store\n"
        f"/radio        BazraGod Radio\n"
        f"/cart         Your music cart\n"
        f"/vault        Secret vault\n"
        f"/store        Store and services\n"
        f"/passport     Digital identity and booking card\n"
        f"/coins        MiserCoin balance\n"
        f"/leaderboard  Top fans\n"
        f"/missions     Daily missions\n"
        f"/invite       Referral link\n"
        f"/radar        Fan location map\n"
        f"/skills       Submit your skills\n"
        f"/volunteer    Volunteer missions\n"
        f"/events       Upcoming events\n"
        f"/social       All socials\n"
        f"/donate       Support the mission\n"
        f"/maximus      AI assistant\n"
        f"/stats        Platform stats\n"
        f"/help         This menu\n\n"
        f"Booking: {BOOKING_EMAIL}\n"
        f"Bot: @{BOT_USERNAME}\n\n"
        f"Parish 14 Nation. BAZRAGOD.")

async def action_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    action = q.data.split(":")[1] if ":" in q.data else ""
    if action == "share_location": await location_prompt(update, context)
    elif action == "invite": await cmd_invite(update, context)
    elif action == "leaderboard": await cmd_leaderboard(update, context)
    elif action == "skills": await cmd_skills(update, context)
    elif action == "volunteer": await cmd_volunteer(update, context)
    elif action == "radar": await cmd_radar(update, context)
    elif action == "events": await cmd_events(update, context)
    elif action == "coins": await cmd_coins(update, context)
    elif action == "passport": await cmd_passport(update, context)
    elif action == "missions": await cmd_missions(update, context)

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    uid = update.effective_user.id; name = uname(update)
    if uid in skill_sessions:
        step = skill_sessions[uid].get("step")
        if step == "skill_name":
            skill_sessions[uid]["skill_name"] = text
            skill_sessions[uid]["step"] = "description"
            await update.message.reply_text("Great! Now describe your skill and how you can help Parish 14 Nation.\n\nType your description:"); return
        elif step == "description":
            skill_name = skill_sessions[uid].get("skill_name", "Unknown")
            skill_sessions.pop(uid, None)
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("INSERT INTO skills (telegram_id, username, skill_name, description) VALUES (%s,%s,%s,%s) RETURNING id", (uid, name, skill_name, text))
                sid = cur.fetchone()[0]; conn.commit()
            finally:
                release_db(conn)
            pts = award_points(uid, "submit_skill", name)
            await update.message.reply_text(f"SKILL SUBMITTED\n\nSkill: {skill_name}\nRef: #{sid}\n\nBAZRAGOD will review your contribution.\n\n+{pts} MiserCoins", reply_markup=main_menu)
            try: await telegram_app.bot.send_message(OWNER_ID, f"NEW SKILL SUBMISSION #{sid}\n\nFan: @{name} ({uid})\nSkill: {skill_name}\nDescription: {text}")
            except Exception: pass
            return
    if context.user_data.get("ai_active"):
        if await handle_maximus_chat(uid, text, update, context): return
    if is_admin(uid) and pending_broadcasts.get(OWNER_ID):
        pending_broadcasts.pop(OWNER_ID)
        sent = await _do_broadcast(text)
        await update.message.reply_text(f"Broadcast sent to {sent} fans."); return
    routes = {
        "MUSIC": cmd_music,
        "STORE": cmd_store,
        "COMMUNITY": lambda u, c: u.message.reply_text("COMMUNITY", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Invite Friends", callback_data="action:invite")],
            [InlineKeyboardButton("Leaderboard", callback_data="action:leaderboard")],
            [InlineKeyboardButton("Skills Harvest", callback_data="action:skills")],
            [InlineKeyboardButton("Volunteer", callback_data="action:volunteer")],
            [InlineKeyboardButton("Fan Radar", callback_data="action:radar")],
            [InlineKeyboardButton("Events", callback_data="action:events")],
        ])),
        "FAN ECONOMY": lambda u, c: u.message.reply_text("FAN ECONOMY", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("MiserCoins", callback_data="action:coins")],
            [InlineKeyboardButton("My Passport", callback_data="action:passport")],
            [InlineKeyboardButton("Daily Missions", callback_data="action:missions")],
            [InlineKeyboardButton("Leaderboard", callback_data="action:leaderboard")],
            [InlineKeyboardButton("Invite Friends", callback_data="action:invite")],
        ])),
        "SOCIAL": cmd_social,
        "MAXIMUS AI": cmd_maximus,
        "BazraGod Radio": cmd_radio,
        "My Passport": cmd_passport,
        "Secret Vault": cmd_vault,
        "Help": cmd_help,
        "Back to Menu": lambda u, c: u.message.reply_text("Main Menu", reply_markup=main_menu),
    }
    handler = routes.get(text)
    if handler: await handler(update, context)

async def bg_tasks():
    while True:
        try:
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("UPDATE users SET is_supporter=FALSE WHERE is_supporter=TRUE AND supporter_expires IS NOT NULL AND supporter_expires<CURRENT_DATE")
                conn.commit()
            finally:
                release_db(conn)
        except Exception as e:
            print(f"BG task error: {e}")
        await asyncio.sleep(3600)

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", cmd_start))
telegram_app.add_handler(CommandHandler("menu", lambda u, c: u.message.reply_text("Main Menu", reply_markup=main_menu)))
telegram_app.add_handler(CommandHandler("cancel", cmd_cancel))
telegram_app.add_handler(CommandHandler("help", cmd_help))
telegram_app.add_handler(CommandHandler("language", cmd_language))
telegram_app.add_handler(CommandHandler("music", cmd_music))
telegram_app.add_handler(CommandHandler("beats", cmd_beats))
telegram_app.add_handler(CommandHandler("radio", cmd_radio))
telegram_app.add_handler(CommandHandler("cart", cmd_cart))
telegram_app.add_handler(CommandHandler("vault", cmd_vault))
telegram_app.add_handler(CommandHandler("store", cmd_store))
telegram_app.add_handler(CommandHandler("passport", cmd_passport))
telegram_app.add_handler(CommandHandler("profile", cmd_passport))
telegram_app.add_handler(CommandHandler("coins", cmd_coins))
telegram_app.add_handler(CommandHandler("leaderboard", cmd_leaderboard))
telegram_app.add_handler(CommandHandler("missions", cmd_missions))
telegram_app.add_handler(CommandHandler("invite", cmd_invite))
telegram_app.add_handler(CommandHandler("refer", cmd_invite))
telegram_app.add_handler(CommandHandler("radar", cmd_radar))
telegram_app.add_handler(CommandHandler("skills", cmd_skills))
telegram_app.add_handler(CommandHandler("volunteer", cmd_volunteer))
telegram_app.add_handler(CommandHandler("social", cmd_social))
telegram_app.add_handler(CommandHandler("events", cmd_events))
telegram_app.add_handler(CommandHandler("donate", cmd_donate))
telegram_app.add_handler(CommandHandler("maximus", cmd_maximus))
telegram_app.add_handler(CommandHandler("stats", cmd_stats))
telegram_app.add_handler(CommandHandler("weekly", cmd_weekly))
telegram_app.add_handler(CommandHandler("admin", cmd_admin))
telegram_app.add_handler(CommandHandler("start_radio", cmd_start_radio))
telegram_app.add_handler(CommandHandler("broadcast", cmd_broadcast))
telegram_app.add_handler(CommandHandler("shoutout", cmd_shoutout))
telegram_app.add_handler(CommandHandler("announce", cmd_announce))
telegram_app.add_handler(CommandHandler("premiere", cmd_premiere))
telegram_app.add_handler(CommandHandler("list_songs", cmd_list_songs))
telegram_app.add_handler(CommandHandler("delete_song", cmd_delete_song))
telegram_app.add_handler(CommandHandler("list_vault", cmd_list_vault))
telegram_app.add_handler(CommandHandler("delete_vault", cmd_delete_vault))
telegram_app.add_handler(CommandHandler("vault_unlock", cmd_vault_unlock))
telegram_app.add_handler(CommandHandler("unlock_download", cmd_unlock_download))
telegram_app.add_handler(CommandHandler("activate_supporter", cmd_activate_supporter))
telegram_app.add_handler(CommandHandler("add_event", cmd_add_event))

telegram_app.add_handler(CallbackQueryHandler(lang_cb, pattern="^lang:"))
telegram_app.add_handler(CallbackQueryHandler(entry_step2, pattern="^entry:step2"))
telegram_app.add_handler(CallbackQueryHandler(entry_step3, pattern="^entry:step3"))
telegram_app.add_handler(CallbackQueryHandler(entry_agreed, pattern="^entry:agreed"))
telegram_app.add_handler(CallbackQueryHandler(entry_gate_done, pattern="^entry:gate_done"))
telegram_app.add_handler(CallbackQueryHandler(play_song_cb, pattern="^song:"))
telegram_app.add_handler(CallbackQueryHandler(like_cb, pattern="^like:"))
telegram_app.add_handler(CallbackQueryHandler(beat_cb, pattern="^beat:"))
telegram_app.add_handler(CallbackQueryHandler(buy_beat_cb, pattern="^buy_beat:"))
telegram_app.add_handler(CallbackQueryHandler(buy_song_cb, pattern="^buy_song:"))
telegram_app.add_handler(CallbackQueryHandler(cart_add_cb, pattern="^cart_add:"))
telegram_app.add_handler(CallbackQueryHandler(cart_remove_cb, pattern="^cart_remove:"))
telegram_app.add_handler(CallbackQueryHandler(cart_clear_cb, pattern="^cart_clear"))
telegram_app.add_handler(CallbackQueryHandler(cart_checkout_cb, pattern="^cart_checkout"))
telegram_app.add_handler(CallbackQueryHandler(radio_next_cb, pattern="^radio:next"))
telegram_app.add_handler(CallbackQueryHandler(vault_item_cb, pattern="^vault:"))
telegram_app.add_handler(CallbackQueryHandler(vault_pay_cb, pattern="^vault_pay:"))
telegram_app.add_handler(CallbackQueryHandler(store_cb, pattern="^store:"))
telegram_app.add_handler(CallbackQueryHandler(service_cb, pattern="^service:"))
telegram_app.add_handler(CallbackQueryHandler(merch_cb, pattern="^merch:"))
telegram_app.add_handler(CallbackQueryHandler(leaderboard_cb, pattern="^lb:"))
telegram_app.add_handler(CallbackQueryHandler(mission_complete_cb, pattern="^mission:"))
telegram_app.add_handler(CallbackQueryHandler(volunteer_cb, pattern="^volunteer:"))
telegram_app.add_handler(CallbackQueryHandler(upload_cb, pattern="^upload:"))
telegram_app.add_handler(CallbackQueryHandler(action_cb, pattern="^action:"))

telegram_app.add_handler(MessageHandler(filters.LOCATION, location_handler))
telegram_app.add_handler(MessageHandler(filters.AUDIO, handle_audio))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

loop = asyncio.new_event_loop()

def start_bot():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    if RADIO_CHANNEL_ID:
        loop.create_task(channel_radio_loop(telegram_app.bot))
    loop.create_task(bg_tasks())
    loop.run_forever()

threading.Thread(target=start_bot, daemon=True).start()

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    data = flask_request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    future = asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), loop)
    try:
        future.result(timeout=30)
    except Exception as e:
        print(f"Webhook processing error: {e}")
    return "ok"

@flask_app.route("/stripe_webhook", methods=["POST"])
def stripe_webhook():
    payload = flask_request.data
    sig_header = flask_request.headers.get("Stripe-Signature")
    if not STRIPE_OK:
        return "stripe not available", 400
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return str(e), 400
    if event["type"] == "checkout.session.completed":
        asyncio.run_coroutine_threadsafe(handle_stripe_payment(event["data"]["object"], telegram_app.bot), loop)
    return "ok"

@flask_app.route("/")
def health():
    return f"I.A.A.I.M.O ONLINE v18.000 | PARISH 14 NATION | RADIO {'BROADCASTING' if radio_loop_running else 'STANDBY'}", 200

if __name__ == "__main__":
    init_pool()
    init_db()
    print("=" * 50)
    print("I.A.A.I.M.O MISERBOT v18.000 LEAN")
    print("SOVEREIGN ARTIST PLATFORM")
    print("Bot: @BazragodMiserbot_bot")
    print("Nation: Parish 14")
    print("Status: ONLINE")
    print("=" * 50)
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
