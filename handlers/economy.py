from database import get_conn,release_conn

async def coins(update,context):

    user=update.effective_user.id

    conn=get_conn()
    cur=conn.cursor()

    cur.execute("SELECT coins FROM users WHERE user_id=%s",(user,))
    row=cur.fetchone()

    release_conn(conn)

    coins=row[0] if row else 0

    await update.message.reply_text(
        f"MiserCoins: {coins}"
    )
