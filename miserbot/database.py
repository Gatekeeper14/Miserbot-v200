from psycopg2.pool import SimpleConnectionPool
from config import DATABASE_URL

db_pool = None

def init_pool():
    global db_pool
    db_pool = SimpleConnectionPool(1, 10, dsn=DATABASE_URL)

def get_db():
    return db_pool.getconn()

def release_db(conn):
    db_pool.putconn(conn)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id BIGINT PRIMARY KEY,
                username TEXT,
                points INT DEFAULT 0,
                invites INT DEFAULT 0,
                referrer_id BIGINT,
                tier TEXT DEFAULT 'Fan',
                city TEXT,
                country TEXT,
                is_supporter BOOLEAN DEFAULT FALSE,
                supporter_expires DATE,
                language TEXT DEFAULT 'en',
                entry_completed BOOLEAN DEFAULT FALSE,
                gate_completed BOOLEAN DEFAULT FALSE,
                passport_number TEXT,
                joined_at TIMESTAMP DEFAULT NOW()
            )
        """)
        for col, defn in [
            ("is_supporter", "BOOLEAN DEFAULT FALSE"),
            ("supporter_expires", "DATE"),
            ("language", "TEXT DEFAULT 'en'"),
            ("entry_completed", "BOOLEAN DEFAULT FALSE"),
            ("gate_completed", "BOOLEAN DEFAULT FALSE"),
            ("passport_number", "TEXT"),
            ("invites", "INT DEFAULT 0"),
        ]:
            cur.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {defn}")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id SERIAL PRIMARY KEY,
                title TEXT UNIQUE,
                file_id TEXT UNIQUE,
                plays INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                rotation TEXT DEFAULT 'C',
                uploaded_at TIMESTAMP DEFAULT NOW()
            )
        """)
        for col, defn in [
            ("plays", "INTEGER DEFAULT 0"),
            ("likes", "INTEGER DEFAULT 0"),
            ("rotation", "TEXT DEFAULT 'C'"),
        ]:
            cur.execute(f"ALTER TABLE songs ADD COLUMN IF NOT EXISTS {col} {defn}")

        tables = [
            """CREATE TABLE IF NOT EXISTS beats (
                id SERIAL PRIMARY KEY,
                title TEXT UNIQUE,
                file_id TEXT UNIQUE,
                plays INTEGER DEFAULT 0,
                uploaded_at TIMESTAMP DEFAULT NOW()
            )""",
            """CREATE TABLE IF NOT EXISTS drops (
                id SERIAL PRIMARY KEY,
                title TEXT UNIQUE,
                file_id TEXT UNIQUE,
                uploaded_at TIMESTAMP DEFAULT NOW()
            )""",
            """CREATE TABLE IF NOT EXISTS announcements (
                id SERIAL PRIMARY KEY,
                title TEXT UNIQUE,
                file_id TEXT UNIQUE,
                uploaded_at TIMESTAMP DEFAULT NOW()
            )""",
            """CREATE TABLE IF NOT EXISTS vault_songs (
                id SERIAL PRIMARY KEY,
                title TEXT UNIQUE,
                file_id TEXT UNIQUE,
                required_points INTEGER DEFAULT 1000,
                price_usd FLOAT DEFAULT 50,
                uploaded_at TIMESTAMP DEFAULT NOW()
            )""",
            "CREATE TABLE IF NOT EXISTS vault_access (telegram_id BIGINT, vault_id INT, method TEXT DEFAULT 'points', PRIMARY KEY (telegram_id, vault_id))",
            "CREATE TABLE IF NOT EXISTS fan_points (id SERIAL PRIMARY KEY, telegram_id BIGINT, action TEXT, pts INT, category TEXT DEFAULT 'earn', logged_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS song_likes (telegram_id BIGINT, song_id INT, PRIMARY KEY (telegram_id, song_id))",
            "CREATE TABLE IF NOT EXISTS downloads (id SERIAL PRIMARY KEY, telegram_id BIGINT, song_id INT, purchased BOOLEAN DEFAULT FALSE, download_count INT DEFAULT 0, purchased_at TIMESTAMP DEFAULT NOW(), UNIQUE(telegram_id, song_id))",
            "CREATE TABLE IF NOT EXISTS cart (id SERIAL PRIMARY KEY, telegram_id BIGINT, song_id INT, added_at TIMESTAMP DEFAULT NOW(), UNIQUE(telegram_id, song_id))",
            "CREATE TABLE IF NOT EXISTS stripe_sessions (id SERIAL PRIMARY KEY, telegram_id BIGINT, session_id TEXT UNIQUE, product_type TEXT, product_id TEXT, amount INTEGER, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS payments (id SERIAL PRIMARY KEY, telegram_id BIGINT, item TEXT, price FLOAT, status TEXT DEFAULT 'pending', purchased_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS referrals (id SERIAL PRIMARY KEY, referrer_id BIGINT, referred_id BIGINT, joined_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS missions (telegram_id BIGINT, mission_date DATE, completed BOOLEAN DEFAULT FALSE, PRIMARY KEY (telegram_id, mission_date))",
            "CREATE TABLE IF NOT EXISTS fan_locations (telegram_id BIGINT PRIMARY KEY, city TEXT, country TEXT, latitude FLOAT, longitude FLOAT, updated_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS skills (id SERIAL PRIMARY KEY, telegram_id BIGINT, username TEXT, skill_name TEXT, description TEXT, status TEXT DEFAULT 'pending', submitted_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS bookings (id SERIAL PRIMARY KEY, telegram_id BIGINT, username TEXT, service_type TEXT, notes TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS dedications (id SERIAL PRIMARY KEY, telegram_id BIGINT, username TEXT, message TEXT, played BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS events (id SERIAL PRIMARY KEY, title TEXT, description TEXT, event_date TIMESTAMP, location TEXT, ticket_url TEXT, status TEXT DEFAULT 'upcoming', created_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS radio_history (id SERIAL PRIMARY KEY, file_id TEXT, title TEXT, played_at TIMESTAMP DEFAULT NOW())",
            "CREATE TABLE IF NOT EXISTS radio_queue (id SERIAL PRIMARY KEY, file_id TEXT, title TEXT, item_type TEXT, position INT DEFAULT 0, added_at TIMESTAMP DEFAULT NOW())",
            """CREATE TABLE IF NOT EXISTS radio_state (
                id INT PRIMARY KEY DEFAULT 1,
                last_updated TIMESTAMP DEFAULT NOW()
            )""",
        ]
        for tbl in tables:
            cur.execute(tbl)

        for col, defn in [
            ("current_index", "INT DEFAULT 0"),
            ("streak_days", "INT DEFAULT 0"),
            ("last_streak_date", "DATE"),
        ]:
            cur.execute(f"ALTER TABLE radio_state ADD COLUMN IF NOT EXISTS {col} {defn}")

        cur.execute("INSERT INTO radio_state (id) VALUES (1) ON CONFLICT DO NOTHING")
        conn.commit()
        print("DATABASE READY v18.000")
    finally:
        release_db(conn)
