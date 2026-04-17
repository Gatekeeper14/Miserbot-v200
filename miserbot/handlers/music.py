from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import get_db, release_db
from services.economy import award_points
from services.radio import next_item_for_user, log_radio, get_listener_count
from core.metadata import heat_score, increment_plays, increment_likes
from core.cart import cart_add, cart_get, cart_remove, cart_clear, cart_price
from core.generator import create_stripe_checkout
from config import CASHAPP, PAYPAL, SONG_PRICE, ALBUM_PRICE, ALBUM_COUNT

async def music_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    award_points(uid, "play_song", name)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, plays, likes, donations FROM songs ORDER BY id")
        songs = cur.fetchall()
    finally:
        release_db(conn)
    if not songs:
        await update.message.reply_text("Catalog loading... check back soon.")
        return
    keyboard = [[InlineKeyboardButton(f"{s[1]}  {heat_score(s[3], s[4], s[2])}", callback_data=f"song:{s[0]}")] for s in songs]
    await update.message.reply_text(f"BAZRAGOD CATALOG\n{len(songs)} tracks\n\nSelect a track to play or buy", reply_markup=InlineKeyboardMarkup(keyboard))

async def play_song_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    try:
        song_id = int(query.data.split(":")[1])
    except: return
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT title, file_id, plays, likes, donations FROM songs WHERE id=%s", (song_id,))
        song = cur.fetchone()
        if song:
            cur.execute("UPDATE songs SET plays=plays+1 WHERE id=%s", (song_id,))
            conn.commit()
    finally:
        release_db(conn)
    if not song: return
    title, file_id, plays, likes, donations = song
    plays += 1
    h = heat_score(likes, donations, plays)
    pts = award_points(uid, "play_song", name)
    await query.message.reply_audio(file_id,
        caption=f"{title}\nBAZRAGOD\n\n{h}  {plays:,} plays  {likes} likes\n\n+{pts} MiserCoins",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Like", callback_data=f"like:{song_id}"),
            InlineKeyboardButton("Add to Cart", callback_data=f"cart_add:{song_id}"),
            InlineKeyboardButton("Buy Now", callback_data=f"buy_song:{song_id}"),
            InlineKeyboardButton("Download", callback_data=f"download:{song_id}"),
        ]]))

async def like_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        song_id = int(query.data.split(":")[1])
    except:
        await query.answer(); return
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    if increment_likes(uid, song_id):
        award_points(uid, "like_song", name)
        await query.answer("Liked! +3 MiserCoins", show_alert=False)
    else:
        await query.answer("Already liked", show_alert=False)

async def cart_add_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        song_id = int(query.data.split(":")[1])
    except:
        await query.answer(); return
    uid = query.from_user.id
    count = cart_add(uid, song_id)
    price, cnt = cart_price(uid)
    if cnt >= ALBUM_COUNT:
        await query.answer(f"Added! Cart: {cnt} songs = ${ALBUM_PRICE} album!", show_alert=False)
    else:
        await query.answer(f"Added! {cnt} song(s) = ${price}. Add {ALBUM_COUNT - cnt} more for album deal.", show_alert=False)

async def cart_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    items = cart_get(uid)
    if not items:
        await update.message.reply_text("YOUR CART\n\nCart is empty.\n\nBrowse music and add songs.")
        return
    price, count = cart_price(uid)
    deal = f"ALBUM DEAL! ${ALBUM_PRICE} for {count} songs" if count >= ALBUM_COUNT else f"{count} song(s) = ${price}\n\nAdd {ALBUM_COUNT - count} more for ${ALBUM_PRICE} album deal"
    text = "YOUR CART\n\n"
    keyboard = []
    for song_id, title in items:
        text += f"{title}\n"
        keyboard.append([InlineKeyboardButton(f"Remove {title[:20]}", callback_data=f"cart_remove:{song_id}")])
    text += f"\n{deal}"
    keyboard.append([InlineKeyboardButton(f"Checkout ${price}", callback_data="cart_checkout")])
    keyboard.append([InlineKeyboardButton("Clear Cart", callback_data="cart_clear")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def cart_remove_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        song_id = int(query.data.split(":")[1])
    except:
        await query.answer(); return
    uid = query.from_user.id
    cart_remove(uid, song_id)
    await query.answer("Removed from cart.")

async def cart_clear_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    cart_clear(query.from_user.id)
    await query.message.reply_text("Cart cleared.")

async def cart_checkout_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    items = cart_get(uid)
    if not items:
        await query.message.reply_text("Cart is empty."); return
    price, count = cart_price(uid)
    product_name = f"BAZRAGOD Custom Album {count} Songs" if count >= ALBUM_COUNT else f"BAZRAGOD {count} Song(s)"
    url = create_stripe_checkout(uid, name, "cart_album", price, product_name)
    if url:
        await query.message.reply_text(
            f"CHECKOUT\n\n{count} song(s)\nTotal: ${price}\n\nDelivered instantly after payment.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"Pay ${price} via Stripe", url=url)]]))
    else:
        await query.message.reply_text(
            f"CHECKOUT\n\n{count} song(s)\nTotal: ${price}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)], [InlineKeyboardButton("I Paid", callback_data="manual_pay:cart_album")]]))

async def buy_song_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    try:
        song_id = int(query.data.split(":")[1])
    except: return
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM downloads WHERE telegram_id=%s AND song_id=%s AND purchased=TRUE", (uid, song_id))
        already = cur.fetchone() is not None
        cur.execute("SELECT title FROM songs WHERE id=%s", (song_id,))
        song = cur.fetchone()
    finally:
        release_db(conn)
    if already:
        await query.answer("You already own this song.", show_alert=True); return
    if not song:
        await query.answer("Song not found.", show_alert=True); return
    title = song[0]
    url = create_stripe_checkout(uid, name, "single_song", SONG_PRICE, f"BAZRAGOD - {title}", str(song_id))
    if url:
        await query.message.reply_text(
            f"BUY SONG\n\n{title}\nBAZRAGOD\n\nPrice: ${SONG_PRICE}\n\nDelivered instantly after payment.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"Pay ${SONG_PRICE} via Stripe", url=url)]]))
    else:
        await query.message.reply_text(
            f"BUY {title}\n\nPrice: ${SONG_PRICE}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)], [InlineKeyboardButton("I Paid", callback_data=f"manual_pay:single_song:{song_id}")]]))

async def download_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    try:
        song_id = int(query.data.split(":")[1])
    except: return
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM downloads WHERE telegram_id=%s AND song_id=%s AND purchased=TRUE", (uid, song_id))
        purchased = cur.fetchone() is not None
        cur.execute("SELECT title, file_id FROM songs WHERE id=%s", (song_id,))
        song = cur.fetchone()
    finally:
        release_db(conn)
    if not song:
        await query.answer("Song not found.", show_alert=True); return
    title, file_id = song
    if purchased:
        award_points(uid, "download_purchase", name)
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("UPDATE downloads SET download_count=download_count+1 WHERE telegram_id=%s AND song_id=%s", (uid, song_id))
            conn.commit()
        finally:
            release_db(conn)
        await query.message.reply_audio(file_id, caption=f"DOWNLOAD\n\n{title}\nBAZRAGOD\n\nYours to keep. Parish 14 Nation.")
    else:
        await buy_song_cb(update, context)

async def radio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.username or str(uid)
    from services.economy import update_streak
    from config import STREAK_BONUSES, STREAK_BADGES
    streak = update_streak(uid)
    streak_msg = ""
    for milestone, bonus in sorted(STREAK_BONUSES.items()):
        if streak == milestone:
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("UPDATE users SET points=points+%s WHERE telegram_id=%s", (bonus, uid))
                cur.execute("INSERT INTO fan_points (telegram_id, action, pts, category) VALUES (%s,'streak_bonus',%s,'earn')", (uid, bonus))
                conn.commit()
            finally:
                release_db(conn)
            streak_msg = f"\n\n{STREAK_BADGES.get(milestone, '')} STREAK BONUS\n+{bonus} coins for {milestone}-day streak"
            break
    pts = award_points(uid, "radio", name)
    await _play_next(uid, name, pts, get_listener_count(), update.message, context, streak_msg)

async def radio_next_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer("Loading next...")
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    pts = award_points(uid, "radio", name)
    await _play_next(uid, name, pts, get_listener_count(), query.message, context)

async def _play_next(uid, name, pts, listeners, msg, context, extra=""):
    import random
    from config import AD_MESSAGES
    item = next_item_for_user(uid)
    now = datetime.now().strftime("%I:%M %p") if True else ""
    from datetime import datetime
    now = datetime.now().strftime("%I:%M %p")
    if item["type"] == "empty":
        await msg.reply_text("Radio loading... check back soon."); return
    if item["type"] == "ad":
        await msg.reply_text(f"BazraGod Radio {now}\n\n{random.choice(AD_MESSAGES)}\n\n{listeners} listeners{extra}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Continue Radio", callback_data="radio:next")]]))
        return
    if item["type"] in ("announcement", "drop", "beat") and item["file_id"]:
        await msg.reply_audio(item["file_id"],
            caption=f"{item['title']}\nBazraGod Radio {now}\n\n+{pts} coins{extra}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Next Track", callback_data="radio:next")]]))
        return
    if item["type"] == "song" and item["file_id"]:
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("UPDATE songs SET plays=plays+1 WHERE title=%s", (item["title"],))
            cur.execute("SELECT id, plays, likes, donations FROM songs WHERE title=%s", (item["title"],))
            row = cur.fetchone(); conn.commit()
        finally:
            release_db(conn)
        sid = row[0] if row else 0
        plays = row[1] if row else 0
        likes = row[2] if row else 0
        donations = row[3] if row else 0
        h = heat_score(likes, donations, plays)
        await msg.reply_audio(item["file_id"],
            caption=f"BazraGod Radio {now}\n\n{item['title']}\nBAZRAGOD\n\n{h}  {plays:,} plays\n\n{listeners} listeners\n\n+{pts} coins{extra}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Next Track", callback_data="radio:next"),
                InlineKeyboardButton("Like", callback_data=f"like:{sid}"),
                InlineKeyboardButton("Add to Cart", callback_data=f"cart_add:{sid}"),
                InlineKeyboardButton("Download", callback_data=f"download:{sid}"),
            ]]))
        log_radio(item["file_id"], item["title"])
