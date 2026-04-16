async def start(update, context):

    if INTRO_FILE_ID and INTRO_FILE_ID.strip() != "":
        try:
            await update.message.reply_voice(INTRO_FILE_ID)
        except:
            pass

    if FIRST_MESSAGE_FILE_ID and FIRST_MESSAGE_FILE_ID.strip() != "":
        try:
            await update.message.reply_voice(FIRST_MESSAGE_FILE_ID)
        except:
            pass

    await update.message.reply_text(
        "Welcome to Miserbot ecosystem."
    )
