import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool

DATABASE_URL = os.getenv("DATABASE_URL")

pool = SimpleConnectionPool(
    1,
    10,
    DATABASE_URL
)


def get_conn():
    return pool.getconn()


def release_conn(conn):
    pool.putconn(conn)


def setup_tables():

    conn = get_conn()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id BIGINT PRIMARY KEY,
        username TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # MISERCOINS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS misercoins(
        user_id BIGINT PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )
    """)

    # REFERRALS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS referrals(
        id SERIAL PRIMARY KEY,
        referrer BIGINT,
        referred BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # STAKING
    cur.execute("""
    CREATE TABLE IF NOT EXISTS staking(
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        amount INTEGER,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # PASSPORTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS passports(
        user_id BIGINT PRIMARY KEY,
        passport_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # SONGS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS songs(
        id SERIAL PRIMARY KEY,
        title TEXT,
        artist TEXT,
        genre TEXT,
        price INTEGER DEFAULT 5,
        telegram_file_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ALBUMS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS albums(
        id SERIAL PRIMARY KEY,
        title TEXT,
        price INTEGER DEFAULT 50,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ALBUM TRACKS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS album_tracks(
        album_id INTEGER,
        song_id INTEGER
    )
    """)

    # CART
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cart(
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        song_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ORDERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        item TEXT,
        price INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    release_conn(conn)
