from database import get_db, release_db
from services.economy import deduct_points

def get_vault_menu(uid):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points FROM users WHERE telegram_id=%s", (uid,))
        fan = cur.fetchone(); fan_points = fan[0] if fan else 0
        cur.execute("SELECT id, title, required_points FROM vault_songs ORDER BY required_points")
        items = cur.fetchall()
        cur.execute("SELECT vault_id FROM vault_access WHERE telegram_id=%s", (uid,))
        unlocked = {r[0] for r in cur.fetchall()}
    finally:
        release_db(conn)
    return fan_points, items, unlocked

def unlock_vault_item(uid, vault_id, method="coins"):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO vault_access (telegram_id, vault_id, method) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING", (uid, vault_id, method))
        conn.commit()
        cur.execute("SELECT title, file_id FROM vault_songs WHERE id=%s", (vault_id,))
        return cur.fetchone()
    finally:
        release_db(conn)

def unlock_all_vault(uid, method="payment"):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM vault_songs")
        for (vid,) in cur.fetchall():
            cur.execute("INSERT INTO vault_access (telegram_id, vault_id, method) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING", (uid, vid, method))
        conn.commit()
    finally:
        release_db(conn)
