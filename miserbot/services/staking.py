from database import get_conn,release_conn

def stake(user_id,amount):

    conn=get_conn()
    cur=conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS staking(
        user_id BIGINT,
        amount INT
    )
    """)

    cur.execute(
    "INSERT INTO staking(user_id,amount) VALUES(%s,%s)",
    (user_id,amount)
    )

    cur.execute(
    "UPDATE users SET coins=coins-%s WHERE user_id=%s",
    (amount,user_id)
    )

    conn.commit()
    release_conn(conn)
