from datetime import date, timedelta
from database import get_db, release_db
from config import POINTS, STAKE_TIERS, DAILY_DRIP, get_rank, get_station_rank

def get_multiplier(uid):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT multiplier FROM stakes WHERE telegram_id=%s AND status='active' AND ends_at>NOW() ORDER BY multiplier DESC LIMIT 1", (uid,))
        row = cur.fetchone()
        return float(row[0]) if row else 1.0
    finally:
        release_db(conn)

def award_points(tid, action, username=None, category="earn"):
    base = POINTS.get(action, 1)
    if base == 0: return 0
    mult = get_multiplier(tid)
    pts = int(base * mult)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (telegram_id, username, points)
            VALUES (%s,%s,%s)
            ON CONFLICT (telegram_id) DO UPDATE
            SET points=users.points+EXCLUDED.points,
                username=COALESCE(EXCLUDED.username, users.username)
        """, (tid, username, pts))
        cur.execute("INSERT INTO fan_points (telegram_id, action, pts, category) VALUES (%s,%s,%s,%s)", (tid, action, pts, category))
        cur.execute("SELECT points FROM users WHERE telegram_id=%s", (tid,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE users SET tier=%s WHERE telegram_id=%s", (get_rank(row[0]), tid))
        conn.commit()
    finally:
        release_db(conn)
    return pts

def deduct_points(tid, amount, action="spend"):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points FROM users WHERE telegram_id=%s", (tid,))
        row = cur.fetchone()
        if not row or row[0] < amount: return False
        cur.execute("UPDATE users SET points=points-%s WHERE telegram_id=%s", (amount, tid))
        cur.execute("INSERT INTO fan_points (telegram_id, action, pts, category) VALUES (%s,%s,%s,'spend')", (tid, action, -amount))
        conn.commit()
        return True
    finally:
        release_db(conn)

def register_user(tid, username, referrer_id=None):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT telegram_id FROM users WHERE telegram_id=%s", (tid,))
        if cur.fetchone(): return False
        pnum = f"P14-{tid % 100000:05d}"
        cur.execute("INSERT INTO users (telegram_id, username, referrer_id, passport_number) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING", (tid, username, referrer_id, pnum))
        if referrer_id and referrer_id != tid:
            cur.execute("UPDATE users SET invites=invites+1 WHERE telegram_id=%s", (referrer_id,))
            cur.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (%s,%s)", (referrer_id, tid))
        conn.commit()
        return True
    finally:
        release_db(conn)

def get_user_lang(uid):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT language FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
        return row[0] if row and row[0] else "en"
    finally:
        release_db(conn)

def set_user_lang(uid, lang):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET language=%s WHERE telegram_id=%s", (lang, uid))
        conn.commit()
    finally:
        release_db(conn)

def update_streak(uid):
    today = date.today()
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT streak_days, last_streak_date FROM radio_state WHERE id=1")
        state = cur.fetchone(); streak = 0
        if state:
            cs, ld = state; cs = cs or 0
            if ld == today - timedelta(days=1): streak = cs + 1
            elif ld == today: streak = cs
            else: streak = 1
            cur.execute("UPDATE radio_state SET last_streak_date=%s, streak_days=%s WHERE id=1", (today, streak))
            conn.commit()
        return streak
    finally:
        release_db(conn)

def check_supporter_expiry():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET is_supporter=FALSE WHERE is_supporter=TRUE AND supporter_expires IS NOT NULL AND supporter_expires<CURRENT_DATE")
        conn.commit()
    finally:
        release_db(conn)

async def run_daily_drip(bot):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT telegram_id FROM users WHERE tier='Nation Elite' OR tier='Parish Legend'")
        elite = cur.fetchall()
    finally:
        release_db(conn)
    for (uid,) in elite:
        conn2 = get_db(); cur2 = conn2.cursor()
        try:
            cur2.execute("UPDATE users SET points=points+%s WHERE telegram_id=%s", (DAILY_DRIP, uid))
            cur2.execute("INSERT INTO fan_points (telegram_id, action, pts, category) VALUES (%s,'daily_drip',%s,'earn')", (uid, DAILY_DRIP))
            conn2.commit()
        finally:
            release_db(conn2)
        try:
            await bot.send_message(uid, f"DAILY DRIP\n\n+{DAILY_DRIP} MiserCoins deposited.\n\nNation Elite dividend. Parish 14 rewards loyalty.")
        except: pass

async def process_stake_maturity(bot):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, telegram_id, amount, multiplier, days FROM stakes WHERE status='active' AND ends_at<NOW()")
        for sid, uid, amount, multiplier, days in cur.fetchall():
            bonus = int(amount * (multiplier - 1.0) * days * 0.5)
            cur.execute("UPDATE stakes SET status='matured', earned=%s WHERE id=%s", (bonus, sid))
            cur.execute("UPDATE users SET points=points+%s WHERE telegram_id=%s", (amount + bonus, uid))
            cur.execute("INSERT INTO fan_points (telegram_id, action, pts, category) VALUES (%s,'stake_return',%s,'earn')", (uid, amount + bonus))
            conn.commit()
            try:
                await bot.send_message(uid, f"STAKE MATURED\n\nYour {amount:,} coin stake has unlocked.\nBonus: +{bonus} coins\nTotal: {amount + bonus:,} coins\n\nParish 14 pays its soldiers.")
            except: pass
    finally:
        release_db(conn)
