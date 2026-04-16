from database import get_conn, release_conn


def get_all_songs():

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, artist, price
        FROM songs
        ORDER BY created_at DESC
    """)

    rows = cur.fetchall()

    release_conn(conn)

    return rows


def add_song(title, artist, file_id, price=5):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO songs(title, artist, telegram_file_id, price)
        VALUES(%s,%s,%s,%s)
    """, (title, artist, file_id, price))

    conn.commit()
    release_conn(conn)
