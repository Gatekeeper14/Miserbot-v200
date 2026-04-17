async def panel_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    try:
        panel = query.data.split(":")[1]
    except:
        return

    if panel == "music":
        await query.message.reply_text("MUSIC SYSTEM", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Music Library", callback_data="panel:music_library")],
            [InlineKeyboardButton("Playlist Radio", callback_data="radio:next")],
            [InlineKeyboardButton("Secret Vault", callback_data="panel:vault_menu")],
            [InlineKeyboardButton("Super Fan Album", callback_data="vault_pay:bundle")],
            [InlineKeyboardButton("Listening Room", callback_data="panel:listening_room")],
        ]))
    elif panel == "store_main":
        await store_panel(update, context)
    elif panel == "community":
        await query.message.reply_text("COMMUNITY SYSTEM", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Invite Friends", callback_data="panel:invite")],
            [InlineKeyboardButton("Leaderboard", callback_data="panel:leaderboard")],
            [InlineKeyboardButton("Submit Track", callback_data="panel:submit")],
            [InlineKeyboardButton("Voice Wall", callback_data="panel:voice_wall")],
            [InlineKeyboardButton("Artist Spotlight", callback_data="panel:spotlight")],
        ]))
    elif panel == "economy":
        await query.message.reply_text("FAN ECONOMY", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("MiserCoins", callback_data="panel:coins")],
            [InlineKeyboardButton("My Passport", callback_data="panel:passport")],
            [InlineKeyboardButton("Daily Missions", callback_data="panel:missions")],
            [InlineKeyboardButton("My Streak", callback_data="panel:streak")],
            [InlineKeyboardButton("Coin Staking", callback_data="panel:staking")],
            [InlineKeyboardButton("Coin Shop", callback_data="panel:coin_shop")],
        ]))
    elif panel == "social":
        keyboard = [[InlineKeyboardButton(n, url=u)] for n, u in SOFT_GATE]
        keyboard.append([InlineKeyboardButton("Ladies Hub", callback_data="panel:ladies_hub")])
        keyboard.append([InlineKeyboardButton("Events", callback_data="panel:events")])
        keyboard.append([InlineKeyboardButton("About Miserbot", callback_data="panel:about")])
        await query.message.reply_text("SOCIAL ACCESS\n\nAll Parish 14 channels.", reply_markup=InlineKeyboardMarkup(keyboard))
    elif panel == "music_library":
        await music_catalog(update, context)
    elif panel == "vault_menu":
        await vault_cmd(update, context)
    elif panel == "listening_room":
        from services.radio import get_listener_count
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("SELECT title, played_at FROM radio_history ORDER BY played_at DESC LIMIT 5")
            recent = cur.fetchall()
        finally:
            release_db(conn)
        now = datetime.now().strftime("%I:%M %p")
        recently_played = "\n".join([f"  {r[0]}" for r in recent]) if recent else "  Tune in to build history"
        await query.message.reply_text(
            f"LISTENING ROOM\n\nTime: {now}\nListeners: {get_listener_count()} tuned in\n\nRECENTLY PLAYED:\n{recently_played}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Tune In Now", callback_data="radio:next")],
                [InlineKeyboardButton("Radio Channel", url=RADIO_CHANNEL_LINK)],
            ]))
    elif panel == "invite":
        await refer_cmd(update, context)
    elif panel == "leaderboard":
        await leaderboard_cmd(update, context)
    elif panel == "submit":
        await submit_track_cmd(update, context)
    elif panel == "voice_wall":
        await voice_wall_prompt(update, context)
    elif panel == "spotlight":
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("SELECT artist_name, song_title FROM artist_submissions WHERE status='approved' ORDER BY RANDOM() LIMIT 5")
            approved = cur.fetchall()
            cur.execute("SELECT COUNT(*) FROM artist_submissions WHERE status='approved'")
            total = cur.fetchone()[0]
        finally:
            release_db(conn)
        if not approved:
            await query.message.reply_text("ARTIST SPOTLIGHT\n\nNo featured artists yet.\n\nSubmit your music for review.")
            return
        text = f"ARTIST SPOTLIGHT\n\nParish 14 Network\n{total} approved artists\n\n"
        for artist_name, song_title in approved:
            text += f"Artist: {artist_name}\nTrack: {song_title}\n\n"
        await query.message.reply_text(text)
    elif panel == "coins":
        await my_coins(update, context)
    elif panel == "passport":
        await passport_cmd(update, context)
    elif panel == "missions":
        await daily_mission_cmd(update, context)
    elif panel == "streak":
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("SELECT streak_days, last_streak_date FROM radio_state WHERE id=1")
            state = cur.fetchone()
        finally:
            release_db(conn)
        streak = 0
        if state:
            sd, ld = state
            if ld and ld >= date.today() - timedelta(days=1):
                streak = sd or 0
        streak_badge = ""
        for days, badge in sorted(STREAK_BADGES.items(), reverse=True):
            if streak >= days:
                streak_badge = badge; break
        bonuses = "\n".join([f"{d} days = +{b} coins" for d, b in STREAK_BONUSES.items()])
        await query.message.reply_text(
            f"LISTENER STREAK\n\nCurrent streak: {streak} days\nBadge: {streak_badge or 'Keep going!'}\n\nSTREAK BONUSES\n{bonuses}\n\nListen daily to build your streak. Parish 14.")
    elif panel == "staking":
        await staking_cmd(update, context)
    elif panel == "coin_shop":
        await coin_shop(update, context)
    elif panel == "ladies_hub":
        await query.message.reply_text(
            "LADIES HUB\n\nExclusive female fan community for Parish 14 Nation.\n\nExperiences designed for the Queens of the movement.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Fan Photo Pass ${SERVICES['fan_photo'][1]}", callback_data="service:fan_photo")],
                [InlineKeyboardButton(f"Backstage Pass ${SERVICES['backstage_pass'][1]}", callback_data="service:backstage_pass")],
                [InlineKeyboardButton("Parish 14 Lounge", url=PARISH_LOUNGE)],
            ]))
    elif panel == "events":
        await events_cmd(update, context)
    elif panel == "about":
        await query.message.reply_text(
            f"ABOUT MISERBOT\n\nI.A.A.I.M.O\nIndependent Artists Artificial Intelligence Music Ops\n\nMiserbot is the sovereign digital music nation of BAZRAGOD.\n\nNo labels. No middlemen. Direct connection between artist and fans.\n\nPlatform: Telegram Super App\nRadio: 24/7 BazraGod Radio\nNation: Parish 14\nBrain: MAXIMUS AI\n\nContact: {BOOKING_EMAIL}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Parish 14 Lounge", url=PARISH_LOUNGE)],
                [InlineKeyboardButton("BazraGod Radio", url=RADIO_CHANNEL_LINK)],
            ]))
    elif panel == "merch":
        await merch_panel(update, context)
    elif panel == "club_booking":
        await query.message.reply_text("CLUB BOOKING\n\nBook BAZRAGOD for your event.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Small Club ${SERVICES['small_club'][1]:,}", callback_data="service:small_club")],
                [InlineKeyboardButton(f"Medium Club ${SERVICES['medium_club'][1]:,}", callback_data="service:medium_club")],
                [InlineKeyboardButton(f"Large Venue ${SERVICES['large_venue'][1]:,}", callback_data="service:large_venue")],
                [InlineKeyboardButton("Full Booking Terms", callback_data="action:booking_terms")],
            ]))

async def action_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    try:
        action = query.data.split(":")[1]
    except:
        return
    if action == "booking_terms":
        await query.message.reply_text(BOOKING_TERMS)
    elif action == "cart":
        await cart_view(update, context)

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random
    text = update.message.text or ""
    uid = update.effective_user.id

    if uid in auction_bid_sessions:
        if await auction_bid_text_handler(uid, text, update, context):
            return
    if context.user_data.get("staking_custom"):
        from handlers.economy import stake_custom_handler
        if await stake_custom_handler(uid, text, update, context):
            return
    if context.user_data.get("shop_dedication"):
        context.user_data.pop("shop_dedication", None)
        name = update.effective_user.username or str(uid)
        cost = POINT_SHOP["dedication"][1]
        from services.economy import deduct_points
        if deduct_points(uid, cost, "shop_dedication"):
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("INSERT INTO dedications (telegram_id, username, message) VALUES (%s,%s,%s) RETURNING id",
                    (uid, name, text))
                ded_id = cur.fetchone()[0]; conn.commit()
            finally:
                release_db(conn)
            await update.message.reply_text(
                f"DEDICATION QUEUED\n\nRef #{ded_id}\n\nMAXIMUS will announce your dedication on BazraGod Radio.\n\nParish 14 Nation.",
                reply_markup=main_menu)
        else:
            await update.message.reply_text("Not enough coins.")
        return
    if context.user_data.get("ai_active"):
        if await ai_chat_handler_fn(update, context):
            return
    if uid == OWNER_ID and pending_broadcasts.get(OWNER_ID):
        pending_broadcasts.pop(OWNER_ID)
        sent = await _broadcast(context, text)
        await update.message.reply_text(f"Broadcast sent to {sent} fans.")
        return

    routes = {
        "MUSIC SYSTEM": lambda u, c: _fake_panel(u, c, "music"),
        "STORE": store_panel,
        "COMMUNITY": lambda u, c: _fake_panel(u, c, "community"),
        "FAN ECONOMY": lambda u, c: _fake_panel(u, c, "economy"),
        "SOCIAL ACCESS": lambda u, c: _fake_panel(u, c, "social"),
        "MAXIMUS AI": maximus_cmd,
        "BazraGod Radio": radio_handler,
        "My Passport": passport_cmd,
        "BAZRAGOD MUSIC": music_catalog,
        "Secret Vault": vault_cmd,
        "Auction House": auction_house_cmd,
        "Help": help_cmd,
        "Back to Menu": menu_cmd,
    }
    handler = routes.get(text)
    if handler:
        await handler(update, context)

async def _fake_panel(update, context, panel_name):
    class FakeQuery:
        def __init__(self):
            self.from_user = update.effective_user
            self.message = update.message
            self.data = f"panel:{panel_name}"
        async def answer(self, *args, **kwargs):
            pass
    update.callback_query = FakeQuery()
    await panel_cb(update, context)

async def close_auctions_task():
    while True:
        try:
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("SELECT id, title, top_bidder, top_username, current_bid FROM auctions WHERE status='active' AND ends_at<NOW()")
                for aid, title, winner_id, winner_name, final_bid in cur.fetchall():
                    cur.execute("UPDATE auctions SET status='ended' WHERE id=%s", (aid,))
                    conn.commit()
                    if winner_id:
                        try:
                            await telegram_app.bot.send_message(winner_id,
                                f"YOU WON THE AUCTION\n\n{title}\nFinal bid: {final_bid:,} MiserCoins\n\nBAZRAGOD will deliver your item. Parish 14.")
                        except:
                            pass
                        try:
                            await telegram_app.bot.send_message(OWNER_ID,
                                f"AUCTION ENDED\n\n{title}\nWinner: @{winner_name} ({winner_id})\nFinal bid: {final_bid:,} coins")
                        except:
                            pass
            finally:
                release_db(conn)
        except Exception as e:
            print(f"Auction close error: {e}")
        await asyncio.sleep(60)

async def background_tasks():
    while True:
        try:
            check_supporter_expiry()
            await process_stake_maturity(telegram_app.bot)
            now = datetime.now()
            if now.hour == 9 and now.minute < 5:
                await run_daily_drip(telegram_app.bot)
        except Exception as e:
            print(f"Background task error: {e}")
        await asyncio.sleep(300)

async def send_weekly_intel():
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM users"); total_fans = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE joined_at>NOW()-INTERVAL '7 days'"); new_fans = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(points),0) FROM users"); total_pts = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fan_locations"); mapped = cur.fetchone()[0]
        cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 3"); top_fans = cur.fetchall()
        cur.execute("SELECT title, plays FROM songs ORDER BY plays DESC LIMIT 3"); top_songs = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM stripe_sessions WHERE status='completed'"); stripe_done = cur.fetchone()[0]
    finally:
        release_db(conn)
    fans_text = "\n".join([f"  @{f}  {p:,} coins" for f, p in top_fans if f]) or "  None yet"
    songs_text = "\n".join([f"  {t_}  {p_:,} plays" for t_, p_ in top_songs]) or "  None"
    report = (
        f"WEEKLY INTEL REPORT\n"
        f"Week: {datetime.now().strftime('%d %B %Y')}\n\n"
        f"Total Fans:    {total_fans:,}\n"
        f"New This Week: {new_fans}\n"
        f"Total Coins:   {total_pts:,}\n"
        f"Fans Mapped:   {mapped}\n"
        f"Stripe Sales:  {stripe_done}\n\n"
        f"TOP FANS\n{fans_text}\n\n"
        f"TOP SONGS\n{songs_text}\n\n"
        f"MAXIMUS INTEL v18.000"
    )
    try:
        await telegram_app.bot.send_message(OWNER_ID, report)
    except Exception as e:
        print(f"Weekly intel error: {e}")

def weekly_intel_thread():
    last_sent = None
    while True:
        try:
            now = datetime.now()
            week_key = now.strftime("%Y-%W")
            if now.weekday() == 6 and now.hour == 9 and last_sent != week_key:
                asyncio.run_coroutine_threadsafe(send_weekly_intel(), loop)
                last_sent = week_key
        except Exception as e:
            print(f"Weekly thread error: {e}")
        time.sleep(60)

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", entry_sequence))
telegram_app.add_handler(CommandHandler("menu", menu_cmd))
telegram_app.add_handler(CommandHandler("cancel", cancel_cmd))
telegram_app.add_handler(CommandHandler("help", help_cmd))
telegram_app.add_handler(CommandHandler("language", language_select))
telegram_app.add_handler(CommandHandler("radio", radio_handler))
telegram_app.add_handler(CommandHandler("music", music_catalog))
telegram_app.add_handler(CommandHandler("cart", cart_view))
telegram_app.add_handler(CommandHandler("vault", vault_cmd))
telegram_app.add_handler(CommandHandler("coins", my_coins))
telegram_app.add_handler(CommandHandler("passport", passport_cmd))
telegram_app.add_handler(CommandHandler("profile", passport_cmd))
telegram_app.add_handler(CommandHandler("missions", daily_mission_cmd))
telegram_app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
telegram_app.add_handler(CommandHandler("invite", refer_cmd))
telegram_app.add_handler(CommandHandler("refer", refer_cmd))
telegram_app.add_handler(CommandHandler("staking", staking_cmd))
telegram_app.add_handler(CommandHandler("store", store_panel))
telegram_app.add_handler(CommandHandler("supporter", supporter_cmd))
telegram_app.add_handler(CommandHandler("donate", donate_cmd))
telegram_app.add_handler(CommandHandler("social", social_cmd))
telegram_app.add_handler(CommandHandler("community", community_cmd))
telegram_app.add_handler(CommandHandler("events", events_cmd))
telegram_app.add_handler(CommandHandler("tour", tour_cmd))
telegram_app.add_handler(CommandHandler("booking", booking_cmd))
telegram_app.add_handler(CommandHandler("submit", submit_track_cmd))
telegram_app.add_handler(CommandHandler("radar", fan_radar_cmd))
telegram_app.add_handler(CommandHandler("stats", stats_cmd))
telegram_app.add_handler(CommandHandler("wisdom", wisdom_cmd))
telegram_app.add_handler(CommandHandler("fitness", fitness_cmd))
telegram_app.add_handler(CommandHandler("maximus", maximus_cmd))
telegram_app.add_handler(CommandHandler("auctions", auction_house_cmd))
telegram_app.add_handler(CommandHandler("admin", admin_cmd))
telegram_app.add_handler(CommandHandler("start_radio", start_radio_cmd))
telegram_app.add_handler(CommandHandler("broadcast", broadcast_cmd))
telegram_app.add_handler(CommandHandler("shoutout", shoutout_cmd))
telegram_app.add_handler(CommandHandler("announce", announce_cmd))
telegram_app.add_handler(CommandHandler("premiere", premiere_cmd))
telegram_app.add_handler(CommandHandler("vault_unlock", vault_unlock_cmd))
telegram_app.add_handler(CommandHandler("unlock_download", unlock_download_cmd))
telegram_app.add_handler(CommandHandler("activate_supporter", activate_supporter_cmd))
telegram_app.add_handler(CommandHandler("list_songs", list_songs_cmd))
telegram_app.add_handler(CommandHandler("delete_song", delete_song_cmd))
telegram_app.add_handler(CommandHandler("approve_submission", approve_submission_cmd))
telegram_app.add_handler(CommandHandler("approve_voice", approve_voice_cmd))
telegram_app.add_handler(CommandHandler("create_auction", create_auction_cmd))
telegram_app.add_handler(CommandHandler("add_event", add_event_cmd))

telegram_app.add_handler(CallbackQueryHandler(lang_cb, pattern="^lang:"))
telegram_app.add_handler(CallbackQueryHandler(entry_step2_cb, pattern="^entry:step2"))
telegram_app.add_handler(CallbackQueryHandler(entry_step3_cb, pattern="^entry:step3"))
telegram_app.add_handler(CallbackQueryHandler(entry_agreed_cb, pattern="^entry:agreed"))
telegram_app.add_handler(CallbackQueryHandler(entry_gate_done_cb, pattern="^entry:gate_done"))
telegram_app.add_handler(CallbackQueryHandler(panel_cb, pattern="^panel:"))
telegram_app.add_handler(CallbackQueryHandler(action_cb, pattern="^action:"))
telegram_app.add_handler(CallbackQueryHandler(service_cb, pattern="^service:"))
telegram_app.add_handler(CallbackQueryHandler(merch_cb, pattern="^merch:"))
telegram_app.add_handler(CallbackQueryHandler(play_song_cb, pattern="^song:"))
telegram_app.add_handler(CallbackQueryHandler(like_cb, pattern="^like:"))
telegram_app.add_handler(CallbackQueryHandler(cart_add_cb, pattern="^cart_add:"))
telegram_app.add_handler(CallbackQueryHandler(cart_remove_cb, pattern="^cart_remove:"))
telegram_app.add_handler(CallbackQueryHandler(cart_clear_cb, pattern="^cart_clear"))
telegram_app.add_handler(CallbackQueryHandler(cart_checkout_cb, pattern="^cart_checkout"))
telegram_app.add_handler(CallbackQueryHandler(buy_song_cb, pattern="^buy_song:"))
telegram_app.add_handler(CallbackQueryHandler(download_cb, pattern="^download:"))
telegram_app.add_handler(CallbackQueryHandler(radio_next_cb, pattern="^radio:next"))
telegram_app.add_handler(CallbackQueryHandler(leaderboard_cb, pattern="^lb:"))
telegram_app.add_handler(CallbackQueryHandler(vault_item_cb, pattern="^vault:"))
telegram_app.add_handler(CallbackQueryHandler(vault_pay_cb, pattern="^vault_pay:"))
telegram_app.add_handler(CallbackQueryHandler(shop_cb, pattern="^shop:"))
telegram_app.add_handler(CallbackQueryHandler(stake_cb, pattern="^stake:"))
telegram_app.add_handler(CallbackQueryHandler(mission_complete_cb, pattern="^mission:"))
telegram_app.add_handler(CallbackQueryHandler(auction_bid_cb_fn, pattern="^auction_bid:"))
telegram_app.add_handler(CallbackQueryHandler(auction_bid_cb_fn, pattern="^auction_mybids"))
telegram_app.add_handler(CallbackQueryHandler(manual_pay_cb, pattern="^manual_pay:"))
telegram_app.add_handler(CallbackQueryHandler(upload_classify_cb, pattern="^upload:"))

telegram_app.add_handler(MessageHandler(filters.LOCATION, location_handler))
telegram_app.add_handler(MessageHandler(filters.VOICE, voice_wall_submit))
telegram_app.add_handler(MessageHandler(filters.AUDIO, handle_audio_upload))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

loop = asyncio.new_event_loop()

def start_bot():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    if RADIO_CHANNEL_ID:
        loop.create_task(start_channel_radio(telegram_app.bot))
    loop.create_task(close_auctions_task())
    loop.create_task(background_tasks())
    loop.run_forever()

threading.Thread(target=start_bot, daemon=True).start()

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    data = flask_request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), loop)
    return "ok"

@flask_app.route("/stripe_webhook", methods=["POST"])
def stripe_webhook():
    payload = flask_request.data
    sig_header = flask_request.headers.get("Stripe-Signature")
    if not STRIPE_OK:
        return "stripe not available", 400
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return str(e), 400
    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]
        asyncio.run_coroutine_threadsafe(process_stripe_event(session_data, telegram_app.bot), loop)
    return "ok"

@flask_app.route("/")
def health():
    from services.radio import radio_loop_running
    return f"I.A.A.I.M.O ONLINE v18.000 | PARISH 14 NATION | RADIO {'BROADCASTING' if radio_loop_running else 'STANDBY'}", 200

if __name__ == "__main__":
    init_pool()
    init_db()
    classify_rotation()
    threading.Thread(target=weekly_intel_thread, daemon=True).start()
    print("=" * 50)
    print("I.A.A.I.M.O MISERBOT v18.000")
    print("SOVEREIGN ARTIST PLATFORM")
    print("Bot: @BazragodMiserbot_bot")
    print("Nation: Parish 14")
    print("Status: ONLINE")
    print("=" * 50)
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
