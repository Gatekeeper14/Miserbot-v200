import psycopg2
from psycopg2.pool import SimpleConnectionPool
from config import DATABASE_URL

pool=None

def init_db():
    global pool
    pool=SimpleConnectionPool(1,10,DATABASE_URL)

def get_conn():
    return pool.getconn()

def release_conn(conn):
    pool.putconn(conn)

def setup_tables():

    conn=get_conn()
    cur=conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id BIGINT PRIMARY KEY,
        username TEXT,
        coins INT DEFAULT 0,
        joined TIMESTAMP DEFAULT NOW()
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS songs(
        id SERIAL PRIMARY KEY,
        title TEXT,
        file_id TEXT,
        price INT DEFAULT 5
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS referrals(
        user_id BIGINT,
        invited BIGINT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS passports(
        user_id BIGINT PRIMARY KEY,
        passport TEXT
    )
    """)

    conn.commit()
    release_conn(conn)
