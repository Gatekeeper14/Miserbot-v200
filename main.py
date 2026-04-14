import os
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)

# =============================
# CONFIG
# =============================
BOT_TOKEN = os.getenv("ROYAL_BOT_TOKEN")

# Your real Stripe bundle link (can change later per product)
STRIPE_LINK = "https://buy.stripe.com/6oUeVf0Ml7Iv6Wg1PM5Rm00"

# Default pricing (display only; checkout uses STRIPE_LINK for now)
TRACK_PRICE = "$9.99"
BEAT_PRICE = "$500"

# =============================
# IN-MEMORY STORE (simple + stable)
# =============================
tracks = {}   # {"TRACK_001": {"name": "...", "file_id": "..."}}
beats = {}    # {"BEAT_101": {"name": "...", "file_id": "..."}}
drops = {}    # {"DROP_001": {"name": "...", "file_id": "..."}}
intros = {}   # {"INTRO_001": {"name": "...", "file_id": "..."}}

track_counter = 1
beat_counter = 101
drop_counter = 1
intro_counter = 1


# =============================
# UTIL
# =============================
def next_track_code():
    global track_counter
    code = f"TRACK_{track_counter:03d}"
    track_counter += 1
    return code


def next_beat_code():
    global beat_counter
    code = f"BEAT_{beat_counter:03d}"
    beat_counter += 1
    return code


def next_drop_code():
    global drop_counter
    code = f"DROP_{drop_counter:03d}"
    drop_counter += 1
    return code


def next_intro_code():
    global intro_counter
    code = f"INTRO_{intro_counter:03d}"
    intro_counter += 1
    return code


def classify_filename(name: str):
    """Return type based on filename prefix."""
    if not name:
        return None
    n = name.lower()
    if n.startswith("song_") or n.startswith("track_") or n.startswith("song"):
        return "song"
    if n.startswith("beat_") or "beat" in n:
        return "beat"
    if n.startswith("drop_") or "drop" in n:
        return "drop"
    if n.startswith("intro_") or "intro" in n:
        return "intro"
    return None


# =============================
# START / MENU
# =============================
def start(update, context):
    keyboard = [
        [InlineKeyboardButton("🎧 Catalog", callback_data="catalog")],
        [InlineKeyboardButton("🎹 Beat Store", callback_data="beats")],
        [InlineKeyboardButton("ℹ️ How to Buy", callback_data="how")],
    ]
    update.message.reply_text(
        "🚀 Miserbot AI Music Platform\n\n"
        "Preview tracks and purchase directly via Stripe.\n"
        "Artists upload: song_*, beat_*, drop_*, intro_*",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =============================
# CATALOG
# =============================
def show_catalog(update, context):
    query = update.callback_query
    query.answer()

    if not tracks:
        query.message.reply_text("No tracks available yet.")
        return

    text = "🎧 TRACK STORE\n\n"
    buttons = []

    for code, data in tracks.items():
        text += f"{code} — {data['name']} ({TRACK_PRICE})\n"
        buttons.append(
            [
                InlineKeyboardButton(
                    f"▶ Preview {code}", callback_data=f"preview|{code}"
                ),
                InlineKeyboardButton(
                    f"💳 Buy {code}", url=STRIPE_LINK
                ),
            ]
        )

    query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


def show_beats(update, context):
    query = update.callback_query
    query.answer()

    if not beats:
        query.message.reply_text("No beats available yet.")
        return

    text = "🎹 BEAT STORE\n\n"
    buttons = []

    for code, data in beats.items():
        text += f"{code} — {data['name']} ({BEAT_PRICE})\n"
        buttons.append(
            [
                InlineKeyboardButton(
                    f"▶ Preview {code}", callback_data=f"preview|{code}"
                ),
                InlineKeyboardButton(
                    f"💳 Buy {code}", url=STRIPE_LINK
                ),
            ]
        )

    query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


def how_to_buy(update, context):
    query = update.callback_query
    query.answer()
    query.message.reply_text(
        "1) Open Catalog or Beat Store\n"
        "2) Preview by number\n"
        "3) Tap Buy to checkout with Stripe\n\n"
        "Delivery happens instantly in the chat after payment (manual for now)."
    )


# =============================
# PREVIEW
# =============================
def preview_router(update, context):
    query = update.callback_query
    query.answer()

    _, code = query.data.split("|")

    if code.startswith("TRACK") and code in tracks:
        file_id = tracks[code]["file_id"]
        context.bot.send_audio(chat_id=query.message.chat_id, audio=file_id)
    elif code.startswith("BEAT") and code in beats:
        file_id = beats[code]["file_id"]
        context.bot.send_audio(chat_id=query.message.chat_id, audio=file_id)
    else:
        query.message.reply_text("Item not found.")


# =============================
# AUDIO CAPTURE
# =============================
def capture_upload(update, context):
    msg = update.message

    file_id = None
    file_name = None

    if msg.audio:
        file_id = msg.audio.file_id
        file_name = msg.audio.file_name
    elif msg.document:
        file_id = msg.document.file_id
        file_name = msg.document.file_name

    if not file_id:
        return

    file_type = classify_filename(file_name or "")

    print("UPLOAD:", file_name, file_id)

    if file_type == "song":
        code = next_track_code()
        tracks[code] = {"name": file_name, "file_id": file_id}
        msg.reply_text(f"Stored {code} — {file_name}")

    elif file_type == "beat":
        code = next_beat_code()
        beats[code] = {"name": file_name, "file_id": file_id}
        msg.reply_text(f"Stored {code} — {file_name}")

    elif file_type == "drop":
        code = next_drop_code()
        drops[code] = {"name": file_name, "file_id": file_id}
        msg.reply_text(f"Stored {code} — {file_name}")

    elif file_type == "intro":
        code = next_intro_code()
        intros[code] = {"name": file_name, "file_id": file_id}
        msg.reply_text(f"Stored {code} — {file_name}")

    else:
        msg.reply_text(
            "Unknown file type.\nUse prefixes: song_, beat_, drop_, intro_"
        )


# =============================
# ROUTER
# =============================
def router(update, context):
    data = update.callback_query.data

    if data == "catalog":
        show_catalog(update, context)
    elif data == "beats":
        show_beats(update, context)
    elif data == "how":
        how_to_buy(update, context)
    elif data.startswith("preview"):
        preview_router(update, context)


# =============================
# MAIN
# =============================
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(router))
    dp.add_handler(MessageHandler(Filters.audio | Filters.document, capture_upload))

    updater.bot.delete_webhook()
    print("🚀 Miserbot Engine Online")

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
