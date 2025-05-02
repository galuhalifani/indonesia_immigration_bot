from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from model import ask

import os

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    user_message = request.form.get("Body", "")
    print(f"Received from WhatsApp: {user_message}")

    try:
        response = ask(user_message)
    except Exception as e:
        print(f"Error: {e}")
        response = "⚠️ Maaf, terjadi kesalahan."

    twilio_response = MessagingResponse()
    twilio_response.message(response)
    return str(twilio_response)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)