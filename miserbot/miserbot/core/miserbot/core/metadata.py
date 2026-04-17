from database import get_db, release_db

def get_song_metadata(song_id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, file_id, plays, likes, donations, rotation FROM songs WHERE id=%s", (song_id,))
        return cur.fetchone()
    finally:
        release_db(conn)

def increment_plays(song_id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE songs SET plays=plays+1 WHERE id=%s", (song_id,))
        conn.commit()
    finally:
        release_db(conn)

def increment_likes(uid, song_id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO song_likes (telegram_id, song_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (uid, song_id))
        if cur.rowcount > 0:
            cur.execute("UPDATE songs SET likes=likes+1 WHERE id=%s", (song_id,))
            conn.commit()
            return True
        return False
    finally:
        release_db(conn)

def get_top_songs(limit=10, order_by="plays"):
    conn = get_db(); cur = conn.cursor()
    try:
        col = order_by if order_by in ("plays","likes","donations") else "plays"
        cur.execute(f"SELECT title, plays, likes, donations FROM songs ORDER BY {col} DESC LIMIT %s", (limit,))
        return cur.fetchall()
    finally:
        release_db(conn)

def heat_score(likes, donations, plays):
    score = (likes * 5) + (donations * 10) + (plays / 1000)
    if score >= 250: return "FIRE x5"
    if score >= 100: return "FIRE x4"
    if score >= 50:  return "FIRE x3"
    if score >= 10:  return "FIRE x2"
    return "FIRE"

def classify_rotation():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, plays, likes, donations FROM songs")
        for sid, plays, likes, donations in cur.fetchall():
            score = (plays / 1000.0) + (likes * 5) + (donations * 10)
            rotation = "A" if score > 1000 else "B" if score > 500 else "C"
            cur.execute("UPDATE songs SET rotation=%s WHERE id=%s", (rotation, sid))
        conn.commit()
    finally:
        release_db(conn)
