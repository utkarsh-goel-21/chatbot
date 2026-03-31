from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import time
import requests
from router.query_router import route_query
from text_to_sql.sql_generator import generate_sql
from text_to_sql.sql_executor import execute_sql
from text_to_sql.db_setup import get_engine
from sqlalchemy import text
from rag.answer_generator import generate_rag_answer
from utils.groq_client import call_llm
from text_to_sql.db_setup import setup_database
from rag.generate_insights import generate_insight_documents
from rag.embedder import embed_documents
from text_to_sql.schema_loader import get_schema

DEMO_CUSTOMERS = [11091, 11176]

def seed():
    setup_database()
    engine = get_engine()
    for cid in DEMO_CUSTOMERS:
        with engine.connect() as conn:
            count = conn.execute(text(
                "SELECT COUNT(*) FROM rag_documents WHERE user_id = :cid"
            ), {"cid": cid}).scalar()
        if count > 0:
            print(f"Insights already exist for customer {cid}. Skipping.")
            continue
        print(f"Generating insights for customer {cid}...")
        docs = generate_insight_documents(cid)
        embed_documents(docs)
    print("Warming up schema cache...")
    get_schema()
    print("Schema cache ready.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on startup
    threading.Thread(target=seed, daemon=True).start()
    yield
    # Runs on shutdown (nothing to clean up for now)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://chatbot-flax-tau-13.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str
    user_id: int = 11091
    history: list = []

@app.get("/")
def root():
    return {"status": "BizBot backend is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: int = Form(...)
):
    from utils.file_processor import process_csv, process_pdf, process_txt
    from text_to_sql.schema_loader import reset_schema_cache

    contents = await file.read()
    filename = file.filename.lower()

    try:
        if filename.endswith(".csv"):
            table_name = process_csv(contents, file.filename, user_id)
            reset_schema_cache()
            return {
                "status": "success",
                "type": "csv",
                "message": f"CSV uploaded successfully. You can now ask questions about {file.filename}.",
                "table_name": table_name
            }
        elif filename.endswith(".pdf"):
            chunks = process_pdf(contents, file.filename, user_id)
            return {
                "status": "success",
                "type": "pdf",
                "message": f"PDF uploaded successfully ({chunks} chunks indexed). You can now ask questions about {file.filename}.",
            }
        elif filename.endswith(".txt"):
            chunks = process_txt(contents, file.filename, user_id)
            return {
                "status": "success",
                "type": "txt",
                "message": f"Text file uploaded successfully ({chunks} chunks indexed). You can now ask questions about {file.filename}.",
            }
        else:
            return {"status": "error", "message": "Unsupported file type. Please upload CSV, PDF, or TXT files."}

    except Exception as e:
        print(f"Upload error: {e}")
        return {"status": "error", "message": f"Failed to process file: {str(e)}"}

@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question
    route = route_query(question, request.history)

    if route == "TEXT_TO_SQL":
        error_feedback = None
        max_retries = 2
        success = False
        
        for attempt in range(max_retries):
            try:
                sql = generate_sql(question, request.user_id, request.history, error_feedback)
                if sql.strip() == "CANNOT_ANSWER":
                    answer = "I don't have enough data to answer that question. The available data doesn't include the information needed to determine this."
                    success = True
                    break
                elif sql.strip() == "ACCESS_DENIED":
                    answer = "I'm sorry, but I can only show you your own data. I can't access information belonging to other customers."
                    success = True
                    break
                else:
                    raw_result = execute_sql(sql)
                    system_prompt = """You are a helpful business assistant.
You will be given a user question and raw database results.
Convert the raw results into a clean, concise natural language answer.
Do not mention SQL or databases in your response.
IMPORTANT: Only answer based on the data provided. Do not make assumptions.
CRITICAL: If the Raw Database Result is exactly `[]` or empty, you MUST reply: "I do not have any records matching your specific request." Do NOT extrapolate and say the user has "no purchase data" overall."""
                    prompt = f"""User Question: {question}
Raw Database Result: {raw_result}
Answer:"""
                    answer = call_llm(prompt=prompt, system_prompt=system_prompt, history=request.history, max_tokens=512)
                    success = True
                    break
            except Exception as e:
                print(f"TEXT_TO_SQL syntax/execution error on attempt {attempt+1}: {e}")
                error_feedback = str(e)
                
        if not success:
            answer = "I couldn't process that query after multiple attempts. Try asking something more specific like 'How many orders do I have?' or 'What products have I purchased?'"

    elif route == "RAG":
        answer = generate_rag_answer(question, request.user_id, request.history)

    elif route == "BLOCKED":
        system_prompt = """You are BizBot, a friendly and professional AI assistant for a business data platform.
The user just sent a conversational, generic, or off-topic message (e.g. "hello", "why", "who are you").
Respond politely and naturally, but keep your response very brief (1-2 sentences).
If they said hello, greet them. If they asked what you can do, explain you can parse their CSV sales data and PDF documents. 
If they asked a completely random or nonsense question, gently say you're an AI built specifically for business analytics and guide them back on track."""
        
        prompt = f"User Message: {question}\n\nYour Response:"
        answer = call_llm(prompt=prompt, system_prompt=system_prompt, history=request.history, max_tokens=150)

    else:
        answer = "I was unable to understand your question. Please try again."

    return {"question": question, "route": route, "answer": answer}

@app.get("/data-sources")
def get_data_sources(user_id: int):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Get uploaded CSV tables
            tables_res = conn.execute(text(
                "SELECT original_filename, table_name, created_at FROM uploaded_tables WHERE customer_id = :user_id ORDER BY created_at DESC"
            ), {"user_id": user_id}).fetchall()
            
            csv_list = [{"filename": r[0], "table_name": r[1], "type": "csv", "created_at": r[2].isoformat() if r[2] else None} for r in tables_res]

            # Get documents
            docs_res = conn.execute(text(
                "SELECT id FROM rag_documents WHERE user_id = :user_id"
            ), {"user_id": user_id}).fetchall()
            
            doc_names = set()
            for (doc_id,) in docs_res:
                parts = doc_id.split(f"customer_{user_id}_")
                if len(parts) > 1:
                    rest = parts[1]
                    idx = rest.rfind("_chunk_")
                    if idx != -1:
                        doc_names.add(rest[:idx])
            
            doc_list = [{"filename": name, "type": "pdf/txt"} for name in doc_names]
            
            return {"status": "success", "data": {"csvs": csv_list, "documents": doc_list}}
    except Exception as e:
        print(f"Error fetching data sources: {e}")
        return {"status": "error", "message": str(e)}

def keep_alive():
    while True:
        time.sleep(600)
        try:
            requests.get("https://bizbot-4vlu.onrender.com")
        except:
            pass

threading.Thread(target=keep_alive, daemon=True).start()