import sys
import os
import re
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from datetime import datetime, timezone
from .prompt import PROFESSIONAL_PROMPT
from .feedback_handler import is_feedback_message, extract_feedback_content, OPENAI_KEY, collection, user_collection

# Initialize Embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENAI_KEY,
    dimensions=1536
)

def init_memory():
    return ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key='answer')

memory_store = {}

def get_user_memory(user_id: str) -> ConversationBufferMemory:
    if user_id not in memory_store:
        memory_store[user_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
    return memory_store[user_id]

# Vector Store Configuration
vector_store = MongoDBAtlasVectorSearch(
    collection=collection,
    embedding=embeddings,
    index_name='vector_index',
    text_key="text"
)

# Model Configuration
llm = ChatOpenAI(
    model_name="gpt-4",
    openai_api_key=OPENAI_KEY,
    temperature=0,
    max_tokens=800,
)

# @st.cache_resource
qa_chains = {}

def create_conversational_chain(user_id: None):
    memory = get_user_memory(user_id) if user_id else init_memory()

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3, "score_threshold": 0.8}
    )

    qa_chains[user_id] = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": PROFESSIONAL_PROMPT},
        return_source_documents=True
    )

    return qa_chains[user_id]

def clean_answer(raw_answer):
    formatted = re.sub(r'(\d+\.)\s', r'\n\1 ', raw_answer)
    cleaned = re.sub(r'[*_]{2}', '', formatted)
    reference_checked = re.sub(r'^.*Read more at(?!.*(https?://|www\.)).*$', '', cleaned, flags=re.MULTILINE)
    return reference_checked.strip()

last_qna_map = {}

def store_last_qna(user_id, question, answer):
    last_qna_map[user_id] = {"question": question, "answer": answer}
    last_qna_map["anonymous"] = {"question": question, "answer": answer}

def get_last_question(user_id="anonymous"):
    return last_qna_map.get(user_id, {}).get("question", "")

def get_last_answer(user_id="anonymous"):
    return last_qna_map.get(user_id, {}).get("answer", "")
    
def ask(query, user_id="anonymous"):
    try:
        if user_id != "anonymous":
            qa = create_conversational_chain(user_id)
        else:
            qa = create_conversational_chain("anonymous")

        result = qa({"question": query})

        if not result['source_documents']:
            return f"Sorry, no relevant information found on the question asked. Please contact immigration customer service through https://www.imigrasi.go.id/hubungi."
        else:
            answer = clean_answer(result["answer"])
            store_last_qna(user_id, query, answer)

        return answer

    except Exception as e:
        error_msg = f"""
        <div class="assistant-message">
            ⚠️ An error occured<br>
            An error occured, please try again or contact us:<br>
            • Email: galuh.adika@gmail.com<br>
            error: {str(e)}<br>
        </div> 
        """
        return error_msg

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