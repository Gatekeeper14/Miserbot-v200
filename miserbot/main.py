import os
import asyncio
import threading
import time
from datetime import datetime, date, timedelta
from flask import Flask, request as flask_request

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
)

from handlers.music import (
    music_catalog, play_song_cb, like_cb,
    cart_add_cb, cart_view, cart_remove_cb, cart_clear_cb,
    cart_checkout_cb, buy_song_cb, download_cb,
    radio_handler, radio_next_cb,
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
except Exception:
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

    await update.message.reply_text(
        f"Royal Wisdom\n\n{random.choice(QUOTES)}\n\n+{pts} MiserCoins"
    )


async def fitness_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    pts = award_points(uid, "fitness", name)

    await update.message.reply_text(
        f"{FITNESS_MSG}\n\n+{pts} MiserCoins"
    )
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

    asyncio.run_coroutine_threadsafe(
        telegram_app.process_update(update),
        loop,
    )

    return "ok"


@flask_app.route("/stripe_webhook", methods=["POST"])
def stripe_webhook():

    payload = flask_request.data
    sig_header = flask_request.headers.get("Stripe-Signature")

    if not STRIPE_OK:
        return "stripe not available", 400

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            STRIPE_WEBHOOK_SECRET,
        )
    except Exception as e:
        return str(e), 400

    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]

        asyncio.run_coroutine_threadsafe(
            process_stripe_event(session_data, telegram_app.bot),
            loop,
        )

    return "ok"


@flask_app.route("/")
def health():
    from services.radio import radio_loop_running

    return f"I.A.A.I.M.O ONLINE v18.000 | PARISH 14 NAT
