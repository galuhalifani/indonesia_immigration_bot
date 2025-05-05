import re
from datetime import datetime, timezone
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from .text import question_keywords

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
else:
    collection = None
    feedback_collection = None

FEEDBACK_KEYWORDS = ['Feedback', 'feedback', 'Feedback', 'Feedback?', 'feedback?', 'feedback!', 'not helpful', 'not helpful', 'not helpful?', 'not helpful?', 'not helpful!', 'helpful', 'helpful?', 'helpful!', "'helpful'", "'not helpful", "'feedback'"]

def normalize(text):
    return re.sub(r'[^\w\s]', '', text).strip().lower()

def is_feedback_message(text: str) -> bool:
    cleaned = normalize(text)
    return any(cleaned.startswith(keyword) for keyword in FEEDBACK_KEYWORDS)

def extract_feedback_content(raw_message: str) -> dict:
    cleaned = normalize(raw_message)

    for keyword in FEEDBACK_KEYWORDS:
        if cleaned.startswith(keyword):
            remaining = cleaned[len(keyword):].strip()
            return {"feedback": keyword, "comment": remaining}
        
    return {"feedback": None, "comment": raw_message}

def save_feedback(feedback_obj: dict, last_qna: dict) -> str:
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
    user_details = user_collection.find_one({"user_id": user_id})
    if user_details:
        return {"status": "existing", "user_id": user_id}
    else:
        user_collection.insert_one({"user_id": user_id, "timestamp": datetime.now(timezone.utc).isoformat()})
        return {"status": "new", "user_id": user_id}

def starts_with_question_keyword(query: str) -> bool:
    query_lower = query.lower().strip()
    return any(query_lower.startswith(keyword) for keyword in question_keywords)
