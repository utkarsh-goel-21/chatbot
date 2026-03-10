from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import time
import requests
from router.query_router import route_query
from text_to_sql.sql_generator import generate_sql
from text_to_sql.sql_executor import execute_sql
from rag.answer_generator import generate_rag_answer
from utils.groq_client import call_llm
from text_to_sql.db_setup import setup_database
from rag.embedder import embed_documents
from rag.sample_docs import sample_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://chatbot-flax-tau-13.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str

@app.on_event("startup")
def startup():
    def seed():
        setup_database()
        embed_documents(sample_documents)
    threading.Thread(target=seed, daemon=True).start()

@app.get("/")
def root():
    return {"status": "BizBot backend is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question
    route = route_query(question)

    if route == "TEXT_TO_SQL":
        try:
            sql = generate_sql(question)
            raw_result = execute_sql(sql)
            system_prompt = """You are a helpful business assistant.
You will be given a user question and raw database results.
Convert the raw results into a clean, concise natural language answer.
Do not mention SQL or databases in your response."""
            prompt = f"""User Question: {question}
Raw Database Result: {raw_result}
Answer:"""
            answer = call_llm(prompt=prompt, system_prompt=system_prompt)
        except Exception:
            answer = "I couldn't process that query. Try asking something more specific like 'How many products do we have?' or 'What transactions happened today?'"

    elif route == "RAG":
        answer = generate_rag_answer(question)

    else:
        answer = "I was unable to understand your question. Please try again."

    return {"question": question, "route": route, "answer": answer}

def keep_alive():
    while True:
        time.sleep(600)
        try:
            requests.get("https://bizbot-4vlu.onrender.com")
        except:
            pass

threading.Thread(target=keep_alive, daemon=True).start()
