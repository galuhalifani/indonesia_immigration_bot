import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from flask import Flask, request, jsonify
from deployment.streamlit.model import ask, check_question_feedback
from deployment.streamlit.feedback_handler import save_feedback
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

    # Send an immediate placeholder response
    resp = MessagingResponse()
    resp.message("⏳ Hang tight, let me check that for you...")

    def process_response():
        result = check_question_feedback(incoming_msg, user_id)

        if result["is_feedback"]:
            last_qna = result["last_qna"]
            if not last_qna["question"]:
                reply = "Sorry, please ask a question first before providing feedback."
            else:
                reply = save_feedback(result["feedback_obj"], last_qna)
        else:
            reply = ask(incoming_msg, user_id)
            if not reply:
                reply = "Sorry, I missed that - can you please try asking again?"
    
     # Send the actual message via Twilio API
        client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        client.messages.create(
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=user_id,
            body=reply
        )

    Thread(target=process_response).start()
    return str(resp)

@app.route("/ask", methods=["POST"])
def handle_question():
    data = request.json
    query = data.get("query")
    user_id = data.get("user_id", "anonymous")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    result = check_question_feedback(query, user_id)
    
    if result["is_feedback"]:
        last_qna = result["last_qna"]
        if not last_qna["question"]:
            return jsonify({"message": "Sorry, please ask a question first before providing feedback."}), 400

        save_result = save_feedback(result["feedback_obj"], last_qna)
        return jsonify({"message": save_result}), 200

    answer = ask(query, user_id)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)