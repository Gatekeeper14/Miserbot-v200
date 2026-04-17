from datetime import date, timedelta
from database import get_db, release_db
from services.economy import award_points

def activate_supporter(uid, days=30):
    expires = date.today() + timedelta(days=days)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET is_supporter=TRUE, tier='Nation Elite', supporter_expires=%s WHERE telegram_id=%s RETURNING username", (expires, uid))
        row = cur.fetchone(); conn.commit()
        return row[0] if row else None, expires
    finally:
        release_db(conn)

def is_supporter(uid):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT is_supporter, supporter_expires FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
        if not row: return False, None
        return row[0], row[1]
    finally:
        release_db(conn)
