import random
from datetime import date
from database import get_db, release_db
from config import MISSIONS, POINTS

def get_today_mission(uid):
    today = date.today()
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT completed FROM missions WHERE telegram_id=%s AND mission_date=%s", (uid, today))
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO missions (telegram_id, mission_date) VALUES (%s,%s) ON CONFLICT DO NOTHING", (uid, today))
            conn.commit()
            return False, random.choice(MISSIONS)
        return row[0], random.choice(MISSIONS)
    finally:
        release_db(conn)

def complete_mission(uid):
    today = date.today()
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT completed FROM missions WHERE telegram_id=%s AND mission_date=%s", (uid, today))
        row = cur.fetchone()
        if row and row[0]:
            return False
        cur.execute("INSERT INTO missions (telegram_id, mission_date, completed) VALUES (%s,%s,TRUE) ON CONFLICT (telegram_id, mission_date) DO UPDATE SET completed=TRUE", (uid, today))
        conn.commit()
        return True
    finally:
        release_db(conn)
