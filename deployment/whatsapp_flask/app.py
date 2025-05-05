import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from flask import Flask, request, jsonify
from deployment.streamlit.model import ask
from deployment.streamlit.handler import save_feedback, starts_with_question_keyword, check_question_feedback, check_user, translate_answer, detect_language
from deployment.streamlit.text import greeting
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from threading import Thread

app = Flask(__name__)

@app.route("/")
def root():
    return "Instant Immigration Bot API is running."

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get("Body", "").strip()
    user_id = request.values.get("From", "").strip()

    result = check_question_feedback(incoming_msg, user_id)
    last_qna = result["last_qna"]

    user = check_user(user_id)
    new_user = user['status'] == 'new'
    resp = MessagingResponse()

    if new_user:
        print(f"########### Send initial greetings: {user_id}")
        resp.message(greeting)

    if result["is_feedback"]:
        if not last_qna["question"]:
            reply = "Sorry, please ask a question first before providing feedback."
        else:
            reply = save_feedback(result["feedback_obj"], last_qna)
        
        print(f"########### Send feedback acknowledgement: {user_id}")
        return resp.message(reply)
    
    else:
        is_question = starts_with_question_keyword(incoming_msg)
        # send an immediate placeholder response
        if not last_qna["question"] and is_question:
            resp.message("⏳ let me check that for you...")

        def process_response():
            print(f"########### Running process_response for user: {user_id}")
            reply = ask(incoming_msg, user_id)
            if not reply:
                reply = "Sorry, I missed that - can you please try asking again?"
        
            # send the actual message via Twilio API
            client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
            client.messages.create(
                from_=os.getenv("TWILIO_PHONE_NUMBER"),
                to=user_id,
                body=reply
            )

        Thread(target=process_response).start()
        return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)