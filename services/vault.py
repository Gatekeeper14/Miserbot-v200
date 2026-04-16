from database import get_conn, release_conn


def unlock_vault(user):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS vault(
        user_id BIGINT PRIMARY KEY,
        unlocked BOOLEAN DEFAULT FALSE,
        super_vault BOOLEAN DEFAULT FALSE
    )
    """)

    cur.execute("""
    INSERT INTO vault(user_id, unlocked)
    VALUES(%s, TRUE)
    ON CONFLICT(user_id)
    DO UPDATE SET unlocked=TRUE
    """, (user,))

    conn.commit()
    release_conn(conn)


def unlock_super_vault(user):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE vault
    SET super_vault = TRUE
    WHERE user_id = %s
    """, (user,))

    conn.commit()
    release_conn(conn)
