from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from router.query_router import route_query
from text_to_sql.sql_generator import generate_sql
from text_to_sql.sql_executor import execute_sql
from rag.answer_generator import generate_rag_answer
from utils.groq_client import call_llm

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str

@app.get("/")
def health_check():
    return {"status": "Business Chatbot is running"}

@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question
    route = route_query(question)

    if route == "TEXT_TO_SQL":
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

    elif route == "RAG":
        answer = generate_rag_answer(question)

    else:
        answer = "I was unable to understand your question. Please try again."

    return {
        "question": question,
        "route": route,
        "answer": answer
    }
