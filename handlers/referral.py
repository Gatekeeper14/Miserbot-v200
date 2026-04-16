from services.referral_mining import generate_referral_link

async def invite(update,context):

    user=update.effective_user.id
    bot=context.bot.username

    link=generate_referral_link(user,bot)

    await update.message.reply_text(
        f"Invite friends:\n{link}"
    )
