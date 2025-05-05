import streamlit as st

st.set_page_config(
    page_title="Instant - Indonesia Immigration Assistant",
    layout="centered",
    initial_sidebar_state="expanded"
)

from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from streamlit_option_menu import option_menu
import os
import re
from model import ask
from handler import save_feedback, translate_answer, check_question_feedback
from text import feedback_instr, no_affiliation, description, no_replacement_for_official_advice, source_of_answer_short, source_of_answer

primary_color = "#ffffff"
secondary_color = "#1E1E1E"
accent_color = "#FF6B35"
sidebar_bg = "#0e1117"
sidebar_text = "#ffffff"
selected_bg = "#f39c12"
selected_text = "#000000"
text_color = "#000000"
bg_color = "#252422"
header = "#1E1E1E"


# --- Custom CSS ---
st.markdown(f"""
<style>
    :root {{
        --primary: {primary_color};
        --secondary: {secondary_color};
        --accent: {accent_color};
        --text: {text_color};
    }}

    .stApp {{
        background-color: {bg_color};
    }}

    .header {{
        padding: 1rem 0;
        border-bottom: 2px solid var(--primary);
        margin-bottom: 2rem;
    }}

    .chat-container {{
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
    }}

    .user-message {{
        background: var(--secondary);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #DEE2E6;
    }}

    .assistant-message {{
        background: var(--primary);
        color: var(--text);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #DEE2E6;
    }}

    .pdf-ref {{
        color: var(--primary);
        border-left: 3px solid var(--accent);
        padding-left: 1rem;
        margin-top: 1rem;
    }}
</style>
""", unsafe_allow_html=True)

# Sidebar Menu
with st.sidebar:

    selected = option_menu(
        "Menu",
        ["Chatbot", "About", "Contact"],
        icons=["chat-dots", "info-circle", "telephone"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": sidebar_bg},
            "icon": {"color": accent_color, "font-size": "25px"},
            "nav-link": {"color": sidebar_text, "font-size": "16px", "text-align": "left", "margin":"0px"},
            "nav-link-selected": {"background-color": selected_bg, "color": selected_text},
        }
    )

def get_second_last_user_message():
    count = 0
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "user":
            count += 1
            if count == 2:
                return msg["content"]
    return None

def get_last_user_message():
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "user" and msg["type"] == "question":
            return msg["content"]
    return None

def get_last_assistant_message():
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "assistant" and msg["type"] == "answer":
            return msg["content"]
    return None
    
def normalize(text):
    return re.sub(r'[^\w\s]', '', text).strip().lower()

def separate_feedback_from_query(user_input, normalized_feedbacks):
    question = get_last_user_message()
    answer = get_last_assistant_message()
    cleaned_input = normalize(user_input)
    
    if cleaned_input in normalized_feedbacks:
        return {"type": "pure_feedback", "feedback": cleaned_input, "comment": "", "question": question, "answer": answer}
    
    # Try to match a known feedback prefix
    for keyword in normalized_feedbacks:
        if cleaned_input.startswith(keyword):
            remaining = cleaned_input[len(keyword):].strip()
            return {
                "type": "mixed",
                "feedback": keyword,
                "comment": remaining,
                "question": question, 
                "answer": answer
            }
    
    return {"type": "normal_query", "feedback": None, "comment": user_input, "question": question, "answer": answer}

def normalize(text):
    return re.sub(r'[^\w\s]', '', text).strip().lower()

# --- Streamlit UI ---
if selected == "Chatbot":
    with st.container():
        col1, col2 = st.columns([4, 4])
        with col1:
            st.image("instant.png", width=1000)
        with col2:
            st.markdown(f"""
            <div class="header">
                <h1 style="color: var(--primary); margin: 0;">Instant Bot</h1>
                <p style="color: #666; margin: 0;">{no_affiliation}</p>
                <br>
                <p style="color: #666; margin: 0;">{source_of_answer_short}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="chat-container">
        <div style="background: var(--secondary); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            🤖 You can ask in English or Indonesian. Ask anything related to:
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; margin-top: 0.5rem;">
                <span style="padding: 0.3rem; border-radius: 5px;">✔️ M-Paspor </span>
                <span style="padding: 0.3rem; border-radius: 5px;">✔️ Immigration Documents and Procedures </span>
                <span style="padding: 0.3rem; border-radius: 5px;">✔️ Indonesian Citizen Immigration Services </span>
                <span style="padding: 0.3rem; border-radius: 5px;">✔️ Foreign Citizen Immigration Services </span>
                <span style="padding: 0.3rem; border-radius: 5px;">✔️ Dual Citizenship for Children </span>
                <span style="padding: 0.3rem; border-radius: 5px;">✔️ Related Immigration Regulations </span>
            </div>
            <br>
            <span>{feedback_instr}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "type": "greeting",
            "content": "Hello! I'm Instant. How can I help you today?"
        }]

    # Display Chat History
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-container">
                <div class="user-message">
                    😀 <strong>You</strong><br>
                    {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-container">
                <div class="assistant-message">
                    🤖 <strong>Instant Bot</strong><br>
                    {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)

    query = st.chat_input("Ask your question here... (Example: How to apply for KITAS?)")

    if query:
        is_feedback = check_question_feedback(query, "anonymous")
        
        if is_feedback['is_feedback']:
            st.session_state.messages.append({"role": "user", "type": "feedback", "content": query})
            last_question = is_feedback['last_qna']['question']

            if not last_question:
                resp = "Sorry, you have not asked a question, or the session has been reset. Please ask a question first before providing feedback."
                mssg = translate_answer(query, resp)
                st.session_state.messages.append({
                    "role": "assistant",
                    "type": "warning",
                    "content": mssg
                })
                st.rerun()
            else:
                feedback_obj = is_feedback['feedback_obj']
                last_qna = is_feedback['last_qna']

                response = save_feedback(feedback_obj, last_qna)
                if "error" not in response:
                    st.toast("Feedback recorded!", icon="💾")

                st.markdown(response)

        else:
            st.session_state.messages.append({"role": "user", "type": "question", "content": query})

            with st.spinner("Looking up..."):
                answer = ask(query)

            st.session_state.messages.append({"role": "assistant", "type": "answer", "content": answer})  
            st.rerun()

elif selected == "About":
    st.markdown("### 📟 About Instant")
    st.markdown(f"""
    <div style='text-align: justify; font-size: 16px;'>
        {description}
        <br><br>
        <strong>Disclaimer:</strong> {no_affiliation}
        <br><br>
        <strong>Source of Information:</strong> {source_of_answer}
        <br><br>
        <strong>GitHub Repository:</strong> <a href="https://github.com/galuhalifani/indonesia_immigration_bot" target="_blank">Indonesia Immigration Bot</a>
    """, unsafe_allow_html=True)

elif selected == "Contact":
    st.markdown("### 📩 Contact Us")
    st.markdown("""
    **If you have further question, collaboration proposal, or any other inquiries related to this bot, please contact:**

    - 📧 [galuh.adika@gmail.com](mailto:galuh.adika@gmail.com)
    """)

# Footer
st.markdown(f"""
<div style="text-align: center; margin-top: 3rem; color: #666; font-size: 0.9rem;">
    <hr style="margin: 2rem 0;">
    <div style="display: flex; align-items: center; justify-content: center; gap: 0.5rem;">{no_replacement_for_official_advice}</div>
""", unsafe_allow_html=True)
