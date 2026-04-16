# -------------------------------
# DATABASE INIT
# -------------------------------

def setup_database():
    conn=get_db()
    cur=conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id BIGINT PRIMARY KEY,
        username TEXT,
        coins INT DEFAULT 0,
        streak INT DEFAULT 0,
        language TEXT DEFAULT 'en',
        joined TIMESTAMP DEFAULT NOW()
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS songs(
        id SERIAL PRIMARY KEY,
        title TEXT,
        file_id TEXT,
        price INT DEFAULT 5,
        uploaded TIMESTAMP DEFAULT NOW()
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cart(
        user_id BIGINT,
        song_id INT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS referrals(
        user_id BIGINT,
        invited BIGINT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS coins(
        user_id BIGINT,
        amount INT,
        reason TEXT,
        created TIMESTAMP DEFAULT NOW()
    );
    """)

    conn.commit()
    release_db(conn)


# -------------------------------
# MAIN MENU
# -------------------------------

def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["🎧 Music","🛒 Store"],
            ["📻 Radio","💰 MiserCoins"],
            ["🏆 Leaderboard","👑 Passport"],
            ["💬 Lounge","⚙️ Support"]
        ],
        resize_keyboard=True
    )


# -------------------------------
# START COMMAND
# -------------------------------

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.effective_user

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT user_id FROM users WHERE user_id=%s",(user.id,))
    exists=cur.fetchone()

    if not exists:
        cur.execute(
            "INSERT INTO users(user_id,username) VALUES(%s,%s)",
            (user.id,user.username)
        )
        conn.commit()

    release_db(conn)

    if INTRO_FILE_ID:
        await update.message.reply_voice(INTRO_FILE_ID)

    if FIRST_MESSAGE_FILE_ID:
        await update.message.reply_voice(FIRST_MESSAGE_FILE_ID)

    await update.message.reply_text(
        "🚀 Welcome to Miserbot\n\nChoose a section below.",
        reply_markup=main_menu()
    )


# -------------------------------
# MUSIC LIST
# -------------------------------

async def music(update:Update,context:ContextTypes.DEFAULT_TYPE):

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT title,file_id FROM songs ORDER BY id DESC LIMIT 10")
    songs=cur.fetchall()

    release_db(conn)

    if not songs:
        await update.message.reply_text("🎧 Catalog loading. Upload songs to activate.")
        return

    for title,file_id in songs:
        await update.message.reply_audio(file_id,caption=f"{title}\n💰 ${SONG_PRICE}")


# -------------------------------
# RADIO
# -------------------------------

async def radio(update:Update,context:ContextTypes.DEFAULT_TYPE):

    dj=get_current_dj()

    intro=random.choice(dj["intros"])

    await update.message.reply_text(
        f"📻 {dj['name']} LIVE\n\n{intro}"
    )


# -------------------------------
# COINS
# -------------------------------

async def coins(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.effective_user

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT coins FROM users WHERE user_id=%s",(user.id,))
    row=cur.fetchone()

    release_db(conn)

    coins=row[0] if row else 0

    await update.message.reply_text(f"💰 MiserCoins Balance: {coins}")


# -------------------------------
# MESSAGE ROUTER
# -------------------------------

async def router(update:Update,context:ContextTypes.DEFAULT_TYPE):

    text=update.message.text

    if text=="🎧 Music":
        await music(update,context)

    elif text=="📻 Radio":
        await radio(update,context)

    elif text=="💰 MiserCoins":
        await coins(update,context)

    elif text=="💬 Lounge":
        await update.message.reply_text(PARISH_LOUNGE)

    else:
        await update.message.reply_text("Use the buttons below.")


# -------------------------------
# BUILD BOT
# -------------------------------

def build_bot():

    application=Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start",start))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND,router)
    )

    return application


# -------------------------------
# MAIN ENTRY
# -------------------------------

if __name__=="__main__":

    init_pool()
    setup_database()

    bot=build_bot()

    print("🚀 MISERBOT v18.000 ONLINE")

    bot.run_polling()
