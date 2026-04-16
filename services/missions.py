from database import get_conn,release_conn
from datetime import date

REWARD=10

def claim_daily(user_id):

    conn=get_conn()
    cur=conn.cursor()

    today=date.today()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS missions(
        user_id BIGINT PRIMARY KEY,
        last_claim DATE
    )
    """)

    cur.execute("SELECT last_claim FROM missions WHERE user_id=%s",(user_id,))
    row=cur.fetchone()

    if row and row[0]==today:
        release_conn(conn)
        return False

    cur.execute("""
    INSERT INTO missions(user_id,last_claim)
    VALUES(%s,%s)
    ON CONFLICT(user_id)
    DO UPDATE SET last_claim=%s
    """,(user_id,today,today))

    cur.execute(
    "UPDATE users SET coins=coins+%s WHERE user_id=%s",
    (REWARD,user_id)
    )

    conn.commit()
    release_conn(conn)

    return True
