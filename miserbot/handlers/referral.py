from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import get_db, release_db
from services.economy import award_points
from config import BOT_USERNAME, POINTS

async def refer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT invites, tier FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
    finally:
        release_db(conn)
    invites = row[0] if row else 0
    tier = row[1] if row else "Fan"
    milestones = (
        f"1 invite = +{POINTS['invite_friend']} coins\n"
        f"5 invites = +300 bonus coins\n"
        f"10 invites = Vault access unlocked\n"
        f"50 invites = Nation Elite status"
    )
    await update.message.reply_text(
        f"REFERRAL SYSTEM\n\nYour invite link:\n{link}\n\nInvites: {invites}\nTier: {tier}\n\nMILESTONES\n{milestones}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Share Link", url=f"https://t.me/share/url?url={link}&text=Join+Parish+14+Nation")]]))
    await _check_milestones(uid, invites, update.message)

async def _check_milestones(uid, invites, msg):
    conn = get_db(); cur = conn.cursor()
    try:
        if invites == 5:
            cur.execute("UPDATE users SET points=points+300 WHERE telegram_id=%s", (uid,))
            cur.execute("INSERT INTO fan_points (telegram_id, action, pts) VALUES (%s,'referral_milestone_5',300)", (uid,))
            conn.commit()
            await msg.reply_text("MILESTONE REACHED\n\n5 invites completed.\n+300 bonus MiserCoins. Parish 14.")
        elif invites == 10:
            cur.execute("SELECT id FROM vault_songs LIMIT 1")
            v = cur.fetchone()
            if v:
                cur.execute("INSERT INTO vault_access (telegram_id, vault_id, method) VALUES (%s,%s,'referral') ON CONFLICT DO NOTHING", (uid, v[0]))
            conn.commit()
            await msg.reply_text("MILESTONE REACHED\n\n10 invites completed.\nVault access unlocked. Parish 14.")
        elif invites == 50:
            from datetime import date, timedelta
            expires = date.today() + timedelta(days=365)
            cur.execute("UPDATE users SET is_supporter=TRUE, tier='Nation Elite', supporter_expires=%s WHERE telegram_id=%s", (expires, uid))
            conn.commit()
            await msg.reply_text("MILESTONE REACHED\n\n50 invites completed.\nNation Elite status granted for 1 year. Parish 14.")
    finally:
        release_db(conn)
