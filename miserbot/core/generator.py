try:
    import stripe as stripe_lib
    STRIPE_OK = True
except:
    STRIPE_OK = False

from config import STRIPE_SECRET_KEY, BOT_USERNAME
from database import get_db, release_db

if STRIPE_OK and STRIPE_SECRET_KEY:
    stripe_lib.api_key = STRIPE_SECRET_KEY

def create_stripe_checkout(uid, username, product_type, amount_usd, product_name, product_id=""):
    if not STRIPE_OK or not STRIPE_SECRET_KEY:
        return None
    try:
        session = stripe_lib.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": product_name},
                    "unit_amount": int(amount_usd * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"https://t.me/{BOT_USERNAME}",
            cancel_url=f"https://t.me/{BOT_USERNAME}",
            metadata={
                "telegram_id": str(uid),
                "username": username or "",
                "product_type": product_type,
                "product_id": product_id,
            },
        )
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO stripe_sessions (telegram_id, session_id, product_type, product_id, amount) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (session_id) DO NOTHING",
                (uid, session.id, product_type, product_id, int(amount_usd))
            )
            conn.commit()
        finally:
            release_db(conn)
        return session.url
    except Exception as e:
        print(f"Stripe error: {e}")
        return None

async def process_stripe_event(session_data, bot):
    from config import BOOKING_EMAIL, OWNER_ID
    from core.delivery import (
        deliver_single_song, deliver_cart_album, deliver_vault_single,
        deliver_vault_superfan, deliver_supporter, deliver_service
    )
    from services.economy import award_points

    uid = int(session_data.get("metadata", {}).get("telegram_id", 0))
    product_type = session_data.get("metadata", {}).get("product_type", "")
    product_id = session_data.get("metadata", {}).get("product_id", "")
    session_id = session_data.get("id", "")
    username = session_data.get("metadata", {}).get("username", "fan")

    if not uid:
        return

    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE stripe_sessions SET status='completed' WHERE session_id=%s", (session_id,))
        conn.commit()
    finally:
        release_db(conn)

    try:
        if product_type == "single_song":
            song_id = int(product_id) if product_id else 0
            if song_id:
                await deliver_single_song(bot, uid, song_id, username)
                award_points(uid, "download_purchase", username)

        elif product_type == "cart_album":
            count = await deliver_cart_album(bot, uid, username)
            if count:
                award_points(uid, "download_purchase", username)

        elif product_type == "vault_single":
            await deliver_vault_single(bot, uid)

        elif product_type == "vault_superfan":
            await deliver_vault_superfan(bot, uid, username, OWNER_ID)

        elif product_type == "supporter":
            await deliver_supporter(bot, uid, username)
            award_points(uid, "supporter_sub", username)

        elif product_type in ("service", "booking", "ladies_hub"):
            service_name = product_id.replace("_", " ").title()
            await deliver_service(bot, uid, username, service_name, BOOKING_EMAIL, OWNER_ID)

        elif product_type == "donation":
            amount = session_data.get("amount_total", 0) / 100
            await bot.send_message(uid, f"DONATION RECEIVED\n\n${amount:.2f} supports independent music directly.\nBAZRAGOD thanks you.\n\nParish 14 Nation.")
            award_points(uid, "charity", username)

    except Exception as e:
        print(f"Stripe delivery error: {e}")
