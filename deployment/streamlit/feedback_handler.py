import re
from datetime import datetime, timezone
from pymongo import MongoClient
import os
from dotenv import load_dotenv

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
