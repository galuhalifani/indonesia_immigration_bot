import sys
import os
import re
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from datetime import datetime, timezone
from .prompt import PROFESSIONAL_PROMPT
from .handler import is_feedback_message, extract_feedback_content, OPENAI_KEY, collection, user_collection, store_last_qna

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