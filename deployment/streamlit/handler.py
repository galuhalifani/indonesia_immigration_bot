import re
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from .text import question_keywords
from langdetect import detect
from deep_translator import GoogleTranslator

# Load Environment Variables
load_dotenv()
MONGODB_URI = os.environ.get("MONGO_URI")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

def init_mongodb():
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        return client
    except Exception as e:
        error_msg = f"⚠️ Failed connecting to database: {str(e)}"
        return error_msg

client = init_mongodb()
if client:
    db = client['instant_bot']
    collection = db['instant']
    feedback_collection = db['feedback']
    user_collection = db['user']
    web_counter_collection = db['web_counter']
else:
    collection = None
    feedback_collection = None
    user_collection = None
    web_counter_collection = None

FEEDBACK_KEYWORDS = ['Feedback', 'feedback', 'Feedback', 'Feedback?', 'feedback?', 'feedback!', 'not helpful', 'not helpful', 'not helpful?', 'not helpful?', 'not helpful!', 'helpful', 'helpful?', 'helpful!', "'helpful'", "'not helpful", "'feedback'", "membantu", "tidak membantu"]

def normalize(text):
    return re.sub(r'[^\w\s]', '', text).strip().lower()

def is_feedback_message(text: str) -> bool:
    cleaned = normalize(text)
    # all_feedback_keywords = translate_list(text, FEEDBACK_KEYWORDS)
    return any(cleaned.startswith(keyword) for keyword in FEEDBACK_KEYWORDS)

def extract_feedback_content(raw_message: str) -> dict:
    cleaned = normalize(raw_message)

    # feedback = GoogleTranslator(source='auto', target='en').translate(cleaned) if detect(cleaned) != 'en' else cleaned
    for keyword in FEEDBACK_KEYWORDS:
        if cleaned.startswith(keyword):
            remaining = cleaned[len(keyword):].strip()
            return {"feedback": keyword, "comment": remaining}
        
    return {"feedback": None, "comment": cleaned}

def save_feedback(feedback_obj: dict, last_qna: dict):
    feedback_data = {
        "feedback": feedback_obj["feedback"],
        "comment": feedback_obj["comment"],
        "question": last_qna.get("question"),
        "answer": last_qna.get("answer"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    try:
        feedback_collection.insert_one(feedback_data)
        return "Thank you for your feedback! We have recorded it successfully"
    except Exception as e:
        return f"An error occured when saving feedback: {str(e)}"

last_qna_map = {}

def store_last_qna(user_id, question, answer):
    last_qna_map[user_id] = {"question": question, "answer": answer}
    last_qna_map["anonymous"] = {"question": question, "answer": answer}

def get_last_question(user_id="anonymous"):
    return last_qna_map.get(user_id, {}).get("question", "")

def get_last_answer(user_id="anonymous"):
    return last_qna_map.get(user_id, {}).get("answer", "")

def check_question_feedback(query, user_id="anonymous"):
    feedback_obj = None
    last_qna = {"question": None, "answer": None}   

    if is_feedback_message(query):
        feedback_obj = extract_feedback_content(query)
        last_qna = {
            "question": get_last_question(user_id),
            "answer": get_last_answer(user_id),
        }
        return {"is_feedback": True, "query": query, "feedback_obj": feedback_obj, "last_qna": last_qna}
    else:
        return {"is_feedback": False, "query": query, "feedback_obj": feedback_obj, "last_qna": last_qna}
    
def check_user(user_id):
    daily_limit = 10
    user_details = user_collection.find_one({"user_id": user_id})

    if user_details:
        last_chat = user_details.get("last_chat", datetime.now(timezone.utc))
        balance = user_details.get("chat_balance", daily_limit)
        userType = user_details.get("type", 'regular')

        if last_chat.tzinfo is None:
            last_chat = last_chat.replace(tzinfo=timezone.utc)

        print(f'########## checkin user: {user_id}, last chat: {last_chat}, balance: {balance}')

        time_since_last_chat = last_chat - datetime.now(timezone.utc)
        print(f'########## time_since_last_chat: {time_since_last_chat}')

        if time_since_last_chat > timedelta(days=1) :
            # restore balance
            print("########## restoring balance")
            balance = daily_limit
            user_collection.update_one({"user_id": user_id}, {"$set": {"chat_balance": daily_limit}})

        return {"status": "existing", "user_id": user_id, "chat_balance": balance, "type": userType, "user_details": user_details}
    
    else:
        user_collection.insert_one({"user_id": user_id, "timestamp": datetime.now(timezone.utc).isoformat(), "chat_balance": daily_limit, "type": "regular"})
        print(f'########## creating new user: {user_id}, balance: {daily_limit}')
        return {"status": "new", "user_id": user_id, "user_details": user_details, "chat_balance": daily_limit, "type": "regular"}

def starts_with_question_keyword(query: str) -> bool:
    query_lower = query.lower().strip()
    question_keywords_translated = translate_list(query, question_keywords) if detect_language(query) != 'en' else question_keywords        
    return any(query_lower.startswith(keyword) for keyword in question_keywords_translated)

def translate_answer(question, answer):
    if len(question) < 4:
        return answer

    detected_lang_question = detect(question)
    detected_lang_answer = detect(answer)

    if detected_lang_question != detected_lang_answer:
        translated = GoogleTranslator(source='auto', target=detected_lang_question).translate(answer)
        return translated
    else:
        return answer

def translate_list(question, list_of_answers):
    if len(question) < 3:
        return list_of_answers

    detected_lang_question = detect(question)

    translated = []
    if detected_lang_question != 'en':
        for a in list_of_answers:
            answer = GoogleTranslator(source='auto', target=detected_lang_question).translate(a)
            translated.append(answer)
        return translated
    else:
        return list_of_answers
    
def detect_language(text):
    supported_languages = ['en', 'id', 'fr', 'de', 'th', 'es', 'it', 'pt', 'ja', 'ko', 'zh-cn', 'zh-tw', 'ru']
    try:
        lang = detect(text)
        if lang in supported_languages:
            return lang 
        else:
            return "en"
    except Exception as e:
        return "en"

def translate_text(lang, text):
    supported_languages = ['en', 'id', 'fr', 'de', 'th', 'es', 'it', 'pt', 'ja', 'ko', 'zh-cn', 'zh-tw', 'ru']
    try:
        if lang in supported_languages:
            translated = GoogleTranslator(source='auto', target=lang).translate(text)
            return translated
        else:
            return text
    except Exception as e:
        return text

def split_message(text, max_length=1530):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

def deduct_chat_balance(user, user_id):
    if user:
        print(f'########## deduct_chat_balance: {user}, type: {user["type"]}, balance: {user["chat_balance"]}')
        if user["type"] == 'regular' and user["chat_balance"] > 0:
            user_collection.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"chat_balance": -1},
                    "$set": {"last_chat": datetime.now(timezone.utc)}
                }
            )
        
def check_user_balance(user):
    balance = user["chat_balance"]
    print(f'########## check_user_balance: {user}, type: {user["type"]}, balance: {balance}')
    if user["type"] == 'regular' and balance > 0:
        return True
    elif user["type"] == 'unlimited':
        return True
    else:
        return False
    
def add_question_ticker():
    try:
        web_counter_collection.update_one(
                {"type": "whatsapp"},
                {
                    "$inc": {"counter": +1},
                    "$set": {"timestamp": datetime.now(timezone.utc)}
                },
                upsert=True
            )
        return True
    except Exception as e:
        print("Error updating web counter:", e)
        return False