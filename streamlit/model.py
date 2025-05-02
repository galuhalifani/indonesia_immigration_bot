import streamlit as st
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
from streamlit_option_menu import option_menu
import os
import re
from prompt import PROFESSIONAL_PROMPT
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from datetime import datetime, timezone

# Load Environment Variables
load_dotenv()
MONGODB_URI = os.environ.get("MONGO_URI")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize Embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENAI_KEY,
    dimensions=1536
)

@st.cache_resource
def init_memory():
    return ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key='answer')

# MongoDB Connection with Caching
@st.cache_resource
def init_mongodb():
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        return client['instant_bot']
    except Exception as e:
        st.error(f"⚠️ Failed connecting to database: {str(e)}")
        st.stop()

collection = init_mongodb()['instant']

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

@st.cache_resource
def create_conversational_chain():
    memory = init_memory()
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3, "score_threshold": 0.8}
    )

    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": PROFESSIONAL_PROMPT},
        return_source_documents=True
    )

qa = create_conversational_chain()

def clean_answer(raw_answer):
    formatted = re.sub(r'(\d+\.)\s', r'\n\1 ', raw_answer)
    cleaned = re.sub(r'[*_]{2}', '', formatted)
    return cleaned.strip()

def ask(query):
    try:
        # result = qa.invoke({"query": query})
        chat_history = st.session_state.get("chat_history", [])
        result = qa({"question": query, "chat_history": chat_history})
        st.session_state.chat_history = result["chat_history"]

        if not result['source_documents']:
            return f"Sorry, no relevant information found on the question asked. Please contact immigration customer service through https://www.imigrasi.go.id/hubungi."
        else:
            raw_answer = result["answer"]
            answer = clean_answer(raw_answer)

        return answer

    except Exception as e:
        st.warning(f"⚠️ Error: {str(e)}")
        error_msg = f"""
        <div class="assistant-message">
            ⚠️ An error occured<br>
            An error occured, please try again or contact us:<br>
            • Email: galuh.adika@gmail.com<br>
            error: {str(e)}<br>
        </div> 
        """
        return error_msg

def save_feedback(object):
    feedback_data = object.copy()
    feedback_data['timestamp'] = st.session_state.get("time") or datetime.now(timezone.utc).isoformat()

    try:
        feedback_collection = init_mongodb()['feedback']
        feedback_collection.insert_one(feedback_data)
        st.toast("Feedback recorded!", icon="💾")
        return "Thank you for your feedback! We have recorded it successfully"
    except Exception as e:
        st.warning(f"⚠️ Failed to save feedback: {str(e)}")
        return "Failed to save feedback, please try again later"