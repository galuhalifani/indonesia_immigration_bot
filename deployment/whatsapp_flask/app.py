import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from flask import Flask, request, jsonify
from deployment.streamlit.model import ask
from deployment.streamlit.handler import save_feedback, starts_with_question_keyword, check_question_feedback, check_user, split_message, translate_text, deduct_chat_balance, check_user_balance, add_question_ticker
from deployment.streamlit.text import greeting
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from threading import Thread
from deep_translator import GoogleTranslator
from langdetect import detect

app = Flask(__name__)

@app.route("/")
def root():
    return "Instant Immigration Bot API is running."

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    try:
        incoming_msg = request.values.get("Body", "").strip()
        user_id = request.values.get("From", "").strip()
        print(f"########### Starting process: {incoming_msg}, {user_id}")

        result = check_question_feedback(incoming_msg, user_id)
        last_qna = result["last_qna"]

        resp = MessagingResponse()
        user = check_user(user_id)
        print(f"########### User extracted: {user}")
        new_user = user['status'] == 'new'

        lang = detect(incoming_msg)

        if new_user:
            print(f"########### Send initial greetings: {user_id}")
            translated_greeting = translate_text(lang, greeting)
            resp.message(translated_greeting)

        if len(incoming_msg) > 150:
            exceed_length_resp = "Sorry, your message is too long. Please shorten it to less than 150 characters."
            reply = translate_text(lang, exceed_length_resp)
            resp.message(reply)
            return str(resp)
        
        if result["is_feedback"]:
            if not last_qna["question"]:
                reply = "Sorry, please ask a question first before providing feedback."
            else:
                reply = save_feedback(result["feedback_obj"], last_qna)

            resp.message(reply)
            return str(resp)
        
        is_balance_available = check_user_balance(user)
        if not is_balance_available:
            reply = translate_text(lang, "Sorry, you have reached your daily conversation limit. You can start a new conversation tomorrow.")
            resp.message(reply)
            return str(resp)
        else:
            if len(incoming_msg) > 4:
                # send an immediate placeholder response
                if not last_qna["question"]:
                    message = translate_text(lang, 'let me check that for you...')
                    resp.message(f"⏳ {message}")

            def process_response():
                print(f"########### Running process_response for user: {user_id}")
                reply = ask(incoming_msg, user_id)
                
                if not reply:
                    reply = translate_text(lang, "Sorry, I missed that - can you please try asking again?")
            
                # send the actual message via Twilio API
                print(f"########### Sending message to user: {user_id}")
                client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
                if len(reply) > 1599:
                    for part in split_message(reply):
                        client.messages.create(
                            from_=os.getenv("TWILIO_PHONE_NUMBER"),
                            to=user_id,
                            body=part
                        )
                else:
                    client.messages.create(
                        from_=os.getenv("TWILIO_PHONE_NUMBER"),
                        to=user_id,
                        body=reply
                    )
                
                # deduct balance
                try:
                    print(f"########### Deducting balance for user: {user_id}")
                    deduct_chat_balance(user, user_id)
                except Exception as e:
                    print(f"Error deducting chat balance: {str(e)}")

                print(f"########### Refreshing web counter")
                add_question_ticker()

            print(f"########### Ending process for: {user_id}", flush=True)
            Thread(target=process_response).start()
            return str(resp)   
        
    except Exception as e:
        print(f"########### Error try except for user: {user_id}")
        import traceback
        traceback.print_exc()
        print("❌ Internal server error:")
        resp = MessagingResponse()
        resp.message(f"We are sorry, the bot is currently unavailable or under maintenance. Please try again later.")
        return str(resp)

@app.route("/sandbox", methods=["POST"])
def whatsapp_webhook_sandbox():
    incoming_msg = request.values.get("Body", "").strip()
    user_id = request.values.get("From", "").strip()

    result = check_question_feedback(incoming_msg, user_id)
    last_qna = result["last_qna"]

    resp = MessagingResponse()
    user = check_user(user_id)
    new_user = user['status'] == 'new'

    lang = detect(incoming_msg)

    if new_user:
        print(f"########### Send initial greetings: {user_id}")
        translated_greeting = translate_text(lang, greeting)
        resp.message(translated_greeting)

    if len(incoming_msg) > 150:
        exceed_length_resp = "Sorry, your message is too long. Please shorten it to less than 150 characters."
        reply = translate_text(lang, exceed_length_resp)
        resp.message(reply)
        return str(resp)
    
    if result["is_feedback"]:
        if not last_qna["question"]:
            reply = "Sorry, please ask a question first before providing feedback."
        else:
            reply = save_feedback(result["feedback_obj"], last_qna)

        resp.message(reply)
        return str(resp)
    
    is_balance_available = check_user_balance(user)
    if not is_balance_available:
        reply = translate_text(lang, "Sorry, you have reached your daily conversation limit. You can start a new conversation tomorrow.")
        resp.message(reply)
        return str(resp)
    else:
        if len(incoming_msg) > 4:
            # send an immediate placeholder response
            if not last_qna["question"]:
                message = translate_text(lang, 'let me check that for you...')
                resp.message(f"⏳ {message}")

        def process_response():
            print(f"########### Running process_response for user: {user_id}")
            reply = ask(incoming_msg, user_id)
            
            if not reply:
                reply = translate_text(lang, "Sorry, I missed that - can you please try asking again?")
        
            # send the actual message via Twilio API
            client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
            if len(reply) > 1599:
                for part in split_message(reply):
                    client.messages.create(
                        from_=os.getenv("TWILIO_PHONE_NUMBER_SANDBOX"),
                        to=user_id,
                        body=part
                    )
            else:
                client.messages.create(
                    from_=os.getenv("TWILIO_PHONE_NUMBER_SANDBOX"),
                    to=user_id,
                    body=reply
                )
            
            # deduct balance
            try:
                deduct_chat_balance(user['user_details'], user_id)
            except Exception as e:
                print(f"Error deducting chat balance: {str(e)}")

        Thread(target=process_response).start()
        return str(resp)
        
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)