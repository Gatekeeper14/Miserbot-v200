from database import get_conn, release_conn


def top_supporters():

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT username, coins
        FROM users
        ORDER BY coins DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    release_conn(conn)

    return rows
