@app.route("/")
def home():
    return "Miserbot running"


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    print("FULL UPDATE:")
    print(json.dumps(data, indent=2))

    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")

    text = message.get("text", "")

    print("USER MESSAGE:", text)

    if text == "/start":

        print("START COMMAND DETECTED")

        send_message(
            chat_id,
            "👑 Welcome to BAZRAGOD RADIO\n\nPress a button below.",
            main_menu()
        )

    elif text == "📻 BazraGod Radio":

        send_message(
            chat_id,
            "📻 Radio will begin playing here."
        )

    elif text == "🌍 Language":

        send_message(
            chat_id,
            "🌍 Language system coming soon."
        )

    elif text == "👤 My Profile":

        send_message(
            chat_id,
            "👤 Profile system coming soon."
        )

    else:

        send_message(
            chat_id,
            "Command received."
        )

    return {"ok": True}


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(host="0.0.0.0", port=port)
