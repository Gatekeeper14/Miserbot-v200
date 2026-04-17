from config import BOOKING_TERMS, SERVICES, BOOKING_EMAIL

def get_booking_terms():
    return BOOKING_TERMS

def get_service(key):
    return SERVICES.get(key)

def save_booking(uid, username, service_type, notes=""):
    from database import get_db, release_db
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO bookings (telegram_id, username, service_type, notes) VALUES (%s,%s,%s,%s) RETURNING id", (uid, username, service_type, notes))
        bid = cur.fetchone()[0]; conn.commit()
        return bid
    finally:
        release_db(conn)
