import random
from datetime import date, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import get_db, release_db
from services.economy import award_points, deduct_points, get_user_lang
from services.passport import get_passport
from services.missions import get_today_mission, complete_mission
from config import POINTS, STAKE_TIERS, MISSIONS, get_rank, get_station_rank, get_next_rank, t

async def passport_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    text = get_passport(uid)
    if not text:
        await update.message.reply_text("Send /start first.")
        return
    await update.message.reply_text(text)

async def my_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points, invites, tier FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM users WHERE points > COALESCE((SELECT points FROM users WHERE telegram_id=%s),0)", (uid,))
        global_rank = cur.fetchone()[0] + 1
    finally:
        release_db(conn)
    pts, invites, tier = row if row else (0, 0, "Fan")
    from services.economy import get_multiplier
    multiplier = get_multiplier(uid)
    mult_badge = f"  {multiplier}x STAKE ACTIVE" if multiplier > 1.0 else ""
    await update.message.reply_text(
        f"YOUR MISERCOINS\n\nCoins:        {pts:,} MiserCoins\nGlobal Rank:  #{global_rank}\nNation Tier:  {tier}\nStation Rank: {get_station_rank(pts)}\nInvites:      {invites}\nMultiplier:   {multiplier}x{mult_badge}\n\nNEXT: {get_next_rank(pts)}\n\nKeep grinding. Parish 14.")

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("PARISH 14 LEADERBOARD\n\nChoose your view",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Today", callback_data="lb:today"),
            InlineKeyboardButton("Week", callback_data="lb:week"),
            InlineKeyboardButton("All Time", callback_data="lb:alltime"),
        ]]))

async def leaderboard_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    try:
        lb_type = query.data.split(":")[1]
    except: return
    conn = get_db(); cur = conn.cursor()
    try:
        if lb_type == "today":
            cur.execute("SELECT u.username, COALESCE(SUM(fp.pts),0) as pts, u.tier FROM users u LEFT JOIN fan_points fp ON u.telegram_id=fp.telegram_id AND fp.logged_at>NOW()-INTERVAL '24 hours' GROUP BY u.username, u.tier ORDER BY pts DESC LIMIT 10")
            label = "TODAY TOP FANS"
        elif lb_type == "week":
            cur.execute("SELECT u.username, COALESCE(SUM(fp.pts),0) as pts, u.tier FROM users u LEFT JOIN fan_points fp ON u.telegram_id=fp.telegram_id AND fp.logged_at>NOW()-INTERVAL '7 days' GROUP BY u.username, u.tier ORDER BY pts DESC LIMIT 10")
            label = "THIS WEEK TOP FANS"
        else:
            cur.execute("SELECT username, points, tier FROM users ORDER BY points DESC LIMIT 10")
            label = "ALL TIME LEGENDS"
        rows = cur.fetchall()
    finally:
        release_db(conn)
    text = f"PARISH 14 {label}\n\n"
    for i, (username, points, tier) in enumerate(rows):
        text += f"{i+1}. @{username or 'Anonymous'}\n{points:,} coins  {tier}\n\n"
    try:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Today", callback_data="lb:today"),
            InlineKeyboardButton("Week", callback_data="lb:week"),
            InlineKeyboardButton("All Time", callback_data="lb:alltime"),
        ]]))
    except:
        await query.message.reply_text(text)

async def daily_mission_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    completed, mission_text = get_today_mission(uid)
    if completed:
        await update.message.reply_text("DAILY MISSIONS\n\nAlready completed today.\n\nCome back tomorrow. Parish 14."); return
    await update.message.reply_text(
        f"DAILY MISSION\n\n{mission_text}\n\nReward: +{POINTS['mission']} MiserCoins\n\nComplete it then tap below.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Mark Complete", callback_data=f"mission:complete:{uid}")]]))

async def mission_complete_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    try:
        uid = int(query.data.split(":")[2])
    except: return
    if query.from_user.id != uid: return
    name = query.from_user.username or query.from_user.first_name or str(uid)
    if complete_mission(uid):
        pts = award_points(uid, "mission", name)
        lang = get_user_lang(uid)
        await query.message.reply_text(f"MISSION COMPLETE\n\n+{pts} MiserCoins\n\n{t(lang, 'mission_done')}")
    else:
        await query.message.reply_text("Already completed today.")

async def staking_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points FROM users WHERE telegram_id=%s", (uid,))
        fan = cur.fetchone(); pts = fan[0] if fan else 0
        cur.execute("SELECT amount, days, multiplier, ends_at, earned FROM stakes WHERE telegram_id=%s AND status='active' ORDER BY started_at DESC", (uid,))
        active = cur.fetchall()
    finally:
        release_db(conn)
    stake_info = ""
    if active:
        stake_info = "\n\nACTIVE STAKES\n"
        for amount, days, multiplier, ends_at, earned in active:
            days_left = max(0, (ends_at - __import__('datetime').datetime.now()).days)
            stake_info += f"Staked: {amount:,} coins  {days}d  {multiplier}x\n{days_left} days remaining\n"
    tiers = "\n".join([f"{d} days = {m}x multiplier" for d, m in STAKE_TIERS.items()])
    await update.message.reply_text(
        f"COIN STAKING\n\nLock your MiserCoins and earn multipliers.\n\nYour balance: {pts:,} coins\n\nSTAKE TIERS\n{tiers}{stake_info}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Stake 100 coins  7 days  1.2x", callback_data="stake:100:7")],
            [InlineKeyboardButton("Stake 250 coins  14 days  1.35x", callback_data="stake:250:14")],
            [InlineKeyboardButton("Stake 500 coins  30 days  1.5x", callback_data="stake:500:30")],
            [InlineKeyboardButton("Custom Amount", callback_data="stake:custom")],
        ]))

async def stake_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    if query.data == "stake:custom":
        context.user_data["staking_custom"] = True
        await query.message.reply_text("Enter how many coins to stake and how many days.\n\nFormat: amount days\nExample: 750 30\n\nMinimum: 50 coins, 7 days"); return
    try:
        _, amount_str, days_str = query.data.split(":")
        amount = int(amount_str); days = int(days_str)
    except: return
    await _process_stake(query.message, uid, name, amount, days)

async def stake_custom_handler(uid, text, update, context):
    if not context.user_data.get("staking_custom"): return False
    context.user_data.pop("staking_custom", None)
    try:
        parts = text.strip().split(); amount = int(parts[0]); days = int(parts[1])
    except:
        await update.message.reply_text("Invalid format. Use: amount days"); return True
    if days not in STAKE_TIERS:
        await update.message.reply_text("Stake period must be 7, 14, or 30 days."); return True
    name = update.effective_user.username or str(uid)
    await _process_stake(update.message, uid, name, amount, days)
    return True

async def _process_stake(msg, uid, name, amount, days):
    if amount < 50:
        await msg.reply_text("Minimum stake is 50 coins."); return
    if days not in STAKE_TIERS:
        await msg.reply_text("Stake period must be 7, 14, or 30 days."); return
    multiplier = STAKE_TIERS[days]
    if not deduct_points(uid, amount, "stake_lock"):
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("SELECT points FROM users WHERE telegram_id=%s", (uid,)); row = cur.fetchone()
            pts = row[0] if row else 0
        finally:
            release_db(conn)
        await msg.reply_text(f"Not enough coins. You have {pts:,} coins. Need {amount:,}."); return
    ends_at = __import__('datetime').datetime.now() + timedelta(days=days)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO stakes (telegram_id, amount, days, multiplier, ends_at) VALUES (%s,%s,%s,%s,%s)", (uid, amount, days, multiplier, ends_at))
        conn.commit()
    finally:
        release_db(conn)
    from handlers.start import main_menu
    await msg.reply_text(
        f"COINS STAKED\n\nAmount: {amount:,} MiserCoins\nPeriod: {days} days\nMultiplier: {multiplier}x on ALL earns\nUnlocks: {ends_at.strftime('%d/%m/%Y')}\n\nEvery coin you earn is multiplied by {multiplier}x. Parish 14.",
        reply_markup=main_menu)

async def fan_radar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT COALESCE(country,'Unknown'), COUNT(*) FROM fan_locations GROUP BY country ORDER BY 2 DESC LIMIT 15"); cr = cur.fetchall()
        cur.execute("SELECT COALESCE(city,'Unknown'), COALESCE(country,''), COUNT(*) FROM fan_locations WHERE city IS NOT NULL GROUP BY city, country ORDER BY 3 DESC LIMIT 5"); city_r = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM fan_locations"); total_mapped = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users"); total_fans = cur.fetchone()[0]
        cur.execute("SELECT latitude, longitude FROM fan_locations WHERE telegram_id=%s", (uid,)); my_loc = cur.fetchone()
    finally:
        release_db(conn)
    if not cr:
        await update.message.reply_text("PARISH 14 FAN RADAR\n\nNo fans mapped yet.\n\nBe the first. Tap Share Location.\n\nParish 14 Nation is global."); return
    pct = round((total_mapped / total_fans * 100), 1) if total_fans > 0 else 0
    text = f"PARISH 14 FAN RADAR\n\nFans mapped: {total_mapped} of {total_fans} ({pct}%)\n\nTOP COUNTRIES\n"
    for i, (country, fans) in enumerate(cr):
        text += f"{i+1}. {country}  {fans} fans\n"
    if city_r:
        text += "\nTOP CITIES\n"
        for city, country, fans in city_r:
            text += f"  {city}, {country}  {fans} fans\n"
    text += f"\nYOUR LOCATION: {'Mapped' if my_loc else 'Not shared. Tap Share Location.'}"
    text += "\n\nThis is where BAZRAGOD's army stands. Parish 14 Nation is worldwide."
    await update.message.reply_text(text)

async def location_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telegram import KeyboardButton, ReplyKeyboardMarkup
    kb = ReplyKeyboardMarkup([[KeyboardButton("Send Location", request_location=True)], ["Back to Menu"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(f"Share your location.\n\nPut your city on the Parish 14 fan map.\nEarn +{POINTS['share_location']} MiserCoins", reply_markup=kb)

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    loc = update.message.location
    lang = get_user_lang(uid)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO fan_locations (telegram_id, latitude, longitude, updated_at) VALUES (%s,%s,%s,NOW()) ON CONFLICT (telegram_id) DO UPDATE SET latitude=EXCLUDED.latitude, longitude=EXCLUDED.longitude, updated_at=NOW()", (uid, loc.latitude, loc.longitude))
        conn.commit()
    finally:
        release_db(conn)
    pts = award_points(uid, "share_location", name)
    from handlers.start import main_menu
    await update.message.reply_text(f"{t(lang, 'location_saved')}\n\n+{pts} MiserCoins", reply_markup=main_menu)
