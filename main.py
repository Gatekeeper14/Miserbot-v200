async def cmd_passport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; name = uname(update)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT username, points, invites, tier, city, country, joined_at, is_supporter, passport_number FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
        if not row: await update.message.reply_text("Send /start first."); return
        username, points, invites, tier, city, country, joined_at, is_sup, pnum = row
        cur.execute("SELECT COUNT(*) FROM users WHERE points > %s", (points,)); global_rank = cur.fetchone()[0] + 1
        cur.execute("SELECT COUNT(*) FROM downloads WHERE telegram_id=%s AND purchased=TRUE", (uid,)); downloads = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM vault_access WHERE telegram_id=%s", (uid,)); vaults = cur.fetchone()[0]
    finally:
        release_db(conn)
    display = f"@{username}" if username else name
    location = f"{city}, {country}" if city else "Not shared"
    joined = joined_at.strftime("%B %Y") if joined_at else "Unknown"
    sup_badge = "  SUPPORTER" if is_sup else ""
    pnum = pnum or f"P14-{uid % 100000:05d}"
    await update.message.reply_text(
        f"PARISH 14 PASSPORT\n\n"
        f"Passport:     {pnum}\n"
        f"Name:         {display}{sup_badge}\n"
        f"Nation Tier:  {tier}\n"
        f"MiserCoins:   {points:,}\n"
        f"Global Rank:  #{global_rank}\n"
        f"Invites:      {invites}\n"
        f"Downloads:    {downloads}\n"
        f"Vault:        {vaults} unlocked\n"
        f"City:         {location}\n"
        f"Joined:       {joined}\n\n"
        f"NEXT: {get_next_rank(points)}\n\n"
        f"- - - - - - - - - -\n\n"
        f"{BOOKING_CARD}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Book Small Club ${SERVICES['small_club'][1]:,}", callback_data="service:small_club")],
            [InlineKeyboardButton(f"Book Medium Club ${SERVICES['medium_club'][1]:,}", callback_data="service:medium_club")],
            [InlineKeyboardButton(f"Book Large Venue ${SERVICES['large_venue'][1]:,}", callback_data="service:large_venue")],
            [InlineKeyboardButton("Contact BAZRAGOD", url=f"https://t.me/{BOT_USERNAME}")],
        ]))

async def cmd_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points, tier, invites FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM users WHERE points > COALESCE((SELECT points FROM users WHERE telegram_id=%s),0)", (uid,))
        global_rank = cur.fetchone()[0] + 1
    finally:
        release_db(conn)
    pts, tier, invites = row if row else (0, "Fan", 0)
    await update.message.reply_text(
        f"YOUR MISERCOINS\n\nCoins:       {pts:,}\nGlobal Rank: #{global_rank}\nNation Tier: {tier}\nInvites:     {invites}\n\nNEXT: {get_next_rank(pts)}\n\nKeep grinding. Parish 14.")

async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("PARISH 14 LEADERBOARD",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Today", callback_data="lb:today"),
            InlineKeyboardButton("Week", callback_data="lb:week"),
            InlineKeyboardButton("All Time", callback_data="lb:alltime"),
        ]]))

async def leaderboard_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    lb_type = q.data.split(":")[1]
    conn = get_db(); cur = conn.cursor()
    try:
        if lb_type == "today":
            cur.execute("SELECT u.username, COALESCE(SUM(fp.pts),0) as pts, u.tier FROM users u LEFT JOIN fan_points fp ON u.telegram_id=fp.telegram_id AND fp.logged_at>NOW()-INTERVAL '24 hours' GROUP BY u.username, u.tier ORDER BY pts DESC LIMIT 10")
            label = "TODAY"
        elif lb_type == "week":
            cur.execute("SELECT u.username, COALESCE(SUM(fp.pts),0) as pts, u.tier FROM users u LEFT JOIN fan_points fp ON u.telegram_id=fp.telegram_id AND fp.logged_at>NOW()-INTERVAL '7 days' GROUP BY u.username, u.tier ORDER BY pts DESC LIMIT 10")
            label = "THIS WEEK"
        else:
            cur.execute("SELECT username, points, tier FROM users ORDER BY points DESC LIMIT 10")
            label = "ALL TIME"
        rows = cur.fetchall()
    finally:
        release_db(conn)
    text = f"PARISH 14 {label}\n\n"
    for i, (username, points, tier) in enumerate(rows):
        text += f"{i+1}. @{username or 'Anonymous'}\n{points:,} coins  {tier}\n\n"
    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Today", callback_data="lb:today"),
            InlineKeyboardButton("Week", callback_data="lb:week"),
            InlineKeyboardButton("All Time", callback_data="lb:alltime"),
        ]]))
    except Exception:
        await q.message.reply_text(text)

async def cmd_missions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    today = date.today()
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT completed FROM missions WHERE telegram_id=%s AND mission_date=%s", (uid, today))
        row = cur.fetchone()
    finally:
        release_db(conn)
    if row and row[0]:
        await update.message.reply_text("DAILY MISSIONS\n\nAlready completed today.\n\nCome back tomorrow. Parish 14."); return
    mission = random.choice(MISSIONS)
    await update.message.reply_text(
        f"DAILY MISSION\n\n{mission}\n\nReward: +{POINTS['mission']} MiserCoins\n\nComplete it then tap below.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Mark Complete", callback_data=f"mission:complete:{uid}")]]))

async def mission_complete_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = int(q.data.split(":")[2])
    if q.from_user.id != uid: return
    today = date.today()
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT completed FROM missions WHERE telegram_id=%s AND mission_date=%s", (uid, today))
        row = cur.fetchone()
        if row and row[0]: await q.message.reply_text("Already completed today."); return
        cur.execute("INSERT INTO missions (telegram_id, mission_date, completed) VALUES (%s,%s,TRUE) ON CONFLICT (telegram_id, mission_date) DO UPDATE SET completed=TRUE", (uid, today))
        conn.commit()
    finally:
        release_db(conn)
    name = q.from_user.username or str(uid)
    pts = award_points(uid, "mission", name)
    await q.message.reply_text(f"MISSION COMPLETE\n\n+{pts} MiserCoins\n\n{tx(get_lang(uid), 'mission_done')}")

async def cmd_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT invites FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone(); invites = row[0] if row else 0
    finally:
        release_db(conn)
    await update.message.reply_text(
        f"REFERRAL SYSTEM\n\nYour invite link:\n{link}\n\nInvites: {invites}\n\nMILESTONES\n1 invite = +{POINTS['invite_friend']} coins\n5 invites = +300 bonus coins\n10 invites = Vault access\n50 invites = Nation Elite",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Share Link", url=f"https://t.me/share/url?url={link}&text=Join+Parish+14+Nation")]]))

async def cmd_radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT COALESCE(country,'Unknown'), COUNT(*) FROM fan_locations GROUP BY country ORDER BY 2 DESC LIMIT 15")
        cr = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM fan_locations"); total_mapped = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users"); total_fans = cur.fetchone()[0]
        cur.execute("SELECT latitude, longitude FROM fan_locations WHERE telegram_id=%s", (uid,)); my_loc = cur.fetchone()
    finally:
        release_db(conn)
    if not cr:
        await update.message.reply_text("PARISH 14 FAN RADAR\n\nNo fans mapped yet.\n\nBe the first. Share your location.\n\nParish 14 Nation is global."); return
    pct = round((total_mapped / total_fans * 100), 1) if total_fans > 0 else 0
    text = f"PARISH 14 FAN RADAR\n\nFans mapped: {total_mapped} of {total_fans} ({pct}%)\n\nTOP COUNTRIES\n"
    for i, (country, fans) in enumerate(cr):
        text += f"{i+1}. {country}  {fans} fans\n"
    text += f"\nYOUR LOCATION: {'Mapped' if my_loc else 'Not shared. Tap Share Location.'}"
    text += "\n\nThis is where BAZRAGOD's army stands. Parish 14 Nation is worldwide."
    await update.message.reply_text(text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Share My Location", callback_data="action:share_location")]]))

async def location_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup([[KeyboardButton("Send Location", request_location=True)], ["Back to Menu"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(f"Share your location to put your city on the Parish 14 fan map.\n\nEarn +{POINTS['share_location']} MiserCoins", reply_markup=kb)

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; name = uname(update)
    loc = update.message.location
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO fan_locations (telegram_id, latitude, longitude, updated_at) VALUES (%s,%s,%s,NOW()) ON CONFLICT (telegram_id) DO UPDATE SET latitude=EXCLUDED.latitude, longitude=EXCLUDED.longitude, updated_at=NOW()", (uid, loc.latitude, loc.longitude))
        conn.commit()
    finally:
        release_db(conn)
    pts = award_points(uid, "share_location", name)
    await update.message.reply_text(f"{tx(get_lang(uid), 'location_saved')}\n\n+{pts} MiserCoins", reply_markup=main_menu)

async def cmd_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    skill_sessions[uid] = {"step": "skill_name"}
    await update.message.reply_text(
        "SKILLS HARVEST\n\nContribute your skills to Parish 14 Nation.\n\nWhat is your skill?\n\nExamples: Design, Video, Photography, Promotion, Web Dev, Translation, Music Production\n\nType your skill name now.")

async def cmd_volunteer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "VOLUNTEER MISSIONS\n\nEarn MiserCoins by contributing to the nation.\n\nAvailable missions:\n\nShare a BAZRAGOD post on your socials\nCreate a fan video or design\nTranslate content to your language\nPromote BazraGod Radio in your community\nRecruit new fans to Parish 14\n\nEach completed mission earns +100 MiserCoins.\n\nTap below to claim your mission reward.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Claim Mission Reward", callback_data="volunteer:claim")]]))

async def volunteer_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; name = q.from_user.username or str(uid)
    pts = award_points(uid, "volunteer_claim", name)
    await q.message.reply_text(f"VOLUNTEER CLAIM SUBMITTED\n\n+{pts} MiserCoins\n\nAdmin will verify your contribution.\n\nParish 14 Nation grows through you.")
    try: await telegram_app.bot.send_message(OWNER_ID, f"VOLUNTEER CLAIM\n\nFan: @{name} ({uid})\nVerify their contribution and confirm.")
    except Exception: pass

async def cmd_maximus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not openai_client:
        await update.message.reply_text("MAXIMUS is offline. OPENAI_API_KEY not set."); return
    uid = update.effective_user.id; name = uname(update)
    context.user_data["ai_active"] = True
    context.user_data["ai_history"] = []
    pts = award_points(uid, "ai_chat", name)
    await update.message.reply_text(f"MAXIMUS ONLINE\n\nRoyal AI of BAZRAGOD.\nManager. Publicist. Strategist.\n\nAsk me anything.\nType /cancel to return.\n\n+{pts} MiserCoins")

async def handle_maximus_chat(uid, text, update, context):
    if not context.user_data.get("ai_active"): return False
    if not openai_client: return False
    name = uname(update)
    history = context.user_data.get("ai_history", [])
    history.append({"role": "user", "content": text})
    if len(history) > 10: history = history[-10:]
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": AI_SYSTEM_PROMPT}, *history],
            max_tokens=400)
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        context.user_data["ai_history"] = history
        award_points(uid, "ai_chat", name)
        await update.message.reply_text(f"MAXIMUS\n\n{reply}")
        await maximus_voice(context.bot, uid, reply)
    except Exception as e:
        await update.message.reply_text(f"MAXIMUS error: {str(e)}")
    return True

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    audio = update.message.audio
    if not audio or not is_admin(uid): return
    title = audio.title or audio.file_name or (update.message.caption or "").strip() or "Untitled"
    file_id = audio.file_id
    caption = (update.message.caption or "").strip().lower()
    tag_map = {
        "#song": ("songs", "Song"),
        "#beat": ("beats", "Beat"),
        "#drop": ("drops", "Drop"),
        "#announce": ("announcements", "Announcement"),
    }
    if "#vault" in caption:
        req_pts = 1000
        match = re.search(r"#vault\s*(\d+)", caption)
        if match: req_pts = int(match.group(1))
        if check_duplicate(file_id, title, "vault_songs"):
            await update.message.reply_text(f"DUPLICATE DETECTED\n\n{title!r} already exists in Vault.\n\nUpload cancelled."); return
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO vault_songs (title, file_id, required_points) VALUES (%s,%s,%s) RETURNING id", (title, file_id, req_pts))
            new_id = cur.fetchone()[0]; conn.commit()
        finally:
            release_db(conn)
        await update.message.reply_text(f"VAULT SONG ADDED\n\nID: {new_id}\nTitle: {title}\nRequired: {req_pts:,} coins")
        invalidate_cache(); return
    for tag, (dest, label) in tag_map.items():
        if tag in caption:
            if check_duplicate(file_id, title, dest):
                await update.message.reply_text(f"DUPLICATE DETECTED\n\n{title!r} already exists in {label}s.\n\nUpload cancelled."); return
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute(f"INSERT INTO {dest} (title, file_id) VALUES (%s,%s) RETURNING id", (title, file_id))
                new_id = cur.fetchone()[0]; conn.commit()
            finally:
                release_db(conn)
            await update.message.reply_text(f"{label.upper()} ADDED\n\nID: {new_id}\nTitle: {title}")
            invalidate_cache(); pl = build_playlist(); save_queue(pl); return
    await update.message.reply_text(
        f"CLASSIFY UPLOAD\n\nTitle: {title}\n\nWhat type is this audio?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Song", callback_data=f"upload:songs:{file_id}:{title}")],
            [InlineKeyboardButton("Beat", callback_data=f"upload:beats:{file_id}:{title}")],
            [InlineKeyboardButton("Drop", callback_data=f"upload:drops:{file_id}:{title}")],
            [InlineKeyboardButton("Announcement", callback_data=f"upload:announcements:{file_id}:{title}")],
            [InlineKeyboardButton("Vault 1000 coins", callback_data=f"upload:vault:1000:{file_id}:{title}")],
        ]))

async def upload_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if not is_admin(q.from_user.id): return
    parts = q.data.split(":")
    dest = parts[1]
    if dest == "vault":
        req_pts = int(parts[2]); file_id = parts[3]; title = ":".join(parts[4:])
        if check_duplicate(file_id, title, "vault_songs"):
            await q.message.reply_text(f"DUPLICATE DETECTED\n\n{title!r} already in Vault."); return
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO vault_songs (title, file_id, required_points) VALUES (%s,%s,%s) RETURNING id", (title, file_id, req_pts))
            new_id = cur.fetchone()[0]; conn.commit()
        finally:
            release_db(conn)
        await q.message.reply_text(f"VAULT SONG ADDED\n\nID: {new_id}\nTitle: {title}"); return
    file_id = parts[2]; title = ":".join(parts[3:])
    if check_duplicate(file_id, title, dest):
        await q.message.reply_text(f"DUPLICATE DETECTED\n\n{title!r} already exists."); return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute(f"INSERT INTO {dest} (title, file_id) VALUES (%s,%s) RETURNING id", (title, file_id))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    if row:
        await q.message.reply_text(f"ADDED\n\nID: {row[0]}\nTitle: {title}")
        invalidate_cache(); pl = build_playlist(); save_queue(pl)

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text(
        f"ADMIN PANEL v18.000\n\n"
        f"Radio: {'ACTIVE' if radio_loop_running else 'STANDBY'}\n\n"
        f"UPLOAD\nSend audio with caption tag:\n#song #beat #drop #announce #vault 1000\nDuplicate protection active on all uploads.\n\n"
        f"COMMANDS\n/start_radio\n/premiere song_id\n/list_songs\n/delete_song id\n/list_vault\n/delete_vault id\n/vault_unlock uid single|bundle\n/unlock_download uid song_id\n/activate_supporter uid\n/broadcast\n/shoutout @username\n/announce message\n/add_event title desc YYYY-MM-DD location\n/stats\n/weekly")

async def cmd_start_radio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not RADIO_CHANNEL_ID: await update.message.reply_text("RADIO_CHANNEL_ID not set."); return
    if radio_loop_running: await update.message.reply_text("Radio already running."); return
    asyncio.run_coroutine_threadsafe(channel_radio_loop(telegram_app.bot), loop)
    await update.message.reply_text(f"Radio STARTED. Broadcasting to {RADIO_CHANNEL_ID}. Parish 14 Nation.")

async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    pending_broadcasts[OWNER_ID] = True
    await update.message.reply_text("BROADCAST MODE\n\nSend your message now.\n/cancel to abort.")

async def cmd_shoutout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if not args: await update.message.reply_text("Usage: /shoutout @username"); return
    msg = f"SHOUTOUT FROM BAZRAGOD\n\nBig up {args[0]} real Parish 14 energy.\n\nI.A.A.I.M.O"
    sent = await _do_broadcast(msg)
    await update.message.reply_text(f"Shoutout sent to {sent} fans.")

async def cmd_announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    text = " ".join(context.args)
    if not text: await update.message.reply_text("Usage: /announce <message>"); return
    sent = await _do_broadcast(f"OFFICIAL ANNOUNCEMENT\n\n{text}\n\nBAZRAGOD")
    await update.message.reply_text(f"Sent to {sent} fans.")

async def _do_broadcast(text):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT telegram_id FROM users"); fans = cur.fetchall()
    finally:
        release_db(conn)
    sent = 0
    for (fid,) in fans:
        try: await telegram_app.bot.send_message(fid, text); sent += 1
        except Exception: pass
    return sent

async def cmd_premiere(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if not args or not args[0].isdigit(): await update.message.reply_text("Usage: /premiere <song_id>"); return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE songs SET rotation='A' WHERE id=%s RETURNING title", (int(args[0]),))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    if not row: await update.message.reply_text("Song not found."); return
    invalidate_cache(); pl = build_playlist(); save_queue(pl)
    sent = await _do_broadcast(f"WORLD PREMIERE\n\n'{row[0]}' dropping now.\n\nBAZRAGOD drops it here first.\nNo label. No middleman. Parish 14 Nation.")
    await update.message.reply_text(f"Premiere sent to {sent} fans.")

async def cmd_list_songs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, plays, likes, rotation FROM songs ORDER BY id"); rows = cur.fetchall()
    finally:
        release_db(conn)
    rb = {"A": "Hot", "B": "Mid", "C": "Deep"}
    text = f"SONGS  {len(rows)}\n\n"
    for r in rows:
        text += f"[{r[0]}] {rb.get(r[4],'')} {r[1]}\n{heat(r[3], r[2])} {r[2]:,} plays\n"
    await update.message.reply_text(text or "No songs.")

async def cmd_delete_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if not args or not args[0].isdigit(): await update.message.reply_text("Usage: /delete_song <id>"); return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM songs WHERE id=%s RETURNING title", (int(args[0]),))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    invalidate_cache(); pl = build_playlist(); save_queue(pl)
    await update.message.reply_text(f"Deleted: {row[0]}" if row else "Not found.")

async def cmd_list_vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, required_points FROM vault_songs ORDER BY id"); rows = cur.fetchall()
    finally:
        release_db(conn)
    text = f"VAULT SONGS  {len(rows)}\n\n"
    for r in rows:
        text += f"[{r[0]}] {r[1]}\n{r[2]:,} coins\n"
    await update.message.reply_text(text or "Vault empty.")

async def cmd_delete_vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if not args or not args[0].isdigit(): await update.message.reply_text("Usage: /delete_vault <id>"); return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM vault_songs WHERE id=%s RETURNING title", (int(args[0]),))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    await update.message.reply_text(f"Deleted: {row[0]}" if row else "Not found.")

async def cmd_vault_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if len(args) < 2: await update.message.reply_text("Usage: /vault_unlock <uid> <single|bundle>"); return
    fan_id = int(args[0]); pay_type = args[1]
    conn = get_db(); cur = conn.cursor()
    try:
        if pay_type == "bundle":
            cur.execute("SELECT id FROM vault_songs")
            for (vid,) in cur.fetchall():
                cur.execute("INSERT INTO vault_access (telegram_id, vault_id, method) VALUES (%s,%s,'admin') ON CONFLICT DO NOTHING", (fan_id, vid))
        conn.commit()
    finally:
        release_db(conn)
    await update.message.reply_text(f"Vault unlocked for {fan_id}.")
    try:
        msg = "VAULT ACCESS GRANTED\n\nAll vault songs are yours.\n\nParish 14." if pay_type == "bundle" else "VAULT ACCESS GRANTED\n\nGo to Secret Vault to choose your song.\n\nParish 14."
        await context.bot.send_message(fan_id, msg)
    except Exception: pass

async def cmd_unlock_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if len(args) < 2: await update.message.reply_text("Usage: /unlock_download <uid> <song_id>"); return
    fan_id = int(args[0]); song_id = int(args[1])
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO downloads (telegram_id, song_id, purchased) VALUES (%s,%s,TRUE) ON CONFLICT (telegram_id,song_id) DO UPDATE SET purchased=TRUE", (fan_id, song_id))
        cur.execute("SELECT title, file_id FROM songs WHERE id=%s", (song_id,))
        song = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    if song:
        await update.message.reply_text(f"Download unlocked for {fan_id}: {song[0]}")
        try: await context.bot.send_audio(fan_id, song[1], caption=f"DOWNLOAD UNLOCKED\n\n{song[0]}\nBAZRAGOD\n\nYours to keep. Parish 14 Nation.")
        except Exception: pass

async def cmd_activate_supporter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if not args or not args[0].isdigit(): await update.message.reply_text("Usage: /activate_supporter <uid>"); return
    fan_id = int(args[0])
    expires = date.today() + timedelta(days=30)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET is_supporter=TRUE, tier='Nation Elite', supporter_expires=%s WHERE telegram_id=%s RETURNING username", (expires, fan_id))
        row = cur.fetchone(); conn.commit()
    finally:
        release_db(conn)
    if row:
        award_points(fan_id, "supporter_sub")
        await update.message.reply_text(f"@{row[0]} activated. Expires: {expires}")
        try: await context.bot.send_message(fan_id, f"PARISH 14 SUPPORTER ACTIVATED\n\nNation Elite unlocked.\nExpires: {expires.strftime('%B %d, %Y')}\n\nBAZRAGOD sees you.")
        except Exception: pass
    else:
        await update.message.reply_text("Fan not found.")

async def cmd_add_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    args = context.args
    if len(args) < 4: await update.message.reply_text("Usage: /add_event <title> <desc> <YYYY-MM-DD> <location>"); return
    title = args[0].replace("_"," "); description = args[1].replace("_"," ")
    try: event_date = datetime.strptime(args[2], "%Y-%m-%d")
    except Exception: await update.message.reply_text("Date format: YYYY-MM-DD"); return
    location = args[3].replace("_"," ")
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO events (title, description, event_date, location) VALUES (%s,%s,%s,%s) RETURNING id", (title, description, event_date, location))
        eid = cur.fetchone()[0]; conn.commit()
    finally:
        release_db(conn)
    await update.message.reply_text(f"EVENT ADDED\n\nID: {eid}\nTitle: {title}\nDate: {event_date.strftime('%d/%m/%Y')}\nLocation: {location}")
    await _do_broadcast(f"NEW EVENT ANNOUNCED\n\n{title}\n{description}\nDate: {event_date.strftime('%d %B %Y')}\nLocation: {location}")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM users"); total_fans = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM songs"); total_songs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM beats"); total_beats = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(plays),0) FROM songs"); total_plays = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM downloads WHERE purchased=TRUE"); total_sales = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM stripe_sessions WHERE status='completed'"); stripe_sales = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fan_locations"); mapped = cur.fetchone()[0]
        if is_admin(uid):
            cur.execute("SELECT COUNT(*) FROM users WHERE is_supporter=TRUE"); supporters = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(points),0) FROM users"); total_pts = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM skills WHERE status='pending'"); pending_skills = cur.fetchone()[0]
    finally:
        release_db(conn)
    if is_admin(uid):
        await update.message.reply_text(
            f"MISERBOT STATS v18.000\n\n"
            f"Radio:         {'ACTIVE' if radio_loop_running else 'STANDBY'}\n"
            f"Total Fans:    {total_fans:,}\n"
            f"Supporters:    {supporters}\n"
            f"MiserCoins:    {total_pts:,}\n"
            f"Songs:         {total_songs}\n"
            f"Beats:         {total_beats}\n"
            f"Total Plays:   {total_plays:,}\n"
            f"Downloads:     {total_sales}\n"
            f"Stripe Sales:  {stripe_sales}\n"
            f"Fans Mapped:   {mapped}\n"
            f"Pending Skills:{pending_skills}")
    else:
        await update.message.reply_text(
            f"PLATFORM STATISTICS\n\n"
            f"Total fans:  {total_fans:,}\n"
            f"Songs:       {total_songs}\n"
            f"Beats:       {total_beats}\n"
            f"Total plays: {total_plays:,}\n"
            f"Fans mapped: {mapped}\n\n"
            f"Parish 14 Nation. BAZRAGOD.")

async def cmd_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM users"); total_fans = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE joined_at>NOW()-INTERVAL '7 days'"); new_fans = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(points),0) FROM users"); total_pts = cur.fetchone()[0]
        cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 3"); top_fans = cur.fetchall()
        cur.execute("SELECT title, plays FROM songs ORDER BY plays DESC LIMIT 3"); top_songs = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM stripe_sessions WHERE status='completed'"); stripe_done = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM downloads WHERE purchased=TRUE"); total_downloads = cur.fetchone()[0]
    finally:
        release_db(conn)
    fans_text = "\n".join([f"  @{f}  {p:,} coins" for f, p in top_fans if f]) or "  None yet"
    songs_text = "\n".join([f"  {t_}  {p_:,} plays" for t_, p_ in top_songs]) or "  None"
    await update.message.reply_text(
        f"WEEKLY INTEL REPORT\n{datetime.now().strftime('%d %B %Y')}\n\n"
        f"Total Fans:    {total_fans:,}\n"
        f"New This Week: {new_fans}\n"
        f"Total Coins:   {total_pts:,}\n"
        f"Stripe Sales:  {stripe_done}\n"
        f"Downloads:     {total_downloads}\n\n"
        f"TOP FANS\n{fans_text}\n\n"
        f"TOP SONGS\n{songs_text}\n\n"
        f"MAXIMUS INTEL v18.000")

async def cmd_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT title, description, event_date, location, ticket_url FROM events WHERE status='upcoming' AND event_date>NOW() ORDER BY event_date LIMIT 10")
        event_list = cur.fetchall()
    finally:
        release_db(conn)
    if not event_list:
        await update.message.reply_text("UPCOMING EVENTS\n\nNo events announced yet.\n\nStay tuned. Parish 14 Nation is global."); return
    text = "UPCOMING EVENTS\n\n"; kb = []
    for title, description, event_date, location, ticket_url in event_list:
        text += f"{title}\n{description}\nDate: {event_date.strftime('%d/%m/%Y')}\nLocation: {location}\n\n"
        if ticket_url: kb.append([InlineKeyboardButton(f"Tickets {title}", url=ticket_url)])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb) if kb else None)

async def cmd_social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; name = uname(update)
    pts = award_points(uid, "follow_social", name)
    kb = [[InlineKeyboardButton(n, url=u)] for n, u in SOFT_GATE]
    await update.message.reply_text(f"BAZRAGOD NETWORK\n\nJoin the Parish 14 movement.\n\n+{pts} MiserCoins", reply_markup=InlineKeyboardMarkup(kb))

async def cmd_donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id; name = uname(update)
    url1 = create_checkout(uid, name, "donation", 1, "Support BAZRAGOD $1")
    url5 = create_checkout(uid, name, "donation", 5, "Support BAZRAGOD $5")
    kb = []
    if url1: kb.append([InlineKeyboardButton("Donate $1 via Stripe", url=url1)])
    if url5: kb.append([InlineKeyboardButton("Donate $5 via Stripe", url=url5)])
    kb += [[InlineKeyboardButton("CashApp", url=CASHAPP)], [InlineKeyboardButton("PayPal", url=PAYPAL)]]
    await update.message.reply_text("SUPPORT BAZRAGOD\n\nEvery dollar goes directly to the music.\nNo label. No cut. Pure sovereign support.", reply_markup=InlineKeyboardMarkup(kb))

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"PARISH 14 HELP\n\n"
        f"/start        Enter platform\n"
        f"/music        Music catalog\n"
        f"/beats        Beat store\n"
        f"/radio        BazraGod Radio\n"
        f"/cart         Your music cart\n"
        f"/vault        Secret vault\n"
        f"/store        Store and services\n"
        f"/passport     Digital identity and booking card\n"
        f"/coins        MiserCoin balance\n"
        f"/leaderboard  Top fans\n"
        f"/missions     Daily missions\n"
        f"/invite       Referral link\n"
        f"/radar        Fan location map\n"
        f"/skills       Submit your skills\n"
        f"/volunteer    Volunteer missions\n"
        f"/events       Upcoming events\n"
        f"/social       All socials\n"
        f"/donate       Support the mission\n"
        f"/maximus      AI assistant\n"
        f"/stats        Platform stats\n"
        f"/help         This menu\n\n"
        f"Booking: {BOOKING_EMAIL}\n"
        f"Bot: @{BOT_USERNAME}\n\n"
        f"Parish 14 Nation. BAZRAGOD.")

async def action_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    action = q.data.split(":")[1] if ":" in q.data else ""
    if action == "share_location": await location_prompt(update, context)
    elif action == "invite": await cmd_invite(update, context)
    elif action == "leaderboard": await cmd_leaderboard(update, context)
    elif action == "skills": await cmd_skills(update, context)
    elif action == "volunteer": await cmd_volunteer(update, context)
    elif action == "radar": await cmd_radar(update, context)
    elif action == "events": await cmd_events(update, context)
    elif action == "coins": await cmd_coins(update, context)
    elif action == "passport": await cmd_passport(update, context)
    elif action == "missions": await cmd_missions(update, context)

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    uid = update.effective_user.id; name = uname(update)
    if uid in skill_sessions:
        step = skill_sessions[uid].get("step")
        if step == "skill_name":
            skill_sessions[uid]["skill_name"] = text
            skill_sessions[uid]["step"] = "description"
            await update.message.reply_text("Great! Now describe your skill and how you can help Parish 14 Nation.\n\nType your description:"); return
        elif step == "description":
            skill_name = skill_sessions[uid].get("skill_name", "Unknown")
            skill_sessions.pop(uid, None)
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("INSERT INTO skills (telegram_id, username, skill_name, description) VALUES (%s,%s,%s,%s) RETURNING id", (uid, name, skill_name, text))
                sid = cur.fetchone()[0]; conn.commit()
            finally:
                release_db(conn)
            pts = award_points(uid, "submit_skill", name)
            await update.message.reply_text(f"SKILL SUBMITTED\n\nSkill: {skill_name}\nRef: #{sid}\n\nBAZRAGOD will review your contribution.\n\n+{pts} MiserCoins", reply_markup=main_menu)
            try: await telegram_app.bot.send_message(OWNER_ID, f"NEW SKILL SUBMISSION #{sid}\n\nFan: @{name} ({uid})\nSkill: {skill_name}\nDescription: {text}")
            except Exception: pass
            return
    if context.user_data.get("ai_active"):
        if await handle_maximus_chat(uid, text, update, context): return
    if is_admin(uid) and pending_broadcasts.get(OWNER_ID):
        pending_broadcasts.pop(OWNER_ID)
        sent = await _do_broadcast(text)
        await update.message.reply_text(f"Broadcast sent to {sent} fans."); return
    routes = {
        "MUSIC": cmd_music,
        "STORE": cmd_store,
        "COMMUNITY": lambda u, c: u.message.reply_text("COMMUNITY", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Invite Friends", callback_data="action:invite")],
            [InlineKeyboardButton("Leaderboard", callback_data="action:leaderboard")],
            [InlineKeyboardButton("Skills Harvest", callback_data="action:skills")],
            [InlineKeyboardButton("Volunteer", callback_data="action:volunteer")],
            [InlineKeyboardButton("Fan Radar", callback_data="action:radar")],
            [InlineKeyboardButton("Events", callback_data="action:events")],
        ])),
        "FAN ECONOMY": lambda u, c: u.message.reply_text("FAN ECONOMY", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("MiserCoins", callback_data="action:coins")],
            [InlineKeyboardButton("My Passport", callback_data="action:passport")],
            [InlineKeyboardButton("Daily Missions", callback_data="action:missions")],
            [InlineKeyboardButton("Leaderboard", callback_data="action:leaderboard")],
            [InlineKeyboardButton("Invite Friends", callback_data="action:invite")],
        ])),
        "SOCIAL": cmd_social,
        "MAXIMUS AI": cmd_maximus,
        "BazraGod Radio": cmd_radio,
        "My Passport": cmd_passport,
        "Secret Vault": cmd_vault,
        "Help": cmd_help,
        "Back to Menu": lambda u, c: u.message.reply_text("Main Menu", reply_markup=main_menu),
    }
    handler = routes.get(text)
    if handler: await handler(update, context)

async def bg_tasks():
    while True:
        try:
            conn = get_db(); cur = conn.cursor()
            try:
                cur.execute("UPDATE users SET is_supporter=FALSE WHERE is_supporter=TRUE AND supporter_expires IS NOT NULL AND supporter_expires<CURRENT_DATE")
                conn.commit()
            finally:
                release_db(conn)
        except Exception as e:
            print(f"BG task error: {e}")
        await asyncio.sleep(3600)

telegram_app = Application.builder().token(BOT_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", cmd_start))
telegram_app.add_handler(CommandHandler("menu", lambda u, c: u.message.reply_text("Main Menu", reply_markup=main_menu)))
telegram_app.add_handler(CommandHandler("cancel", cmd_cancel))
telegram_app.add_handler(CommandHandler("help", cmd_help))
telegram_app.add_handler(CommandHandler("language", cmd_language))
telegram_app.add_handler(CommandHandler("music", cmd_music))
telegram_app.add_handler(CommandHandler("beats", cmd_beats))
telegram_app.add_handler(CommandHandler("radio", cmd_radio))
telegram_app.add_handler(CommandHandler("cart", cmd_cart))
telegram_app.add_handler(CommandHandler("vault", cmd_vault))
telegram_app.add_handler(CommandHandler("store", cmd_store))
telegram_app.add_handler(CommandHandler("passport", cmd_passport))
telegram_app.add_handler(CommandHandler("profile", cmd_passport))
telegram_app.add_handler(CommandHandler("coins", cmd_coins))
telegram_app.add_handler(CommandHandler("leaderboard", cmd_leaderboard))
telegram_app.add_handler(CommandHandler("missions", cmd_missions))
telegram_app.add_handler(CommandHandler("invite", cmd_invite))
telegram_app.add_handler(CommandHandler("refer", cmd_invite))
telegram_app.add_handler(CommandHandler("radar", cmd_radar))
telegram_app.add_handler(CommandHandler("skills", cmd_skills))
telegram_app.add_handler(CommandHandler("volunteer", cmd_volunteer))
telegram_app.add_handler(CommandHandler("social", cmd_social))
telegram_app.add_handler(CommandHandler("events", cmd_events))
telegram_app.add_handler(CommandHandler("donate", cmd_donate))
telegram_app.add_handler(CommandHandler("maximus", cmd_maximus))
telegram_app.add_handler(CommandHandler("stats", cmd_stats))
telegram_app.add_handler(CommandHandler("weekly", cmd_weekly))
telegram_app.add_handler(CommandHandler("admin", cmd_admin))
telegram_app.add_handler(CommandHandler("start_radio", cmd_start_radio))
telegram_app.add_handler(CommandHandler("broadcast", cmd_broadcast))
telegram_app.add_handler(CommandHandler("shoutout", cmd_shoutout))
telegram_app.add_handler(CommandHandler("announce", cmd_announce))
telegram_app.add_handler(CommandHandler("premiere", cmd_premiere))
telegram_app.add_handler(CommandHandler("list_songs", cmd_list_songs))
telegram_app.add_handler(CommandHandler("delete_song", cmd_delete_song))
telegram_app.add_handler(CommandHandler("list_vault", cmd_list_vault))
telegram_app.add_handler(CommandHandler("delete_vault", cmd_delete_vault))
telegram_app.add_handler(CommandHandler("vault_unlock", cmd_vault_unlock))
telegram_app.add_handler(CommandHandler("unlock_download", cmd_unlock_download))
telegram_app.add_handler(CommandHandler("activate_supporter", cmd_activate_supporter))
telegram_app.add_handler(CommandHandler("add_event", cmd_add_event))

telegram_app.add_handler(CallbackQueryHandler(lang_cb, pattern="^lang:"))
telegram_app.add_handler(CallbackQueryHandler(entry_step2, pattern="^entry:step2"))
telegram_app.add_handler(CallbackQueryHandler(entry_step3, pattern="^entry:step3"))
telegram_app.add_handler(CallbackQueryHandler(entry_agreed, pattern="^entry:agreed"))
telegram_app.add_handler(CallbackQueryHandler(entry_gate_done, pattern="^entry:gate_done"))
telegram_app.add_handler(CallbackQueryHandler(play_song_cb, pattern="^song:"))
telegram_app.add_handler(CallbackQueryHandler(like_cb, pattern="^like:"))
telegram_app.add_handler(CallbackQueryHandler(beat_cb, pattern="^beat:"))
telegram_app.add_handler(CallbackQueryHandler(buy_beat_cb, pattern="^buy_beat:"))
telegram_app.add_handler(CallbackQueryHandler(buy_song_cb, pattern="^buy_song:"))
telegram_app.add_handler(CallbackQueryHandler(cart_add_cb, pattern="^cart_add:"))
telegram_app.add_handler(CallbackQueryHandler(cart_remove_cb, pattern="^cart_remove:"))
telegram_app.add_handler(CallbackQueryHandler(cart_clear_cb, pattern="^cart_clear"))
telegram_app.add_handler(CallbackQueryHandler(cart_checkout_cb, pattern="^cart_checkout"))
telegram_app.add_handler(CallbackQueryHandler(radio_next_cb, pattern="^radio:next"))
telegram_app.add_handler(CallbackQueryHandler(vault_item_cb, pattern="^vault:"))
telegram_app.add_handler(CallbackQueryHandler(vault_pay_cb, pattern="^vault_pay:"))
telegram_app.add_handler(CallbackQueryHandler(store_cb, pattern="^store:"))
telegram_app.add_handler(CallbackQueryHandler(service_cb, pattern="^service:"))
telegram_app.add_handler(CallbackQueryHandler(merch_cb, pattern="^merch:"))
telegram_app.add_handler(CallbackQueryHandler(leaderboard_cb, pattern="^lb:"))
telegram_app.add_handler(CallbackQueryHandler(mission_complete_cb, pattern="^mission:"))
telegram_app.add_handler(CallbackQueryHandler(volunteer_cb, pattern="^volunteer:"))
telegram_app.add_handler(CallbackQueryHandler(upload_cb, pattern="^upload:"))
telegram_app.add_handler(CallbackQueryHandler(action_cb, pattern="^action:"))

telegram_app.add_handler(MessageHandler(filters.LOCATION, location_handler))
telegram_app.add_handler(MessageHandler(filters.AUDIO, handle_audio))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

loop = asyncio.new_event_loop()

def start_bot():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.initialize())
    loop.run_until_complete(telegram_app.start())
    if RADIO_CHANNEL_ID:
        loop.create_task(channel_radio_loop(telegram_app.bot))
    loop.create_task(bg_tasks())
    loop.run_forever()

threading.Thread(target=start_bot, daemon=True).start()

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    data = flask_request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    future = asyncio.run_coroutine_threadsafe(telegram_app.process_update(update), loop)
    try:
        future.result(timeout=30)
    except Exception as e:
        print(f"Webhook processing error: {e}")
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
        asyncio.run_coroutine_threadsafe(handle_stripe_payment(event["data"]["object"], telegram_app.bot), loop)
    return "ok"

@flask_app.route("/")
def health():
    return f"I.A.A.I.M.O ONLINE v18.000 | PARISH 14 NATION | RADIO {'BROADCASTING' if radio_loop_running else 'STANDBY'}", 200

if __name__ == "__main__":
    init_pool()
    init_db()
    print("=" * 50)
    print("I.A.A.I.M.O MISERBOT v18.000 LEAN")
    print("SOVEREIGN ARTIST PLATFORM")
    print("Bot: @BazragodMiserbot_bot")
    print("Nation: Parish 14")
    print("Status: ONLINE")
    print("=" * 50)
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
