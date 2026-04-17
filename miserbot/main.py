import os
import asyncio
import threading
import time
from datetime import datetime, date, timedelta
from flask import Flask, request as flask_request
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)
from database import init_pool, init_db
from config import (
    BOT_TOKEN, RADIO_CHANNEL_ID, OWNER_ID,
    STRIPE_WEBHOOK_SECRET, SOFT_GATE, SERVICES,
    PARISH_LOUNGE, RADIO_CHANNEL_LINK, BOOKING_TERMS,
    POINT_SHOP, POINTS, STAKE_TIERS, QUOTES, FITNESS_MSG,
    AI_SYSTEM_PROMPT, MERCH_ITEMS, CHARITY_THRESHOLD,
    CASHAPP, PAYPAL, BOOKING_EMAIL, BOT_USERNAME,
    SUPPORTER_PRICE, VAULT_UNLOCK_PRICE, VAULT_SUPERFAN_PRICE,
    DEDICATION_COST, STREAK_BONUSES, STREAK_BADGES,
    AD_MESSAGES, MISSIONS, get_rank, get_station_rank, get_next_rank, t,
    SUPPORTED_LANGUAGES, SONG_PRICE, ALBUM_PRICE, ALBUM_COUNT,
)
from handlers.start import (
    entry_sequence, entry_step2_cb, entry_step3_cb,
    entry_agreed_cb, entry_gate_done_cb,
    language_select, lang_cb, cancel_cmd, menu_cmd, main_menu,
    mark_entry, mark_gate, has_entry, has_gate,
)
from handlers.music import (
    music_catalog, play_song_cb, like_cb,
    cart_add_cb, cart_view, cart_remove_cb, cart_clear_cb,
    cart_checkout_cb, buy_song_cb, download_cb,
    radio_handler, radio_next_cb, _play_next,
)
from handlers.store import (
    store_panel, service_cb, merch_panel, merch_cb,
    vault_cmd, vault_item_cb, vault_pay_cb,
    coin_shop, shop_cb, supporter_cmd, donate_cmd, manual_pay_cb,
)
from handlers.economy import (
    passport_cmd, my_coins, leaderboard_cmd, leaderboard_cb,
    daily_mission_cmd, mission_complete_cb,
    staking_cmd, stake_cb, stake_custom_handler,
    fan_radar_cmd, location_prompt, location_handler,
)
from handlers.referral import refer_cmd
from services.economy import (
    get_user_lang, update_streak, check_supporter_expiry,
    run_daily_drip, process_stake_maturity, award_points,
)
from services.radio import start_channel_radio, build_playlist, save_queue, invalidate_cache
from core.generator import process_stripe_event
from core.metadata import classify_rotation
from core.cart import cart_get, cart_price
from services.vault import get_vault_menu, unlock_vault_item
from services.missions import get_today_mission, complete_mission
from services.passport import get_passport
from services.supporters import is_supporter, activate_supporter
from database import get_db, release_db

try:
    import stripe
    STRIPE_OK = True
except:
    STRIPE_OK = False

flask_app = Flask(__name__)

astro_sessions = {}
mood_sessions = {}
cipher_sessions = {}
submission_sessions = {}
auction_bid_sessions = {}
travel_sessions = {}
pending_broadcasts = {}

async def wisdom_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    pts = award_points(uid, "wisdom", name)
    await update.message.reply_text(f"Royal Wisdom\n\n{random.choice(QUOTES)}\n\n+{pts} MiserCoins")

async def fitness_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    pts = award_points(uid, "fitness", name)
    await update.message.reply_text(f"{FITNESS_MSG}\n\n+{pts} MiserCoins")

async def social_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    pts = award_points(uid, "follow_social", name)
    keyboard = [[InlineKeyboardButton(n, url=u)] for n, u in SOFT_GATE]
    await update.message.reply_text(f"BAZRAGOD NETWORK\n\nJoin the Parish 14 movement.\n\n+{pts} MiserCoins",
        reply_markup=InlineKeyboardMarkup(keyboard))

async def community_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"
    await update.message.reply_text(
        f"PARISH 14 COMMUNITY\n\nEvery fan who joins is a soldier.\nEvery share grows the army.\n\nYour invite link:\n{link}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Parish 14 Lounge", url=PARISH_LOUNGE)],
            [InlineKeyboardButton("BazraGod Radio", url=RADIO_CHANNEL_LINK)],
            [InlineKeyboardButton("Share Invite Link", url=f"https://t.me/share/url?url={link}&text=Join+Parish+14+Nation")],
        ]))

async def events_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT title, description, event_date, location, ticket_url FROM events WHERE status='upcoming' AND event_date>NOW() ORDER BY event_date LIMIT 10")
        event_list = cur.fetchall()
    finally:
        release_db(conn)
    if not event_list:
        await update.message.reply_text("UPCOMING EVENTS\n\nNo events announced yet.\n\nStay tuned. Parish 14 Nation is global.")
        return
    text = "UPCOMING EVENTS\n\n"; keyboard = []
    for title, description, event_date, location, ticket_url in event_list:
        text += f"{title}\n{description}\nDate: {event_date.strftime('%d/%m/%Y')}\nLocation: {location}\n\n"
        if ticket_url:
            keyboard.append([InlineKeyboardButton(f"Tickets {title}", url=ticket_url)])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)

async def tour_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT city, country, venue, show_date, ticket_url FROM tour WHERE status='upcoming' AND show_date>NOW() ORDER BY show_date LIMIT 10")
        shows = cur.fetchall()
    finally:
        release_db(conn)
    if not shows:
        await update.message.reply_text(f"BAZRAGOD TOUR SCHEDULE\n\nNo shows announced yet.\n\nFor booking: {BOOKING_EMAIL}")
        return
    text = "BAZRAGOD TOUR SCHEDULE\n\n"; keyboard = []
    for city, country, venue, show_date, ticket_url in shows:
        text += f"{city}, {country}\n{venue}\n{show_date.strftime('%d %B %Y')}\n\n"
        if ticket_url:
            keyboard.append([InlineKeyboardButton(f"Tickets {city}", url=ticket_url)])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)

async def booking_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(BOOKING_TERMS)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"PARISH 14 HELP\n\n"
        f"PANELS\n"
        f"MUSIC SYSTEM    Music, Radio, Vault\n"
        f"STORE           Buy, Book, Donate\n"
        f"COMMUNITY       Invite, Leaderboard, Skills\n"
        f"FAN ECONOMY     Coins, Passport, Missions\n"
        f"SOCIAL ACCESS   All channels\n\n"
        f"COMMANDS\n"
        f"/start       Enter platform\n"
        f"/music       Music catalog\n"
        f"/radio       BazraGod Radio\n"
        f"/cart        Your music cart\n"
        f"/vault       Secret vault\n"
        f"/coins       MiserCoin balance\n"
        f"/passport    Digital identity\n"
        f"/missions    Daily missions\n"
        f"/leaderboard Top fans\n"
        f"/invite      Referral link\n"
        f"/staking     Coin staking\n"
        f"/events      Upcoming events\n"
        f"/tour        Tour schedule\n"
        f"/booking     Booking terms\n"
        f"/store       Store and services\n"
        f"/supporter   Become a supporter\n"
        f"/donate      Support the mission\n"
        f"/social      All socials\n"
        f"/community   Community links\n"
        f"/profile     Full profile\n"
        f"/stats       Platform stats\n"
        f"/help        This menu\n\n"
        f"Booking: {BOOKING_EMAIL}\n"
        f"Bot: @{BOT_USERNAME}\n\n"
        f"Parish 14 Nation. BAZRAGOD.")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from services.radio import radio_loop_running
    uid = update.effective_user.id
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM users"); total_fans = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM songs"); total_songs = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(plays),0) FROM songs"); total_plays = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fan_locations"); mapped = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM auctions WHERE status='active'"); auctions = cur.fetchone()[0]
        if uid == OWNER_ID:
            cur.execute("SELECT COALESCE(SUM(points),0) FROM users"); total_pts = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE is_supporter=TRUE"); supporters = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM stripe_sessions WHERE status='completed'"); stripe_done = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM artist_submissions WHERE status='pending'"); pending_subs = cur.fetchone()[0]
    finally:
        release_db(conn)
    if uid == OWNER_ID:
        await update.message.reply_text(
            f"MISERBOT STATS v18.000\n\n"
            f"Radio:         {'ACTIVE' if radio_loop_running else 'STANDBY'}\n"
            f"Total Fans:    {total_fans:,}\n"
            f"Supporters:    {supporters}\n"
            f"MiserCoins:    {total_pts:,}\n"
            f"Songs:         {total_songs}\n"
            f"Total Plays:   {total_plays:,}\n"
            f"Fans Mapped:   {mapped}\n"
            f"Live Auctions: {auctions}\n"
            f"Stripe Sales:  {stripe_done}\n"
            f"Pending Subs:  {pending_subs}")
    else:
        await update.message.reply_text(
            f"PLATFORM STATISTICS\n\n"
            f"Total fans:    {total_fans:,}\n"
            f"Songs:         {total_songs}\n"
            f"Total plays:   {total_plays:,}\n"
            f"Fans mapped:   {mapped}\n"
            f"Live auctions: {auctions}\n\n"
            f"Parish 14 Nation. BAZRAGOD.")

async def voice_wall_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["voice_wall_active"] = True
    await update.message.reply_text("FAN VOICE WALL\n\nRecord a voice message and send it here.\n\nApproved shoutouts play LIVE on BazraGod Radio.\n\nRecord and send now.\n\nType /cancel to go back.")

async def voice_wall_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    if not context.user_data.get("voice_wall_active"):
        return
    context.user_data.pop("voice_wall_active", None)
    voice = update.message.voice
    if not voice:
        return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO voice_wall (telegram_id, username, file_id) VALUES (%s,%s,%s) RETURNING id", (uid, name, voice.file_id))
        sid = cur.fetchone()[0]; conn.commit()
    finally:
        release_db(conn)
    pts = award_points(uid, "voice_wall", name)
    await update.message.reply_text(f"Submission #{sid} received.\nApproved voices play on BazraGod Radio.\n\n+{pts} MiserCoins", reply_markup=main_menu)
    try:
        await context.bot.send_message(OWNER_ID, f"VOICE #{sid}\nFan: @{name} ({uid})\n/approve_voice {sid}")
        await context.bot.forward_message(chat_id=OWNER_ID, from_chat_id=uid, message_id=update.message.message_id)
    except:
        pass

async def submit_track_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    submission_sessions[uid] = True
    await update.message.reply_text(
        f"SUBMIT YOUR TRACK\n\nSend your audio file with caption:\nArtistName - SongTitle\n\nBAZRAGOD reviews every submission personally.\nApproved tracks go live on BazraGod Radio.\n\nReward: +{POINTS['submit_track']} MiserCoins\n\nType /cancel to go back.")

async def handle_audio_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import re
    uid = update.effective_user.id
    audio = update.message.audio
    if not audio:
        return
    if uid != OWNER_ID:
        if submission_sessions.get(uid):
            submission_sessions.pop(uid, None)
            name = update.effective_user.username or str(uid)
            caption = (update.message.caption or "").strip()
            parts = caption.split("-", 1)
            artist_name = parts[0].strip() if parts else name
            song_title = parts[1].strip() if len(parts) > 1 else (audio.title or "Untitled")
            file_id = audio.file_id
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("INSERT INTO artist_submissions (telegram_id, username, artist_name, song_title, file_id) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                    (uid, name, artist_name, song_title, file_id))
                sub_id = cur.fetchone()[0]; conn.commit()
            finally:
                release_db(conn)
            pts = award_points(uid, "submit_track", name)
            await update.message.reply_text(f"SUBMISSION RECEIVED\n\nArtist: {artist_name}\nTrack: {song_title}\nRef: {sub_id}\n\n+{pts} MiserCoins", reply_markup=main_menu)
            try:
                await context.bot.send_message(OWNER_ID, f"ARTIST SUBMISSION #{sub_id}\n\nArtist: {artist_name}\nTrack: {song_title}\nFan: @{name} ({uid})\n\n/approve_submission {sub_id}")
                await context.bot.forward_message(chat_id=OWNER_ID, from_chat_id=uid, message_id=update.message.message_id)
            except:
                pass
        return
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
        if match:
            req_pts = int(match.group(1))
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO vault_songs (title, file_id, required_points) VALUES (%s,%s,%s) RETURNING id", (title, file_id, req_pts))
            new_id = cur.fetchone()[0]; conn.commit()
        finally:
            release_db(conn)
        await update.message.reply_text(f"Vault song added. ID: {new_id}\nTitle: {title}\nRequired: {req_pts:,} coins")
        return
    for tag, (dest, label) in tag_map.items():
        if tag in caption:
            conn = get_db(); cur = conn.cursor()
            try:
                if dest == "songs":
                    cur.execute("SELECT id FROM songs WHERE LOWER(title)=LOWER(%s)", (title,))
                    if cur.fetchone():
                        await update.message.reply_text(f"Song '{title}' already exists."); return
                    cur.execute("INSERT INTO songs (title, file_id) VALUES (%s,%s) RETURNING id", (title, file_id))
                else:
                    cur.execute(f"INSERT INTO {dest} (title, file_id) VALUES (%s,%s) RETURNING id", (title, file_id))
                new_id = cur.fetchone()[0]; conn.commit()
            finally:
                release_db(conn)
            await update.message.reply_text(f"{label} added. ID: {new_id}\nTitle: {title}")
            invalidate_cache()
            pl = build_playlist(); save_queue(pl)
            return
    await update.message.reply_text(
        f"CLASSIFY UPLOAD\n\nTitle: {title}\n\nWhat type is this audio?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Song", callback_data=f"upload:songs:{file_id}:{title}")],
            [InlineKeyboardButton("Beat", callback_data=f"upload:beats:{file_id}:{title}")],
            [InlineKeyboardButton("Drop", callback_data=f"upload:drops:{file_id}:{title}")],
            [InlineKeyboardButton("Announcement", callback_data=f"upload:announcements:{file_id}:{title}")],
            [InlineKeyboardButton("Vault 1000 coins", callback_data=f"upload:vault:1000:{file_id}:{title}")],
        ]))

async def upload_classify_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if query.from_user.id != OWNER_ID:
        return
    parts = query.data.split(":")
    dest = parts[1]
    if dest == "vault":
        req_pts = int(parts[2]); file_id = parts[3]; title = ":".join(parts[4:])
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO vault_songs (title, file_id, required_points) VALUES (%s,%s,%s) RETURNING id", (title, file_id, req_pts))
            new_id = cur.fetchone()[0]; conn.commit()
        finally:
            release_db(conn)
        await query.message.reply_text(f"Vault song added. ID: {new_id}")
        return
    file_id = parts[2]; title = ":".join(parts[3:])
    conn = get_db(); cur = conn.cursor()
    try:
        if dest == "songs":
            cur.execute("INSERT INTO songs (title, file_id) VALUES (%s,%s) ON CONFLICT (title) DO NOTHING RETURNING id", (title, file_id))
        else:
            cur.execute(f"INSERT INTO {dest} (title, file_id) VALUES (%s,%s) RETURNING id", (title, file_id))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    if row:
        await query.message.reply_text(f"Added. ID: {row[0]}\nTitle: {title}")
        invalidate_cache()
        pl = build_playlist(); save_queue(pl)
async def maximus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.environ.get("OPENAI_API_KEY"):
        await update.message.reply_text("MAXIMUS is offline. OPENAI_API_KEY not set.")
        return
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    context.user_data["ai_active"] = True
    context.user_data["ai_history"] = context.user_data.get("ai_history", [])
    pts = award_points(uid, "ai_chat", name)
    await update.message.reply_text(
        f"MAXIMUS ONLINE\n\nRoyal AI of BAZRAGOD.\nManager. Publicist. Strategist.\n\nAsk me anything.\nType /menu to return.\n\n+{pts} MiserCoins")

async def ai_chat_handler_fn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("ai_active"):
        return False
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    user_msg = update.message.text
    history = context.user_data.get("ai_history", [])
    history.append({"role": "user", "content": user_msg})
    if len(history) > 10:
        history = history[-10:]
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": AI_SYSTEM_PROMPT}, *history],
            max_tokens=400)
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        context.user_data["ai_history"] = history
        award_points(uid, "ai_chat", name)
        await update.message.reply_text(f"MAXIMUS\n\n{reply}")
        try:
            from io import BytesIO
            resp = client.audio.speech.create(model="tts-1", voice="onyx", input=reply[:500], speed=0.95)
            buf = BytesIO(resp.content); buf.name = "maximus.ogg"
            await context.bot.send_voice(chat_id=uid, voice=buf)
        except:
            pass
    except Exception as e:
        await update.message.reply_text(f"MAXIMUS error: {str(e)}")
    return True

async def auction_house_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points FROM users WHERE telegram_id=%s", (uid,))
        fan = cur.fetchone(); pts = fan[0] if fan else 0
        cur.execute("SELECT id, title, description, current_bid, top_username, ends_at FROM auctions WHERE status='active' AND ends_at>NOW() ORDER BY ends_at")
        auctions = cur.fetchall()
    finally:
        release_db(conn)
    if not auctions:
        await update.message.reply_text(
            f"AUCTION HOUSE\n\nYour balance: {pts:,} MiserCoins\n\nNo active auctions right now.\n\nBAZRAGOD drops auctions for exclusive songs, NFTs, feature slots, and video calls.\n\nStay tuned.")
        return
    text = f"AUCTION HOUSE\n\nYour balance: {pts:,} MiserCoins\n\nActive auctions:\n\n"
    keyboard = []
    for aid, title, desc, current_bid, top_user, ends_at in auctions:
        time_left = ends_at - datetime.now()
        hours_left = int(time_left.total_seconds() // 3600)
        mins_left = int((time_left.total_seconds() % 3600) // 60)
        text += f"{title}\nCurrent bid: {current_bid:,} coins\nTop bidder: {top_user or 'None yet'}\nEnds in: {hours_left}h {mins_left}m\n\n"
        keyboard.append([InlineKeyboardButton(f"Bid on {title}", callback_data=f"auction_bid:{aid}")])
    keyboard.append([InlineKeyboardButton("My Bids", callback_data="auction_mybids")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def auction_bid_cb_fn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    if query.data == "auction_mybids":
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("SELECT a.title, ab.amount, a.current_bid, a.top_bidder, a.ends_at FROM auction_bids ab JOIN auctions a ON ab.auction_id=a.id WHERE ab.telegram_id=%s ORDER BY ab.bid_at DESC LIMIT 10", (uid,))
            bids = cur.fetchall()
        finally:
            release_db(conn)
        if not bids:
            await query.message.reply_text("You have not placed any bids yet.")
            return
        text = "MY BIDS\n\n"
        for title, amount, current_bid, top_bidder, ends_at in bids:
            status = "WINNING" if top_bidder == uid else "OUTBID"
            text += f"{title}\nYour bid: {amount:,} coins\nStatus: {status}\nEnds: {ends_at.strftime('%d/%m %H:%M')}\n\n"
        await query.message.reply_text(text)
        return
    try:
        auction_id = int(query.data.split(":")[1])
    except:
        return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, current_bid, starting_bid, ends_at FROM auctions WHERE id=%s AND status='active'", (auction_id,))
        auction = cur.fetchone()
        cur.execute("SELECT points FROM users WHERE telegram_id=%s", (uid,))
        fan = cur.fetchone(); fan_pts = fan[0] if fan else 0
    finally:
        release_db(conn)
    if not auction:
        await query.answer("Auction has ended.", show_alert=True); return
    aid, title, current_bid, starting_bid, ends_at = auction
    min_bid = max(starting_bid, current_bid + 10)
    if fan_pts < min_bid:
        await query.answer(f"Need {min_bid:,} coins. You have {fan_pts:,}.", show_alert=True); return
    auction_bid_sessions[uid] = {"auction_id": aid, "title": title, "min_bid": min_bid}
    await query.message.reply_text(
        f"PLACE YOUR BID\n\nItem: {title}\nCurrent bid: {current_bid:,} coins\nMinimum bid: {min_bid:,} coins\nYour balance: {fan_pts:,} coins\n\nType your bid amount.")

async def auction_bid_text_handler(uid, text, update, context):
    if uid not in auction_bid_sessions:
        return False
    session = auction_bid_sessions.pop(uid)
    name = update.effective_user.username or str(uid)
    try:
        bid_amount = int("".join(filter(str.isdigit, text)))
    except:
        await update.message.reply_text("Invalid amount. Numbers only.")
        auction_bid_sessions[uid] = session; return True
    if bid_amount < session["min_bid"]:
        await update.message.reply_text(f"Bid too low. Minimum is {session['min_bid']:,} coins.")
        return True
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points FROM users WHERE telegram_id=%s", (uid,))
        fan = cur.fetchone()
        if not fan or fan[0] < bid_amount:
            await update.message.reply_text(f"Not enough coins. You have {fan[0] if fan else 0:,} coins.")
            return True
        cur.execute("SELECT id, current_bid, top_bidder FROM auctions WHERE id=%s AND status='active' AND ends_at>NOW()", (session["auction_id"],))
        auction = cur.fetchone()
        if not auction:
            await update.message.reply_text("This auction has ended.")
            return True
        old_top = auction[2]
        cur.execute("UPDATE auctions SET current_bid=%s, top_bidder=%s, top_username=%s WHERE id=%s",
            (bid_amount, uid, name, session["auction_id"]))
        cur.execute("INSERT INTO auction_bids (auction_id, telegram_id, username, amount) VALUES (%s,%s,%s,%s)",
            (session["auction_id"], uid, name, bid_amount))
        conn.commit()
    finally:
        release_db(conn)
    await update.message.reply_text(
        f"BID PLACED\n\nItem: {session['title']}\nYour bid: {bid_amount:,} coins\n\nYou are the top bidder.",
        reply_markup=main_menu)
    if old_top and old_top != uid:
        try:
            await context.bot.send_message(old_top,
                f"YOU HAVE BEEN OUTBID\n\nItem: {session['title']}\nNew top bid: {bid_amount:,} coins\n\nGo to Auction House to bid again.")
        except:
            pass
    return True

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    from services.radio import radio_loop_running
    await update.message.reply_text(
        f"ADMIN PANEL v18.000\n\n"
        f"Radio: {'ACTIVE' if radio_loop_running else 'STANDBY'}\n\n"
        f"RADIO\n/start_radio\n/premiere song_id\n\n"
        f"CONTENT\n/list_songs  /delete_song id\n/list_vault  /delete_vault id\n/vault_unlock uid single|bundle\n\n"
        f"ECONOMY\n/create_auction title desc bid hours\n/activate_supporter uid\n/unlock_download uid song_id\n\n"
        f"EVENTS\n/add_event title desc date location\n\n"
        f"SUBMISSIONS\n/list_submissions\n/approve_submission id\n/reject_submission id\n\n"
        f"VOICES\n/approve_voice id\n\n"
        f"BROADCAST\n/broadcast  /shoutout @username  /announce message\n\n"
        f"UPLOAD\nSend audio with caption tag:\n#song #beat #drop #announce #vault 1000")

async def start_radio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    from services.radio import radio_loop_running
    if not RADIO_CHANNEL_ID:
        await update.message.reply_text("RADIO_CHANNEL_ID not set in Railway.")
        return
    if radio_loop_running:
        await update.message.reply_text("Radio loop already running.")
        return
    asyncio.run_coroutine_threadsafe(start_channel_radio(telegram_app.bot), loop)
    await update.message.reply_text(f"Channel radio STARTED.\nBroadcasting to: {RADIO_CHANNEL_ID}\nParish 14 Nation.")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    pending_broadcasts[OWNER_ID] = True
    await update.message.reply_text("BROADCAST MODE\n\nSend your message now.\n/cancel to abort.")

async def shoutout_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /shoutout @username")
        return
    msg = f"SHOUTOUT FROM BAZRAGOD\n\nBig up {args[0]} real Parish 14 energy.\n\nI.A.A.I.M.O"
    sent = await _broadcast(context, msg)
    await update.message.reply_text(f"Shoutout sent to {sent} fans.")

async def announce_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /announce <message>")
        return
    msg = f"OFFICIAL ANNOUNCEMENT\n\n{text}\n\nBAZRAGOD"
    sent = await _broadcast(context, msg)
    await update.message.reply_text(f"Sent to {sent} fans.")

async def _broadcast(context, text):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT telegram_id FROM users")
        fans = cur.fetchall()
    finally:
        release_db(conn)
    sent = 0
    for (fid,) in fans:
        try:
            await context.bot.send_message(fid, text)
            sent += 1
        except:
            pass
    return sent

async def premiere_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /premiere <song_id>")
        return
    song_id = int(args[0])
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE songs SET rotation='A' WHERE id=%s RETURNING title", (song_id,))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    if not row:
        await update.message.reply_text("Song not found.")
        return
    invalidate_cache()
    pl = build_playlist(); save_queue(pl)
    msg = f"WORLD PREMIERE\n\n'{row[0]}' dropping now.\n\nBAZRAGOD drops it here first.\nNo label. No middleman. Parish 14 Nation."
    sent = await _broadcast(context, msg)
    await update.message.reply_text(f"Premiere sent to {sent} fans.")

async def vault_unlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /vault_unlock <uid> <single|bundle>")
        return
    fan_id = int(args[0]); pay_type = args[1]
    from services.vault import unlock_all_vault
    if pay_type == "bundle":
        unlock_all_vault(fan_id, "admin")
    await update.message.reply_text(f"Vault unlocked for {fan_id}. Type: {pay_type}")
    try:
        msg = f"VAULT ACCESS GRANTED\n\nAll vault songs are yours.\nContact {BOOKING_EMAIL} with your address for merch.\n\nParish 14." if pay_type == "bundle" else "VAULT ACCESS GRANTED\n\nGo to Secret Vault to choose your song.\n\nParish 14."
        await context.bot.send_message(fan_id, msg)
    except:
        pass

async def unlock_download_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /unlock_download <uid> <song_id>")
        return
    fan_id = int(args[0]); song_id = int(args[1])
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO downloads (telegram_id, song_id, purchased) VALUES (%s,%s,TRUE) ON CONFLICT DO NOTHING", (fan_id, song_id))
        cur.execute("SELECT title, file_id FROM songs WHERE id=%s", (song_id,))
        song = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    if song:
        await update.message.reply_text(f"Download unlocked for {fan_id}: {song[0]}")
        try:
            await context.bot.send_audio(fan_id, song[1], caption=f"DOWNLOAD UNLOCKED\n\n{song[0]}\nBAZRAGOD\n\nYours to keep. Parish 14 Nation.")
        except:
            pass

async def activate_supporter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /activate_supporter <telegram_id>")
        return
    fan_id = int(args[0])
    username, expires = activate_supporter(fan_id)
    if username:
        award_points(fan_id, "supporter_sub")
        await update.message.reply_text(f"@{username} activated. Expires: {expires}")
        try:
            await context.bot.send_message(fan_id,
                f"PARISH 14 SUPPORTER ACTIVATED\n\nNation Elite unlocked.\nExpires: {expires.strftime('%B %d, %Y')}\n\nBAZRAGOD sees you.")
        except:
            pass
    else:
        await update.message.reply_text("Fan not found.")

async def list_songs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    from core.metadata import heat_score
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, plays, likes, donations, rotation FROM songs ORDER BY id")
        rows = cur.fetchall()
    finally:
        release_db(conn)
    rb = {"A": "Hot", "B": "Mid", "C": "Deep"}
    text = f"SONGS  {len(rows)}\n\n"
    for r in rows:
        text += f"[{r[0]}] {rb.get(r[5],'')} {r[1]}\n{heat_score(r[3],r[4],r[2])} {r[2]:,} plays\n"
    await update.message.reply_text(text or "Empty.")

async def delete_song_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /delete_song <id>")
        return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM songs WHERE id=%s RETURNING title", (int(args[0]),))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    invalidate_cache()
    pl = build_playlist(); save_queue(pl)
    await update.message.reply_text(f"Deleted: {row[0]}" if row else "Not found.")

async def approve_submission_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /approve_submission <id>")
        return
    sub_id = int(args[0])
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE artist_submissions SET status='approved' WHERE id=%s RETURNING telegram_id, artist_name, song_title, file_id", (sub_id,))
        row = cur.fetchone()
        if row:
            tid, artist, song, file_id = row
            cur.execute("INSERT INTO songs (title, file_id) VALUES (%s,%s) ON CONFLICT (title) DO NOTHING", (f"{artist} {song}", file_id))
            conn.commit()
            invalidate_cache()
            pl = build_playlist(); save_queue(pl)
        else:
            conn.commit()
    finally:
        release_db(conn)
    if row:
        await update.message.reply_text(f"Submission #{sub_id} approved. Added to radio.")
        try:
            await context.bot.send_message(row[0],
                f"YOUR TRACK WAS APPROVED\n\n{row[1]} {row[2]}\n\nNow live on BazraGod Radio.\n\nParish 14 Nation. BAZRAGOD.")
        except:
            pass
    else:
        await update.message.reply_text("Submission not found.")

async def approve_voice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /approve_voice <id>")
        return
    conn​​​​​​​​​​​​​​​​
async def panel_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    try:
        panel = query.data.split(":")[1]
    except:
        return

    if panel == "music":
        await query.message.reply_text("MUSIC SYSTEM", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Music Library", callback_data="panel:music_library")],
            [InlineKeyboardButton("Playlist Radio", callback_data="radio:next")],
            [InlineKeyboardButton("Secret Vault", callback_data="panel:vault_menu")],
            [InlineKeyboardButton("Super Fan Album", callback_data="vault_pay:bundle")],
            [InlineKeyboardButton("Listening Room", callback_data="panel:listening_room")],
        ]))
    elif panel == "store_main":
        await store_panel(update, context)
    elif panel == "community":
        await query.message.reply_text("COMMUNITY SYSTEM", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Invite Friends", callback_data="panel:invite")],
            [InlineKeyboardButton("Leaderboard", callback_data="panel:leaderboard")],
            [InlineKeyboardButton("Submit Track", callback_data="panel:submit")],
            [InlineKeyboardButton("Voice Wall", callback_data="panel:voice_wall")],
            [InlineKeyboardButton("Artist Spotlight", callback_data="panel:spotlight")],
        ]))
    elif panel == "economy":
        await query.message.reply_text("FAN ECONOMY", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("MiserCoins", callback_data="panel:coins")],
            [InlineKeyboardButton("My Passport", callback_data="panel:passport")],
            [InlineKeyboardButton("Daily Missions", callback_data="panel:missions")],
            [InlineKeyboardButton("My Streak", callback_data="panel:streak")],
            [InlineKeyboardButton("Coin Staking", callback_data="panel:staking")],
            [InlineKeyboardButton("Coin Shop", callback_data="panel:coin_shop")],
        ]))
    elif panel == "social":
        keyboard = [[InlineKeyboardButton(n, url=u)] for n, u in SOFT_GATE]
        keyboard.append([InlineKeyboardButton("Ladies Hub", callback_data="panel:ladies_hub")])
        keyboard.append([InlineKeyboardButton("Events", callback_data="panel:events")])
        keyboard.append([InlineKeyboardButton("About Miserbot", callback_data="panel:about")])
        await query.message.reply_text("SOCIAL ACCESS\n\nAll Parish 14 channels.", reply_markup=InlineKeyboardMarkup(keyboard))
    elif panel == "music_library":
        await music_catalog(update, context)
    elif panel == "vault_menu":
        await vault_cmd(update, context)
    elif panel == "listening_room":
        from services.radio import get_listener_count
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("SELECT title, played_at FROM radio_history ORDER BY played_at DESC LIMIT 5")
            recent = cur.fetchall()
        finally:
            release_db(conn)
        now = datetime.now().strftime("%I:%M %p")
        recently_played = "\n".join([f"  {r[0]}" for r in recent]) if recent else "  Tune in to build history"
        await query.message.reply_text(
            f"LISTENING ROOM\n\nTime: {now}\nListeners: {get_listener_count()} tuned in\n\nRECENTLY PLAYED:\n{recently_played}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Tune In Now", callback_data="radio:next")],
                [InlineKeyboardButton("Radio Channel", url=RADIO_CHANNEL_LINK)],
            ]))
    elif panel == "invite":
        await refer_cmd(update, context)
    elif panel == "leaderboard":
        await leaderboard_cmd(update, context)
    elif panel == "submit":
        await submit_track_cmd(update, context)
    elif panel == "voice_wall":
        await voice_wall_prompt(update, context)
    elif panel == "spotlight":
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("SELECT artist_name, song_title FROM artist_submissions WHERE status='approved' ORDER BY RANDOM() LIMIT 5")
            approved = cur.fetchall()
            cur.execute("SELECT COUNT(*) FROM artist_submissions WHERE status='approved'")
            total = cur.fetchone()[0]
        finally:
            release_db(conn)
        if not approved:
            await query.message.reply_text("ARTIST SPOTLIGHT\n\nNo featured artists yet.\n\nSubmit your music for review.")
            return
        text = f"ARTIST SPOTLIGHT\n\nParish 14 Network\n{total} approved artists\n\n"
        for artist_name, song_title in approved:
            text += f"Artist: {artist_name}\nTrack: {song_title}\n\n"
        await query.message.reply_text(text)
    elif panel == "coins":
        await my_coins(update, context)
    elif panel == "passport":
        await passport_cmd(update, context)
    elif panel == "missions":
        await daily_mission_cmd(update, context)
    elif panel == "streak":
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("SELECT streak_days, last_streak_date FROM radio_state WHERE id=1")
            state = cur.fetchone()
        finally:
            release_db(conn)
        streak = 0
        if state:
            sd, ld = state
            if ld and ld >= date.today() - timedelta(days=1):
                streak = sd or 0
        streak_badge = ""
        for days, badge in sorted(STREAK_BADGES.items(), reverse=True):
            if streak >= days:
                streak_badge = badge; break
        bonuses = "\n".join([f"{d} days = +{b} coins" for d, b in STREAK_BONUSES.items()])
        await query.message.reply_text(
            f"LISTENER STREAK\n\nCurrent streak: {streak} days\nBadge: {streak_badge or 'Keep going!'}\n\nSTREAK BONUSES\n{bonuses}\n\nListen daily to build your streak. Parish 14.")
    elif panel == "staking":
        await staking_cmd(update, context)
    elif panel == "coin_shop":
        await coin_shop(update, context)
    elif panel == "ladies_hub":
        await query.message.reply_text(
            "LADIES HUB\n\nExclusive female fan community for Parish 14 Nation.\n\nExperiences designed for the Queens of the movement.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Fan Photo Pass ${SERVICES['fan_photo'][1]}", callback_data="service:fan_photo")],
                [InlineKeyboardButton(f"Backstage Pass ${SERVICES['backstage_pass'][1]}", callback_data="service:backstage_pass")],
                [InlineKeyboardButton("Parish 14 Lounge", url=PARISH_LOUNGE)],
            ]))
    elif panel == "events":
        await events_cmd(update, context)
    elif panel == "about":
        await query.message.reply_text(
            f"ABOUT MISERBOT\n\nI.A.A.I.M.O\nIndependent Artists Artificial Intelligence Music Ops\n\nMiserbot is the sovereign digital music nation of BAZRAGOD.\n\nNo labels. No middlemen. Direct connection between artist and fans.\n\nPlatform: Telegram Super App\nRadio: 24/7 BazraGod Radio\nNation: Parish 14\nBrain: MAXIMUS AI\n\nContact: {BOOKING_EMAIL}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Parish 14 Lounge", url=PARISH_LOUNGE)],
                [InlineKeyboardButton("BazraGod Radio", url=RADIO_CHANNEL_LINK)],
            ]))
    elif panel == "merch":
        await merch_panel(update, context)
    elif panel == "club_booking":
        await query.message.reply_text("CLUB BOOKING\n\nBook BAZRAGOD for your event.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Small Club ${SERVICES['small_club'][1]:,}", callback_data="service:small_club")],
                [InlineKeyboardButton(f"Medium Club ${SERVICES['medium_club'][1]:,}", callback_data="service:medium_club")],
                [InlineKeyboardButton(f"Large Venue ${SERVICES['large_venue'][1]:,}", callback_data="service:large_venue")],
                [InlineKeyboardButton("Full Booking Terms", callback_data="action:booking_terms")],
            ]))

async def action_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    try:
        action = query.data.split(":")[1]
    except:
        return
    if action == "booking_terms":
        await query.message.reply_text(BOOKING_TERMS)
    elif action == "cart":
        await cart_view(update, context)

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random
    text = update.message.text or ""
    uid = update.effective_user.id

    if uid in auction_bid_sessions:
        if await auction_bid_text_handler(uid, text, update, context):
            return
    if context.user_data.get("staking_custom"):
        from handlers.economy import stake_custom_handler
        if await stake_custom_handler(uid, text, update, context):
            return
    if context.user_data.get("shop_dedication"):
        context.user_data.pop("shop_dedication", None)
        name = update.effective_user.username or str(uid)
        cost = POINT_SHOP["dedication"][1]
        from services.economy import deduct_points
        if deduct_points(uid, cost, "shop_dedication"):
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("INSERT INTO dedications (telegram_id, username, message) VALUES (%s,%s,%s) RETURNING id",
                    (uid, name, text))
                ded_id = cur.fetchone()[0]; conn.commit()
            finally:
                release_db(conn)
            await update.message.reply_text(
                f"DEDICATION QUEUED\n\nRef #{ded_id}\n\nMAXIMUS will announce your dedication on BazraGod Radio.\n\nParish 14 Nation.",
                reply_markup=main_menu)
        else:
            await update.message.reply_text("Not enough coins.")
        return
    if context.user_data.get("ai_active"):
        if await ai_chat_handler_fn(update, context):
            return
    if uid == OWNER_ID and pending_broadcasts.get(OWNER_ID):
        pending_broadcasts.pop(OWNER_ID)
        sent = await _broadcast(context, text)
        await update.message.reply_text(f"Broadcast sent to {sent} fans.")
        return

    routes = {
        "MUSIC SYSTEM": lambda u, c: _fake_panel(u, c, "music"),
        "STORE": store_panel,
        "COMMUNITY": lambda u, c: _fake_panel(u, c, "community"),
        "FAN ECONOMY": lambda u, c: _fake_panel(u, c, "economy"),
        "SOCIAL ACCESS": lambda u, c: _fake_panel(u, c, "social"),
        "MAXIMUS AI": maximus_cmd,
        "BazraGod Radio": radio_handler,
        "My Passport": passport_cmd,
        "BAZRAGOD MUSIC": music_catalog,
        "Secret Vault": vault_cmd,
        "Auction House": auction_house_cmd,
        "Help": help_cmd,
        "Back to Menu": menu_cmd,
    }
    handler = routes.get(text)
    if handler:
        await handler(update, context)

async def _fake_panel(update, context, panel_name):
    class FakeQuery:
        def __init__(self):
            self.from_user = update.effective_user
            self.message = update.message
            self.data = f"panel:{panel_name}"
        async def answer(self, *args, **kwargs):
            pass
    update.callback_query = FakeQuery()
    await panel_cb(update, context)

async def close_auctions_task():
    while True:
        try:
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("SELECT id, title, top_bidder, top_username, current_bid FROM auctions WHERE status='active' AND ends_at<NOW()")
                for aid, title, winner_id, winner_name, final_bid in cur.fetchall():
                    cur.execute("UPDATE auctions SET status='ended' WHERE id=%s", (aid,))
                    conn.commit()
                    if winner_id:
                        try:
                            await telegram_app.bot.send_message(winner_id,
                                f"YOU WON THE AUCTION\n\n{title}\nFinal bid: {final_bid:,} MiserCoins\n\nBAZRAGOD will deliver your item. Parish 14.")
                        except:
                            pass
                        try:
                            await telegram_app.bot.send_message(OWNER_ID,
                                f"AUCTION ENDED\n\n{title}\nWinner: @{winner_name} ({winner_id})\nFinal bid: {final_bid:,} coins")
                        except:
                            pass
            finally:
                release_db(conn)
        except Exception as e:
            print(f"Auction close error: {e}")
        await asyncio.sleep(60)

async def background_tasks():
    while True:
        try:
            check_supporter_expiry()
            await process_stake_maturity(telegram_app.bot)
            now = datetime.now()
            if now.hour == 9 and now.minute < 5:
                await run_daily_drip(telegram_app.bot)
        except Exception as e:
            print(f"Background task error: {e}")
        await asyncio.sleep(300)

async def send_weekly_intel():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM users"); total_fans = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE joined_at>NOW()-INTERVAL '7 days'"); new_fans = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(points),0) FROM users"); total_pts = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fan_locations"); mapped = cur.fetchone()[0]
        cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 3"); top_fans = cur.fetchall()
        cur.execute("SELECT title, plays FROM songs ORDER BY plays DESC LIMIT 3"); top_songs = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM stripe_sessions WHERE status='completed'"); stripe_done = cur.fetchone()[0]
    finally:
        release_db(conn)
    fans_text = "\n".join([f"  @{f}  {p:,} coins" for f, p in top_fans if f]) or "  None yet"
    songs_text = "\n".join([f"  {t_}  {p_:,} plays" for t_, p_ in top_songs]) or "  None"
    report = (
        f"WEEKLY INTEL REPORT\n"
        f"Week: {datetime.now().strftime('%d %B %Y')}\n\n"
        f"Total Fans:    {total_fans:,}\n"
        f"New This Week: {new_fans}\n"
        f"Total Coins:   {total_pts:,}\n"
        f"Fans Mapped:   {mapped}\n"
        f"Stripe Sales:  {stripe_done}\n\n"
        f"TOP FANS\n{fans_text}\n\n"
        f"TOP SONGS\n{songs_text}\n\n"
        f"MAXIMUS INTEL v18.000"
    )
    try:
        await telegram_app.bot.send_message(OWNER_ID, report)
    except Exception as e:
        print(f"Weekly intel error: {e}")

def weekly_intel_thread():
    last_sent = None
    while True:
        try:
            now = datetime.now()
            week_key = now.strftime("%Y-%W")
            if now.weekday() == 6 and now.hour == 9 and last_sent != week_key:
                asyncio.run_coroutine_threadsafe(send_weekly_intel(), loop)
                last_sent = week_key
        except Exception as e:
            print(f"Weekly thread error: {e}")
        time.sleep(60)

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", entry_sequence))
telegram_app.add_handler(CommandHandler("menu", menu_cmd))
telegram_app.add_handler(CommandHandler("cancel", cancel_cmd))
telegram_app.add_handler(CommandHandler("help", help_cmd))
telegram_app.add_handler(CommandHandler("language", language_select))
telegram_app.add_handler(CommandHandler("radio", radio_handler))
telegram_app.add_handler(CommandHandler("music", music_catalog))
telegram_app.add_handler(CommandHandler("cart", cart_view))
telegram_app.add_handler(CommandHandler("vault", vault_cmd))
telegram_app.add_handler(CommandHandler("coins", my_coins))
telegram_app.add_handler(CommandHandler("passport", passport_cmd))
telegram_app.add_handler(CommandHandler("profile", passport_cmd))
telegram_app.add_handler(CommandHandler("missions", daily_mission_cmd))
telegram_app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
telegram_app.add_handler(CommandHandler("invite", refer_cmd))
telegram_app.add_handler(CommandHandler("refer", refer_cmd))
telegram_app.add_handler(CommandHandler("staking", staking_cmd))
telegram_app.add_handler(CommandHandler("store", store_panel))
telegram_app.add_handler(CommandHandler("supporter", supporter_cmd))
telegram_app.add_handler(CommandHandler("donate", donate_cmd))
telegram_app.add_handler(CommandHandler("social", social_cmd))
telegram_app.add_handler(CommandHandler("community", community_cmd))
telegram_app.add_handler(CommandHandler("events", events_cmd))
telegram_app.add_handler(CommandHandler("tour", tour_cmd))
telegram_app.add_handler(CommandHandler("booking", booking_cmd))
telegram_app.add_handler(CommandHandler("submit", submit_track_cmd))
telegram_app.add_handler(CommandHandler("radar", fan_radar_cmd))
telegram_app.add_handler(CommandHandler("stats", stats_cmd))
telegram_app.add_handler(CommandHandler("wisdom", wisdom_cmd))
telegram_app.add_handler(CommandHandler("fitness", fitness_cmd))
telegram_app.add_handler(CommandHandler("maximus", maximus_cmd))
telegram_app.add_handler(CommandHandler("auctions", auction_house_cmd))
telegram_app.add_handler(CommandHandler("admin", admin_cmd))
telegram_app.add_handler(CommandHandler("start_radio", start_radio_cmd))
telegram_app.add_handler(CommandHandler("broadcast", broadcast_cmd))
telegram_app.add_handler(CommandHandler("shoutout", shoutout_cmd))
telegram_app.add_handler(CommandHandler("announce", announce_cmd))
telegram_app.add_handler(CommandHandler("premiere", premiere_cmd))
telegram_app.add_handler(CommandHandler("vault_unlock", vault_unlock_cmd))
telegram_app.add_handler(CommandHandler("unlock_download", unlock_download_cmd))
telegram_app.add_handler(CommandHandler("activate_supporter", activate_supporter_cmd))
telegram_app.add_handler(CommandHandler("list_songs", list_songs_cmd))
telegram_app.add_handler(CommandHandler("delete_song", delete_song_cmd))
telegram_app.add_handler(CommandHandler("approve_submission", approve_submission_cmd))
telegram_app.add_handler(CommandHandler("approve_voice", approve_voice_cmd))
telegram_app.add_handler(CommandHandler("create_auction", create_auction_cmd))
telegram_app.add_handler(CommandHandler("add_event", add_event_cmd))

telegram_app.add_handler(CallbackQueryHandler(lang_cb, pattern="^lang:"))
telegram_app.add_handler(CallbackQueryHandler(entry_step2_cb, pattern="^entry:step2"))
telegram_app.add_handler(CallbackQueryHandler(entry_step3_cb, pattern="^entry:step3"))
telegram_app.add_handler(CallbackQueryHandler(entry_agreed_cb, pattern="^entry:agreed"))
telegram_app.add_handler(CallbackQueryHandler(entry_gate_done_cb, pattern="^entry:gate_done"))
telegram_app.add_handler(CallbackQueryHandler(panel_cb, pattern="^panel:"))
telegram_app.add_handler(CallbackQueryHandler(action_cb, pattern="^action:"))
telegram_app.add_handler(CallbackQueryHandler(service_cb, pattern="^service:"))
telegram_app.add_handler(CallbackQueryHandler(merch_cb, pattern="^merch:"))
telegram_app.add_handler(CallbackQueryHandler(play_song_cb, pattern="^song:"))
telegram_app.add_handler(CallbackQueryHandler(like_cb, pattern="^like:"))
telegram_app.add_handler(CallbackQueryHandler(cart_add_cb, pattern="^cart_add:"))
telegram_app.add_handler(CallbackQueryHandler(cart_remove_cb, pattern="^cart_remove:"))
telegram_app.add_handler(CallbackQueryHandler(cart_clear_cb, pattern="^cart_clear"))
telegram_app.add_handler(CallbackQueryHandler(cart_checkout_cb, pattern="^cart_checkout"))
telegram_app.add_handler(CallbackQueryHandler(buy_song_cb, pattern="^buy_song:"))
telegram_app.add_handler(CallbackQueryHandler(download_cb, pattern="^download:"))
telegram_app.add_handler(CallbackQueryHandler(radio_next_cb, pattern="^radio:next"))
telegram_app.add_handler(CallbackQueryHandler(leaderboard_cb, pattern="^lb:"))
telegram_app.add_handler(CallbackQueryHandler(vault_item_cb, pattern="^vault:"))
telegram_app.add_handler(CallbackQueryHandler(vault_pay_cb, pattern="^vault_pay:"))
telegram_app.add_handler(CallbackQueryHandler(shop_cb, pattern="^shop:"))
telegram_app.add_handler(CallbackQueryHandler(stake_cb, pattern="^stake:"))
telegram_app.add_handler(CallbackQueryHandler(mission_complete_cb, pattern="^mission:"))
telegram_app.add_handler(CallbackQueryHandler(auction_bid_cb_fn, pattern="^auction_bid:"))
telegram_app.add_handler(CallbackQueryHandler(auction_bid_cb_fn, pattern="^auction_mybids"))
telegram_app.add_handler(CallbackQueryHandler(manual_pay_cb, pattern="^manual_pay:"))
telegram_app.add_handler(CallbackQueryHandler(upload_classify_cb, pattern="^upload:"))

telegram_app.add_handler(MessageHandler(filters.LOCATION, location_handler))
telegram_app.add_handler(MessageHandler(filters.VOICE, voice_wall_submit))
telegram_app.add_handler(MessageHandler(filters.AUDIO, handle_audio_upload))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

loop = asyncio.new_event_loop()

def start_bot():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    if RADIO_CHANNEL_ID:
        loop.create_task(start_channel_radio(telegram_app.bot))
    loop.create_task(close_auctions_task())
    loop.create_task(background_tasks())
    loop.run_forever()

threading.Thread(target=start_bot, daemon=True).start()

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    data = flask_request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), loop)
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
        session_data = event["data"]["object"]
        asyncio.run_coroutine_threadsafe(process_stripe_event(session_data, telegram_app.bot), loop)
    return "ok"

@flask_app.route("/")
def health():
    from services.radio import radio_loop_running
    return f"I.A.A.I.M.O ONLINE v18.000 | PARISH 14 NATION | RADIO {'BROADCASTING' if radio_loop_running else 'STANDBY'}", 200

if __name__ == "__main__":
    init_pool()
    init_db()
    classify_rotation()
    threading.Thread(target=weekly_intel_thread, daemon=True).start()
    print("=" * 50)
    print("I.A.A.I.M.O MISERBOT v18.000")
    print("SOVEREIGN ARTIST PLATFORM")
    print("Bot: @BazragodMiserbot_bot")
    print("Nation: Parish 14")
    print("Status: ONLINE")
    print("=" * 50)
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
