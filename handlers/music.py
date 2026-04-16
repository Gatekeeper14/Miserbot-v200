from services.music_catalog import get_all_songs


async def music(update, context):

    songs = get_all_songs()

    if not songs:

        await update.message.reply_text(
            "🎧 Music Hub\n\n"
            "Catalog is currently empty.\n"
            "New releases coming soon."
        )
        return

    msg = "🎧 Music Hub\n\n"

    for song in songs:

        msg += f"{song[1]} — {song[2]}  (${song[3]})\n"

    await update.message.reply_text(msg)
