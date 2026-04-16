import stripe
from config import STRIPE_SECRET_KEY

stripe.api_key=STRIPE_SECRET_KEY

def create_payment(amount,name):

    session=stripe.checkout.Session.create(

        payment_method_types=["card"],

        line_items=[{
            "price_data":{
                "currency":"usd",
                "product_data":{"name":name},
                "unit_amount":int(amount*100)
            },
            "quantity":1
        }],

        mode="payment",

        success_url="https://t.me/BazragodMiserbot_bot",
        cancel_url="https://t.me/BazragodMiserbot_bot"

    )

    return session.url
