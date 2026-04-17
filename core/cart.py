from database import get_db, release_db
from config import ALBUM_COUNT, ALBUM_PRICE, SONG_PRICE

def cart_add(uid, song_id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO cart (telegram_id, song_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (uid, song_id))
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM cart WHERE telegram_id=%s", (uid,))
        return cur.fetchone()[0]
    finally:
        release_db(conn)

def cart_remove(uid, song_id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM cart WHERE telegram_id=%s AND song_id=%s", (uid, song_id))
        conn.commit()
    finally:
        release_db(conn)

def cart_get(uid):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT s.id, s.title FROM cart c JOIN songs s ON c.song_id=s.id WHERE c.telegram_id=%s ORDER BY c.added_at", (uid,))
        return cur.fetchall()
    finally:
        release_db(conn)

def cart_clear(uid):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM cart WHERE telegram_id=%s", (uid,))
        conn.commit()
    finally:
        release_db(conn)

def cart_price(uid):
    items = cart_get(uid)
    count = len(items)
    if count == 0: return 0, 0
    if count >= ALBUM_COUNT: return ALBUM_PRICE, count
    return count * SONG_PRICE, count
