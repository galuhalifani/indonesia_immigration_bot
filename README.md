
# Astrax — Assistant for Tax

Astrax is a chatbot powered by a **Large Language Model (LLM)** built using a **Retrieval-Augmented Generation (RAG)** approach to provide fast, accurate, and relevant answers to questions about **individual taxation in Indonesia**, especially related to DJP Online and annual tax filings (SPT Tahunan).

---

## Background

Although digital tax reporting systems have existed since the early 2000s, many users still face difficulties navigating the services or understanding regulations. This leads to heavy loads on customer service and long response times. Astrax aims to:

- Simplify the interaction between taxpayers and digital tax interfaces
- Provide 24/7 assistance based on DJP’s official FAQs
- Serve as a reliable source for any queries related to individual and digital taxation
- Improve the operational efficiency of digital tax systems

---

## Project Objectives

- Develop an LLM-based chatbot that is **reliable and accessible**
- Provide **accurate answers** to individual taxation-related questions
- Improve **user adoption and satisfaction** with digital tax systems

---

## Team Members

| Name                  | Role                 |
|-----------------------|----------------------|
| Galuh Alifani         | Data Analyst & PM    |
| Ade Indra Rukmana     | Data Engineer        |
| Juan Nembaopit        | Data Scientist       |
| Eldi M. Sunartadirja  | Data Scientist       |

---

## Dataset

- Sourced from [DJP Official FAQ](https://pajak.go.id/id/faq-page) and [Annual Report FAQ](https://pajak.go.id/en/node/34236)
- Total: **209 questions & answers**
- Collection method: a combination of **web scraping** and **manual gathering**

---

## Method & Technology

- **LangChain** for RAG pipeline
- **OpenAI GPT-3.5 and GPT-4** as base LLMs
- **MongoDB Atlas Vector Search** as the NoSQL vector database
- **Streamlit** for UI development
- **Hugging Face** for web deployment hosting

---

## File Explanation

| File                           | Description                                      |
|--------------------------------|--------------------------------------------------|
| `Optimized_RAG-gpt4.ipynb`     | RAG model implementation using GPT-4            |
| `RAG_gpt3.ipynb`               | RAG model implementation using GPT-3.5          |
| `EDA.ipynb`                    | Exploratory Data Analysis documentation         |
| `astrax-gpt-3.5-turbo.py`      | Deployment script for GPT-3.5 chatbot           |
| `astrax-gpt-4.py`              | Deployment script for GPT-4 chatbot             |
| `faq_combined.csv`             | Combined FAQ dataset (web scraping + manual)    |
| `faq_categorization.csv`       | Categorized FAQ dataset                         |
| `scrapping.ipynb`              | Web scraping documentation                      |

---

## Model Evaluation

| Model     | Strengths                                              | Weaknesses                                                 |
|-----------|--------------------------------------------------------|-------------------------------------------------------------|
| GPT-3.5   | Faster response time, able to reject out-of-context queries | Sometimes too brief, lacks context for short questions     |
| GPT-4     | More detailed answers, better contextualization for short questions, broader coverage | Slower response time (up to 20 seconds)                   |

---

## Current Limitations

- Model **lacks memory** across user sessions
- May answer tax-related questions outside of the FAQ if contextually related
- Response time can reach **15–20 seconds**
- No user feedback loop implemented yet

---

## Potential Improvements

- Implementing **session-based memory**
- Adding **feedback loop** for response evaluation
- Reducing latency with lighter models
- Expanding document coverage with more DJP FAQs
- Enforcing answers to be sourced **only from official documents**

---

## Demo

This chatbot is available as a [web app](https://huggingface.co/spaces/adeindrar/Astrax) and deployed on Hugging Face using Streamlit UI.

---

## Contact

For collaboration or feedback:
- 📧 Galuh: galuh.adika@gmail.com
- 📧 Ade: adeindrar@gmail.com
- 📧 Eldi: eldimuhamads@gmail.com
- 📧 Juan: juannembaopit13@gmail.com
