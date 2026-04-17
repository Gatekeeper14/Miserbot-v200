from database import get_conn,release_conn

REFERRAL_REWARD=25

def generate_referral_link(user_id,bot):

    return f"https://t.me/{bot}?start=ref{user_id}"

def record_referral(new_user,referrer):

    conn=get_conn()
    cur=conn.cursor()

    cur.execute(
    "INSERT INTO referrals(user_id,invited) VALUES(%s,%s)",
    (referrer,new_user)
    )

    cur.execute(
    "UPDATE users SET coins=coins+%s WHERE user_id=%s",
    (REFERRAL_REWARD,referrer)
    )

    conn.commit()
    release_conn(conn)
