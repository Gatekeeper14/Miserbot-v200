import random
from database import get_conn,release_conn

def create_passport(user):

    passport=f"P14-{random.randint(100000,999999)}"

    conn=get_conn()
    cur=conn.cursor()

    cur.execute("""
    INSERT INTO passports(user_id,passport)
    VALUES(%s,%s)
    ON CONFLICT(user_id)
    DO UPDATE SET passport=%s
    """,(user,passport,passport))

    conn.commit()
    release_conn(conn)

    return passport
