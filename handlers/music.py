from database import get_conn,release_conn

async def music(update,context):

    conn=get_conn()
    cur=conn.cursor()

    cur.execute("SELECT title,file_id FROM songs ORDER BY id DESC")

    songs=cur.fetchall()

    release_conn(conn)

    if not songs:
        await update.message.reply_text("Catalog empty.")
        return

    for title,file_id in songs:
        await update.message.reply_audio(file_id,caption=title)
