from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import SERVICES, MERCH_ITEMS, POINT_SHOP, BOOKING_TERMS, CASHAPP, PAYPAL, SUPPORTER_PRICE, VAULT_UNLOCK_PRICE, VAULT_SUPERFAN_PRICE, DEDICATION_COST, BOOKING_EMAIL
from core.generator import create_stripe_checkout
from services.economy import award_points, deduct_points
from services.vault import get_vault_menu, unlock_vault_item
from database import get_db, release_db

async def store_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("BAZRAGOD STORE AND SERVICES\n\nMusic. Features. Bookings. Everything.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Music Store", callback_data="panel:store")],
            [InlineKeyboardButton("Donate $1", callback_data="store_pay:donation1")],
            [InlineKeyboardButton("Feature Verse", callback_data="service:feature_verse")],
            [InlineKeyboardButton("Video Cameo", callback_data="service:video_cameo")],
            [InlineKeyboardButton("Club Booking", callback_data="panel:club_booking")],
            [InlineKeyboardButton("Studio Bundle", callback_data="service:studio_bundle")],
            [InlineKeyboardButton("Booking Terms", callback_data="action:booking_terms")],
            [InlineKeyboardButton("Merch Store", callback_data="panel:merch")],
            [InlineKeyboardButton("Ladies Hub", callback_data="panel:ladies_hub")],
        ]))

async def service_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    try:
        service_key = query.data.split(":")[1]
    except: return
    if service_key not in SERVICES: return
    service_name, price = SERVICES[service_key]
    url = create_stripe_checkout(uid, name, "service", price, f"BAZRAGOD - {service_name}", service_key)
    if url:
        await query.message.reply_text(
            f"SERVICE BOOKING\n\n{service_name}\nPrice: ${price:,}\n\nBAZRAGOD team contacts you within 24 hours after payment.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"Pay ${price:,} via Stripe", url=url)]]))
    else:
        await query.message.reply_text(
            f"SERVICE BOOKING\n\n{service_name}\nPrice: ${price:,}\n\nContact: {BOOKING_EMAIL}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)], [InlineKeyboardButton("I Paid", callback_data=f"manual_pay:service:{service_key}")]]))

async def merch_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("PARISH 14 MERCH\n\nOfficial BAZRAGOD clothing.\nSizes: M / L / XL",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"T-Shirt ${MERCH_ITEMS['tshirt'][1]}", callback_data="merch:tshirt")],
            [InlineKeyboardButton(f"Pullover ${MERCH_ITEMS['pullover'][1]}", callback_data="merch:pullover")],
            [InlineKeyboardButton(f"Hoodie ${MERCH_ITEMS['hoodie'][1]}", callback_data="merch:hoodie")],
        ]))

async def merch_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    try:
        key = query.data.split(":")[1]
    except: return
    if key not in MERCH_ITEMS: return
    item_name, price = MERCH_ITEMS[key]
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    url = create_stripe_checkout(uid, name, "service", price, f"Parish 14 {item_name}", key)
    keyboard = []
    if url:
        keyboard.append([InlineKeyboardButton(f"Pay ${price} via Stripe", url=url)])
    keyboard += [[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]
    await query.message.reply_text(
        f"PARISH 14 ORDER\n\nItem: {item_name}\nPrice: ${price}\nSizes: M / L / XL\n\nAfter payment send: size + address + payment proof",
        reply_markup=InlineKeyboardMarkup(keyboard))
    try:
        from config import OWNER_ID
        await context.bot.send_message(OWNER_ID, f"MERCH ORDER\nFan: @{name} ({uid})\nItem: {item_name}\nPrice: ${price}")
    except: pass

async def vault_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    award_points(uid, "vault_unlock", name)
    fan_points, items, unlocked = get_vault_menu(uid)
    if not items:
        await update.message.reply_text(
            f"SECRET VAULT\n\nYour MiserCoins: {fan_points:,}\n\nUnreleased BAZRAGOD music.\n\nUnlock by earning MiserCoins\nor pay ${VAULT_UNLOCK_PRICE} for any song\nor pay ${VAULT_SUPERFAN_PRICE} for the Super Fan Bundle.\n\nContent incoming. Stay tuned. Parish 14.")
        return
    text = f"SECRET VAULT\n\nYour MiserCoins: {fan_points:,}\n\n"
    keyboard = []
    for vid, title, req_pts in items:
        if vid in unlocked:
            btn = f"UNLOCKED {title}"
        elif fan_points >= req_pts:
            btn = f"UNLOCK {title}"
        else:
            btn = f"LOCKED {title} - {req_pts:,} coins"
        keyboard.append([InlineKeyboardButton(btn, callback_data=f"vault:{vid}")])
    keyboard.append([InlineKeyboardButton(f"Unlock Any Song ${VAULT_UNLOCK_PRICE}", callback_data="vault_pay:single")])
    keyboard.append([InlineKeyboardButton(f"Super Fan Bundle ${VAULT_SUPERFAN_PRICE}", callback_data="vault_pay:bundle")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def vault_item_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    try:
        vault_id = int(query.data.split(":")[1])
    except: return
    fan_points, items, unlocked = get_vault_menu(uid)
    item_data = next((i for i in items if i[0] == vault_id), None)
    if not item_data:
        await query.answer("Item not found.", show_alert=True); return
    vid, title, req_pts = item_data
    if vault_id in unlocked or fan_points >= req_pts:
        song = unlock_vault_item(uid, vault_id, "coins")
        if song:
            await query.message.reply_audio(song[1], caption=f"VAULT UNLOCKED\n\n{song[0]}\nBAZRAGOD Exclusive\n\nParish 14 Nation.")
    else:
        await query.answer(f"Need {req_pts - fan_points:,} more coins to unlock.", show_alert=True)

async def vault_pay_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    try:
        pay_type = query.data.split(":")[1]
    except: return
    if pay_type == "single":
        url = create_stripe_checkout(uid, name, "vault_single", VAULT_UNLOCK_PRICE, "BAZRAGOD Vault Song Unlock")
        price = VAULT_UNLOCK_PRICE; label = f"Unlock Any 1 Vault Song ${price}"
    else:
        url = create_stripe_checkout(uid, name, "vault_superfan", VAULT_SUPERFAN_PRICE, "BAZRAGOD Super Fan Bundle")
        price = VAULT_SUPERFAN_PRICE; label = f"Super Fan Bundle All Vault Songs + Merch ${price}"
    if url:
        await query.message.reply_text(f"VAULT PAYMENT\n\n{label}\n\nDelivered instantly after payment.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"Pay ${price} via Stripe", url=url)]]))
    else:
        await query.message.reply_text(f"VAULT PAYMENT\n\n{label}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)], [InlineKeyboardButton("I Paid", callback_data=f"manual_pay:{pay_type}_vault")]]))

async def coin_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points FROM users WHERE telegram_id=%s", (uid,))
        fan = cur.fetchone(); pts = fan[0] if fan else 0
    finally:
        release_db(conn)
    text = f"COIN SHOP\n\nYour balance: {pts:,} coins\n\n"
    keyboard = []
    for key, (item_name, cost) in POINT_SHOP.items():
        status = "available" if pts >= cost else "locked"
        text += f"{item_name}\nCost: {cost:,} coins  {status}\n\n"
        keyboard.append([InlineKeyboardButton(f"{item_name[:30]} {cost:,} coins", callback_data=f"shop:{key}")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def shop_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    try:
        key = query.data.split(":")[1]
    except: return
    if key not in POINT_SHOP: return
    item_name, cost = POINT_SHOP[key]
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points FROM users WHERE telegram_id=%s", (uid,))
        fan = cur.fetchone(); pts = fan[0] if fan else 0
    finally:
        release_db(conn)
    if pts < cost:
        await query.answer(f"Not enough coins. Need {cost:,}, you have {pts:,}.", show_alert=True); return
    if key == "dedication":
        context.user_data["shop_dedication"] = True
        await query.message.reply_text(f"RADIO DEDICATION\n\nCost: {cost:,} coins\n\nType your dedication message.\nMAXIMUS will announce it on BazraGod Radio."); return
    if not deduct_points(uid, cost, f"shop_{key}"):
        await query.answer("Purchase failed.", show_alert=True); return
    if key == "vault_pass":
        await query.message.reply_text("VAULT PASS PURCHASED\n\nYou can unlock any one vault item for free.\nGo to Secret Vault to redeem.")
    elif key == "supporter_day":
        from datetime import date, timedelta
        expires = date.today() + timedelta(days=1)
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("UPDATE users SET is_supporter=TRUE, supporter_expires=%s WHERE telegram_id=%s", (expires, uid)); conn.commit()
        finally:
            release_db(conn)
        await query.message.reply_text(f"1-DAY SUPPORTER ACTIVATED\n\nExpires: {expires.strftime('%d/%m/%Y')}")
    elif key == "shoutout":
        await query.message.reply_text("SHOUTOUT PURCHASED\n\nYour personal shoutout from BAZRAGOD has been queued.")
        try:
            from config import OWNER_ID
            await context.bot.send_message(OWNER_ID, f"SHOUTOUT PURCHASE\n\nFan: @{name} ({uid})\n\nRecord and broadcast.")
        except: pass
    elif key == "exclusive_dm":
        from config import AI_SYSTEM_PROMPT
        from openai import OpenAI
        import os
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        if client:
            try:
                response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": AI_SYSTEM_PROMPT}, {"role": "user", "content": f"Write a personal sovereign message to @{name} who just spent MiserCoins for an exclusive DM. 3 sentences. Make them feel like a true insider. End with a command."}], max_tokens=150)
                dm = response.choices[0].message.content
                await query.message.reply_text(f"EXCLUSIVE MESSAGE FROM MAXIMUS\n\n{dm}\n\nParish 14.")
            except:
                await query.message.reply_text(f"EXCLUSIVE DM\n\nBAZRAGOD sees you {name}. You are part of the inner circle. Parish 14 Nation.")

async def supporter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    from services.supporters import is_supporter
    active, expires = is_supporter(uid)
    if active:
        exp_str = expires.strftime("%B %d, %Y") if expires else "Active"
        await update.message.reply_text(f"PARISH 14 SUPPORTER\n\nActive\nExpires: {exp_str}\n\nBenefits: Nation Elite badge, priority shoutouts, early access, leaderboard priority.\n\nThank you."); return
    url = create_stripe_checkout(uid, name, "supporter", SUPPORTER_PRICE, "Parish 14 Supporter $19.99/month", "elite")
    keyboard = []
    if url:
        keyboard.append([InlineKeyboardButton(f"Subscribe ${SUPPORTER_PRICE:.2f}/mo via Stripe", url=url)])
    keyboard += [[InlineKeyboardButton(f"CashApp ${SUPPORTER_PRICE:.2f}/mo", url=CASHAPP)], [InlineKeyboardButton(f"PayPal ${SUPPORTER_PRICE:.2f}/mo", url=PAYPAL)]]
    await update.message.reply_text(
        f"PARISH 14 SUPPORTER\n\n${SUPPORTER_PRICE:.2f}/month\n\nBenefits:\nNation Elite badge\nPriority radio shoutouts\nEarly access songs\nLeaderboard priority",
        reply_markup=InlineKeyboardMarkup(keyboard))

async def donate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT SUM(donations) FROM songs"); total = cur.fetchone()[0] or 0
    finally:
        release_db(conn)
    from config import CHARITY_THRESHOLD
    progress = min(total, CHARITY_THRESHOLD)
    filled = int((progress / CHARITY_THRESHOLD) * 10)
    bar = "X" * filled + "." * (10 - filled)
    url1 = create_stripe_checkout(uid, name, "donation", 1, "Support BAZRAGOD $1")
    url5 = create_stripe_checkout(uid, name, "donation", 5, "Support BAZRAGOD $5")
    keyboard = []
    if url1: keyboard.append([InlineKeyboardButton("Donate $1 via Stripe", url=url1)])
    if url5: keyboard.append([InlineKeyboardButton("Donate $5 via Stripe", url=url5)])
    keyboard += [[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]
    await update.message.reply_text(
        f"PARISH 14 CHARITY FUND\n\nProgress to ${CHARITY_THRESHOLD}:\n[{bar}] {progress}/{CHARITY_THRESHOLD}\n\nEvery donation powers the movement.",
        reply_markup=InlineKeyboardMarkup(keyboard))

async def manual_pay_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    parts = query.data.split(":")
    pay_type = parts[1] if len(parts) > 1 else ""
    await query.message.reply_text("Payment submitted. Admin will verify and deliver your purchase.")
    try:
        from config import OWNER_ID
        await context.bot.send_message(OWNER_ID, f"MANUAL PAYMENT\n\nFan: @{name} ({uid})\nType: {pay_type}\nData: {':'.join(parts[2:])}\n\nVerify and deliver manually.")
    except: pass
