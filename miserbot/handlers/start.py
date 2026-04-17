import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import INTRO_FILE_ID, FIRST_MESSAGE_FILE_ID, SOFT_GATE, BOT_USERNAME, POINTS, t
from services.economy import register_user, award_points, get_user_lang, set_user_lang, update_streak
from database import get_db, release_db

ENTRY_COMPLETED = {}
GATE_COMPLETED = {}

SPACESHIP_FRAMES = [
    "         *        *\n     *       *   *\n           *\n        *     *\n    *       *\n          *\n\n   . . . . . . . . . .",
    "         *        *\n     *       *   *\n           *\n       [UFO]\n    *       *\n          *\n\n   . . . . . . . . . .",
    "      *      *     *\n   *    *  *    *\n        [UFO]\n          *\n    *       *\n\n   . . scanning . . . .",
    "   *    *      *\n      *    *  *\n        *\n         [UFO]\n    *  *       *\n\n   . . frequency locked .",
    "         *    *\n    *       *\n      *  *\n          *\n       [UFO]\n\n   . . Parish 14 detected .",
]

from telegram import ReplyKeyboardMarkup

main_menu = ReplyKeyboardMarkup([
    ["MUSIC SYSTEM", "STORE"],
    ["COMMUNITY", "FAN ECONOMY"],
    ["SOCIAL ACCESS", "MAXIMUS AI"],
    ["BazraGod Radio", "My Passport"],
    ["BAZRAGOD MUSIC", "Secret Vault"],
    ["Auction House", "Help"],
], resize_keyboard=True)

def get_username(update):
    u = update.effective_user
    return u.username or u.first_name or str(u.id)

def mark_entry(uid):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET entry_completed=TRUE WHERE telegram_id=%s", (uid,))
        conn.commit()
    finally:
        release_db(conn)
    ENTRY_COMPLETED[uid] = True

def mark_gate(uid):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET gate_completed=TRUE WHERE telegram_id=%s", (uid,))
        conn.commit()
    finally:
        release_db(conn)
    GATE_COMPLETED[uid] = True

def has_entry(uid):
    if ENTRY_COMPLETED.get(uid): return True
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT entry_completed FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
        if row and row[0]:
            ENTRY_COMPLETED[uid] = True
            return True
        return False
    finally:
        release_db(conn)

def has_gate(uid):
    if GATE_COMPLETED.get(uid): return True
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT gate_completed FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
        if row and row[0]:
            GATE_COMPLETED[uid] = True
            return True
        return False
    finally:
        release_db(conn)

def lang_kb():
    from config import SUPPORTED_LANGUAGES
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"lang:{code}")] for code, label in SUPPORTED_LANGUAGES.items()])

async def entry_sequence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = get_username(update)
    args = context.args if hasattr(context, "args") and context.args else []
    referrer = None
    if args and args[0].isdigit():
        referrer = int(args[0])
        if referrer == uid: referrer = None
    is_new = register_user(uid, name, referrer)
    if is_new and referrer:
        try:
            await context.bot.send_message(referrer, f"New soldier joined your link!\n+{POINTS['invite_friend']} MiserCoins credited")
            award_points(referrer, "invite_friend")
        except: pass
    award_points(uid, "start", name)
    for frame in SPACESHIP_FRAMES:
        try:
            msg = await update.message.reply_text(frame)
            await asyncio.sleep(0.8)
            await msg.delete()
        except: pass
    await update.message.reply_text("B A Z R A G O D\nI.A.A.I.M.O\nPARISH 14 COMMAND\n\nFrequency locked.\nTransmission incoming...")
    await asyncio.sleep(1)
    if has_entry(uid) and has_gate(uid):
        await update.message.reply_text("Welcome back to Parish 14 Nation.", reply_markup=main_menu)
        return
    if INTRO_FILE_ID:
        await update.message.reply_text("Before you enter press play. This is not optional.")
        await update.message.reply_voice(INTRO_FILE_ID, caption="BAZRAGOD The Vision\nI.A.A.I.M.O",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ENTER ECOSYSTEM", callback_data="entry:step2")]]))
    else:
        await show_gate(update.message, uid)

async def entry_step2_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    if FIRST_MESSAGE_FILE_ID:
        await query.message.reply_voice(FIRST_MESSAGE_FILE_ID, caption="I.A.A.I.M.O\nParish 14 Nation",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("JOIN ECOSYSTEM", callback_data="entry:step3")]]))
    else:
        await show_agreement(query.message)

async def entry_step3_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    await show_agreement(query.message)

async def show_agreement(msg):
    await msg.reply_text(
        "PARISH 14 TERMS\n\nBy entering you agree to be part of the sovereign music nation.\n\nNo labels. No middlemen. Direct connection between artist and fan.\n\nDo you agree?",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("I AGREE ENTER", callback_data="entry:agreed")]]))

async def entry_agreed_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    mark_entry(uid)
    await show_gate(query.message, uid)

async def show_gate(msg, uid):
    keyboard = [[InlineKeyboardButton(f"Join {name}", url=url)] for name, url in SOFT_GATE]
    keyboard.append([InlineKeyboardButton("I Have Joined All ENTER", callback_data="entry:gate_done")])
    await msg.reply_text(
        "LAST STEP\n\nJoin all Parish 14 channels to enter the platform.\n\nThis grows the nation and unlocks your full access.",
        reply_markup=InlineKeyboardMarkup(keyboard))

async def entry_gate_done_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    uid = query.from_user.id
    name = query.from_user.username or query.from_user.first_name or str(uid)
    mark_gate(uid)
    await welcome_inside(query, uid, name)

async def welcome_inside(query, uid, name):
    from config import get_station_rank, t
    lang = get_user_lang(uid)
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT points, tier FROM users WHERE telegram_id=%s", (uid,))
        row = cur.fetchone()
    finally:
        release_db(conn)
    pts = row[0] if row else 0
    tier = row[1] if row else "Fan"
    await query.message.reply_text(
        f"{t(lang, 'welcome_inside')}\n\nNation Tier:  {tier}\nStation Rank: {get_station_rank(pts)}\nMiserCoins:   {pts:,}\n\nThe platform is yours.",
        reply_markup=main_menu)
    await query.message.reply_text("SELECT YOUR PANEL",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("MUSIC SYSTEM", callback_data="panel:music")],
            [InlineKeyboardButton("STORE", callback_data="panel:store_main")],
            [InlineKeyboardButton("COMMUNITY", callback_data="panel:community")],
            [InlineKeyboardButton("FAN ECONOMY", callback_data="panel:economy")],
            [InlineKeyboardButton("SOCIAL ACCESS", callback_data="panel:social")],
        ]))

async def language_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    from config import t
    await update.message.reply_text(t(get_user_lang(uid), "select_lang"), reply_markup=lang_kb())

async def lang_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    try:
        lang = query.data.split(":")[1]
    except: return
    from config import SUPPORTED_LANGUAGES, t
    if lang not in SUPPORTED_LANGUAGES: return
    uid = query.from_user.id
    set_user_lang(uid, lang)
    await query.message.reply_text(f"{SUPPORTED_LANGUAGES[lang]} {t(lang, 'lang_saved')}")

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    context.user_data.clear()
    await update.message.reply_text("Cancelled.", reply_markup=main_menu)

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Main Menu", reply_markup=main_menu)
