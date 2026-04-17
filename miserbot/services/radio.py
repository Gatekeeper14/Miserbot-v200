import asyncio
import random
from datetime import datetime
from database import get_db, release_db
from config import (
    RADIO_CHANNEL_ID, BOT_USERNAME,
    RADIO_SONG_DELAY, RADIO_BEAT_DELAY,
    RADIO_DROP_DELAY, RADIO_AD_DELAY,
    RADIO_ANNOUNCE_DELAY, AD_MESSAGES, PLAYLIST_TTL
)

radio_loop_running = False
_PLAYLIST_CACHE = []
_PLAYLIST_LAST_BUILD = 0.0

import time

def invalidate_cache():
    global _PLAYLIST_LAST_BUILD
    _PLAYLIST_LAST_BUILD = 0.0

def get_cached_playlist():
    global _PLAYLIST_CACHE, _PLAYLIST_LAST_BUILD
    if time.time() - _PLAYLIST_LAST_BUILD > PLAYLIST_TTL:
        _PLAYLIST_CACHE = build_playlist()
        _PLAYLIST_LAST_BUILD = time.time()
    return _PLAYLIST_CACHE

def build_playlist():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("""
            SELECT title, file_id, plays, likes, donations, rotation FROM songs
            WHERE file_id NOT IN (
                SELECT COALESCE(file_id,'') FROM radio_history ORDER BY played_at DESC LIMIT 8
            ) ORDER BY id
        """)
        songs = cur.fetchall()
        if not songs:
            cur.execute("SELECT title, file_id, plays, likes, donations, rotation FROM songs ORDER BY id")
            songs = cur.fetchall()
        cur.execute("SELECT title, file_id FROM drops ORDER BY id"); drops = cur.fetchall()
        cur.execute("SELECT title, file_id FROM beats ORDER BY id"); beats = cur.fetchall()
        cur.execute("SELECT title, file_id FROM announcements ORDER BY id"); ann = cur.fetchall()
    finally:
        release_db(conn)

    if not songs:
        return []

    pl = []; di = bi = ai = sc = 0
    for s in songs:
        title, file_id, plays, likes, donations, rotation = s
        pl.append({"type": "song", "title": title, "file_id": file_id,
                   "plays": plays, "likes": likes, "donations": donations, "rotation": rotation})
        sc += 1
        if drops:
            d = drops[di % len(drops)]
            pl.append({"type": "drop", "title": d[0], "file_id": d[1]}); di += 1
        if sc % 2 == 0 and beats:
            b = beats[bi % len(beats)]
            pl.append({"type": "beat", "title": b[0], "file_id": b[1]}); bi += 1
        if sc % 4 == 0:
            pl.append({"type": "ad", "title": "AD", "file_id": None})
            if ann:
                a = ann[ai % len(ann)]
                pl.append({"type": "announcement", "title": a[0], "file_id": a[1]}); ai += 1
    return pl

def save_queue(pl):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM radio_queue")
        for i, item in enumerate(pl):
            cur.execute(
                "INSERT INTO radio_queue (file_id, title, item_type, position) VALUES (%s,%s,%s,%s)",
                (item.get("file_id"), item["title"], item["type"], i)
            )
        conn.commit()
    finally:
        release_db(conn)

def get_queue():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT file_id, title, item_type FROM radio_queue ORDER BY position")
        rows = cur.fetchall()
        return [{"file_id": r[0], "title": r[1], "type": r[2]} for r in rows] if rows else []
    finally:
        release_db(conn)

def get_queue_pos():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT current_index FROM radio_state WHERE id=1")
        row = cur.fetchone()
        return row[0] if row else 0
    finally:
        release_db(conn)

def save_queue_pos(pos):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE radio_state SET current_index=%s, last_updated=NOW() WHERE id=1", (pos,))
        conn.commit()
    finally:
        release_db(conn)

def log_radio(file_id, title):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO radio_history (file_id, title) VALUES (%s,%s)", (file_id, title))
        cur.execute("DELETE FROM radio_history WHERE id NOT IN (SELECT id FROM radio_history ORDER BY played_at DESC LIMIT 50)")
        conn.commit()
    except Exception as e:
        print(f"Radio log error: {e}")
    finally:
        release_db(conn)

def get_pending_dedication():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, telegram_id, username, message FROM dedications WHERE played=FALSE ORDER BY created_at LIMIT 1")
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE dedications SET played=TRUE WHERE id=%s", (row[0],))
            conn.commit()
            return {"id": row[0], "uid": row[1], "username": row[2], "message": row[3]}
        return None
    finally:
        release_db(conn)

def get_listener_count():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM radio_history WHERE played_at > NOW() - INTERVAL '30 minutes'")
        return max(1, cur.fetchone()[0])
    finally:
        release_db(conn)

USER_PLAYLIST_INDEX = {}

def next_item_for_user(uid):
    pl = build_playlist()
    if not pl:
        return {"type": "empty", "title": "", "file_id": None}
    idx = USER_PLAYLIST_INDEX.get(uid, 0)
    if idx >= len(pl):
        idx = 0
    item = pl[idx]
    USER_PLAYLIST_INDEX[uid] = idx + 1
    return item

async def start_channel_radio(bot):
    global radio_loop_running
    if radio_loop_running:
        return
    radio_loop_running = True
    if not RADIO_CHANNEL_ID:
        radio_loop_running = False
        return
    channel_id = int(RADIO_CHANNEL_ID)
    print(f"Radio loop started for {channel_id}")
    pl = build_playlist()
    if pl:
        save_queue(pl)
    while True:
        try:
            queue = get_queue()
            if not queue:
                pl = build_playlist(); save_queue(pl); queue = pl; save_queue_pos(0)
            pos = get_queue_pos()
            if pos >= len(queue):
                pos = 0; save_queue_pos(0)
                pl = build_playlist(); save_queue(pl); queue = pl
            item = queue[pos]; save_queue_pos(pos + 1)
            now = datetime.now().strftime("%I:%M %p")
            ded = get_pending_dedication()
            if ded and random.random() < 0.15:
                await bot.send_message(chat_id=channel_id, text=f"DEDICATION\n\nFor {ded['username']}:\n{ded['message']}\n\nBazraGod Radio {now}")
            if item["type"] == "ad":
                await bot.send_message(chat_id=channel_id, text=f"BazraGod Radio {now}\n\n{random.choice(AD_MESSAGES)}\n\nt.me/{BOT_USERNAME}")
                await asyncio.sleep(RADIO_AD_DELAY)
            elif item["type"] == "announcement" and item["file_id"]:
                await bot.send_audio(chat_id=channel_id, audio=item["file_id"], caption=f"{item['title']}\nBazraGod Radio {now}\n\nt.me/{BOT_USERNAME}")
                await asyncio.sleep(RADIO_ANNOUNCE_DELAY)
            elif item["type"] == "drop" and item["file_id"]:
                await bot.send_audio(chat_id=channel_id, audio=item["file_id"], caption=f"BazraGod Radio {now}\n\nt.me/{BOT_USERNAME}")
                await asyncio.sleep(RADIO_DROP_DELAY)
            elif item["type"] == "beat" and item["file_id"]:
                await bot.send_audio(chat_id=channel_id, audio=item["file_id"], caption=f"BAZRAGOD BEAT {item['title']}\nBazraGod Radio {now}\n\nt.me/{BOT_USERNAME}")
                await asyncio.sleep(RADIO_BEAT_DELAY)
            elif item["type"] == "song" and item["file_id"]:
                conn = get_db(); cur = conn.cursor()
                try:
                    cur.execute("UPDATE songs SET plays=plays+1 WHERE title=%s", (item["title"],))
                    cur.execute("SELECT plays, likes, donations FROM songs WHERE title=%s", (item["title"],))
                    row = cur.fetchone(); conn.commit()
                finally:
                    release_db(conn)
                from core.metadata import heat_score
                plays = row[0] if row else 0; likes = row[1] if row else 0; donations = row[2] if row else 0
                h = heat_score(likes, donations, plays)
                await bot.send_audio(chat_id=channel_id, audio=item["file_id"],
                    caption=f"BazraGod Radio {now}\n\n{item['title']}\nBAZRAGOD\n\n{h}  {plays:,} plays\n\nJoin: t.me/{BOT_USERNAME}")
                log_radio(item["file_id"], item["title"])
                await asyncio.sleep(RADIO_SONG_DELAY)
        except Exception as e:
            print(f"Radio error: {e}")
            await asyncio.sleep(15)
