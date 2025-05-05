
# Instant — Immigration Digital Assistant

Instant is a chatbot powered by a **Large Language Model (LLM)** using a **Retrieval-Augmented Generation (RAG)** approach to provide fast and contextual answers to questions about **immigration procedures in Indonesia**, including visas, residence permits, and general regulations based on publicly available information in [Indonesia immigration official website](https://www.imigrasi.go.id).

---

## Background

Indonesia's immigration processes are highly diverse and many still require ad-hoc assistance to questions related to passport or visa. This often leads to long wait times for support, user errors in applications, or missing documents during application. Instant aims to:

- Simplify access to information about Indonesian immigration services  
- Provide 24/7 assistance based on **official public documentation and FAQs**  
- Reduce the burden on customer service by answering repetitive questions  
- Enhance the experience for both local and foreign nationals applying for passport, visa, or other immigration related services

---

## Project Objectives

- Develop a chatbot that is **reliable, multilingual, and accessible**
- Deliver **accurate responses** to general immigration-related questions  
- Increase **clarity and confidence** in immigration self-service usage

---

## Dataset

- Sourced from [Imigrasi.go.id Official FAQs](https://www.imigrasi.go.id/faq/visa)
- Total: **~1,500 questions & answers**
- Collected through **web scraping** of multiple pages in the official website

---

## Method & Technology

- **LangChain** for implementing the RAG pipeline  
- **OpenAI GPT-4** as base LLMs  
- **MongoDB Atlas Vector Search** for document retrieval  
- **Streamlit** for web-based user interface  
- **Twilio WhatsApp API** for whatsapp-based conversational messaging  
- **Render.com** for backend API deployment

---

## File Explanation

| File                         | Description                                        |
|------------------------------|----------------------------------------------------|
| `model.py`                   | Core logic to retrieve, clean, and respond         |
| `feedback_handler.py`        | Logic to extract and save feedback from users      |
| `prompt.py`                  | Customized prompt template for immigration context |
| `app.py`                     | Flask app with `/whatsapp` endpoint                |
| `scraping.ipynb`             | Web scraping notebook for FAQs                     |
| `requirements.txt`           | Python dependencies for deployment                 |

---

## Features

- Fast retrieval of immigration-related FAQs and general topics from official immigration website  
- Multilingual capability (Bahasa Indonesia and English)
- Feeback loop for future fine-tuning: users can contribute feedback to the bot's response, of whether they find the response helpful or not helpful, followed by comments
- Memory retention available within session to enable follow-up questions by users based on their previous questions until the session closed, restarts, or after 24h of inactivity.

---

## Current Limitations

- The bot cannot **give case-specific advice** or tailored recommendations  
- Slight latency due to vector search + LLM generation  
- Reference links may occasionally be unavailable or too general

---

## Demo

Available via:
- 🌐 [Web UI](https://huggingface.co/spaces/galuhalifani/instant_chatbot)
- 📱 [WhatsApp Bot](https://wa.me/12344234277)

---

## Contact

For feedback or partnership:
- 📧 Galuh: galuh.adika@gmail.com