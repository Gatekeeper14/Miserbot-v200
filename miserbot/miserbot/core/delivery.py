from database import get_db, release_db
from core.cart import cart_get, cart_clear
from config import BOOKING_EMAIL, VAULT_SUPERFAN_PRICE

async def deliver_single_song(bot, uid, song_id, username):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO downloads (telegram_id, song_id, purchased) VALUES (%s,%s,TRUE) ON CONFLICT DO NOTHING", (uid, song_id))
        cur.execute("SELECT title, file_id FROM songs WHERE id=%s", (song_id,))
        song = cur.fetchone()
        conn.commit()
    finally:
        release_db(conn)
    if song:
        await bot.send_audio(uid, song[1], caption=f"DOWNLOAD DELIVERED\n\n{song[0]}\nBAZRAGOD\n\nYours to keep. Parish 14 Nation.")
        return True
    return False

async def deliver_cart_album(bot, uid, username):
    items = cart_get(uid)
    if not items:
        return 0
    for song_id, title in items:
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO downloads (telegram_id, song_id, purchased) VALUES (%s,%s,TRUE) ON CONFLICT DO NOTHING", (uid, song_id))
            cur.execute("SELECT title, file_id FROM songs WHERE id=%s", (song_id,))
            song = cur.fetchone()
            conn.commit()
        finally:
            release_db(conn)
        if song:
            await bot.send_audio(uid, song[1], caption=f"{song[0]} - BAZRAGOD")
    cart_clear(uid)
    await bot.send_message(uid, f"ALBUM DELIVERED\n\n{len(items)} tracks sent.\nBAZRAGOD\n\nParish 14 Nation.")
    return len(items)

async def deliver_vault_single(bot, uid):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM vault_songs LIMIT 1")
        v = cur.fetchone()
        if v:
            cur.execute("INSERT INTO vault_access (telegram_id, vault_id, method) VALUES (%s,%s,'payment') ON CONFLICT DO NOTHING", (uid, v[0]))
            conn.commit()
    finally:
        release_db(conn)
    await bot.send_message(uid, "VAULT UNLOCKED\n\nPick your song from Secret Vault.\n\nParish 14 Nation. BAZRAGOD.")

async def deliver_vault_superfan(bot, uid, username, owner_id):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM vault_songs")
        for (vid,) in cur.fetchall():
            cur.execute("INSERT INTO vault_access (telegram_id, vault_id, method) VALUES (%s,%s,'payment') ON CONFLICT DO NOTHING", (uid, vid))
        conn.commit()
    finally:
        release_db(conn)
    await bot.send_message(uid, f"SUPER FAN BUNDLE UNLOCKED\n\nAll vault songs are yours.\nMerch reward being prepared.\n\nContact {BOOKING_EMAIL} with your address.\n\nParish 14 Nation. BAZRAGOD.")
    try:
        await bot.send_message(owner_id, f"SUPER FAN PURCHASE\n\nFan: @{username} ({uid})\nPrepare merch shipment.")
    except: pass

async def deliver_supporter(bot, uid, username):
    from datetime import datetime, timedelta
    from database import get_db, release_db
    expires = datetime.now() + timedelta(days=30)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET is_supporter=TRUE, tier='Nation Elite', supporter_expires=%s WHERE telegram_id=%s", (expires.date(), uid))
        conn.commit()
    finally:
        release_db(conn)
    await bot.send_message(uid, f"SUPPORTER ACTIVATED\n\nNation Elite access unlocked.\nExpires: {expires.strftime('%B %d, %Y')}\n\nBAZRAGOD sees you.")

async def deliver_service(bot, uid, username, service_name, booking_email, owner_id):
    await bot.send_message(uid, f"SERVICE BOOKING CONFIRMED\n\n{service_name}\n\nBAZRAGOD team will contact you within 24 hours.\n\nContact: {booking_email}\n\nParish 14 Nation.")
    try:
        await bot.send_message(owner_id, f"SERVICE BOOKING\n\nFan: @{username} ({uid})\nService: {service_name}")
    except: pass
