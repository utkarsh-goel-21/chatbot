from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import asyncio
import time
import requests
from router.query_router import route_query_async
from text_to_sql.sql_generator import generate_sql_async
from text_to_sql.sql_executor import execute_sql
from text_to_sql.db_setup import get_engine
from sqlalchemy import text
from rag.answer_generator import generate_rag_answer_async
from utils.groq_client import call_llm_async, warm_up_llm, MODEL_FAST, MODEL_SMART
from text_to_sql.db_setup import setup_database
from rag.generate_insights import generate_insight_documents
from rag.embedder import embed_documents, VECTOR_STORE
from text_to_sql.schema_loader import get_schema
import os

DEMO_CUSTOMERS = [11091, 11176]

def _insights_exist(customer_id: int) -> bool:
    """Check if insight documents already exist for a customer."""
    if VECTOR_STORE == "chromadb":
        try:
            from rag.embedder import _get_chroma_collection
            collection = _get_chroma_collection()
            results = collection.get(
                where={"user_id": customer_id},
                limit=1,
            )
            return len(results.get("ids", [])) > 0
        except Exception:
            return False
    else:
        engine = get_engine()
        with engine.connect() as conn:
            count = conn.execute(text(
                "SELECT COUNT(*) FROM rag_documents WHERE user_id = :cid"
            ), {"cid": customer_id}).scalar()
        return count > 0


def seed():
    setup_database()
    engine = get_engine()

    # Warm up the connection pool
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ DB connection pool warmed up.")

    for cid in DEMO_CUSTOMERS:
        if _insights_exist(cid):
            print(f"Insights already exist for customer {cid}. Skipping.")
            continue
        print(f"Generating insights for customer {cid}...")
        docs = generate_insight_documents(cid)
        embed_documents(docs)

    # Pre-cache schema
    print("Warming up schema cache...")
    get_schema()
    print("Schema cache ready.")

    # Warm up embedding model (Disabled to save RAM on Render Free Tier)
    # _warm_up_embeddings()

    # Warm up LLM connection
    warm_up_llm()
    print("🚀 All systems warmed up and ready!")


def _warm_up_embeddings():
    """Force the embedding model to load by running a dummy embed."""
    try:
        from rag.retriever import get_embedding
        get_embedding("warmup")
        print("✅ Embedding model warmed up.")
    except Exception as e:
        print(f"⚠️  Embedding warm-up failed (non-critical): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=seed, daemon=True).start()
    yield

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


# ── Answer formatting prompt ──
ANSWER_FORMAT_SYSTEM = """You are a helpful business assistant.
Convert raw database results into a clean, concise natural language answer.
Do not mention SQL, databases, or queries.

RULES:
1. Only answer based on the data provided. Never invent information.
2. If the result is [] or empty:
   - For time-based questions (this week, today, this month): say "The available data covers 2011-2014, so there are no records for that time period. Try asking about a different date range."
   - Otherwise: "I don't have any records matching that request."
3. When listing items, use names (not IDs). Format lists cleanly.
4. PRESERVE exact counts, totals, and business logic. If an item appears 8 times, say "8 times". Do not round money.
5. Accurately map the raw data to the user's question. If the data gives a total product count and a separate duplicate count, DO NOT mix them up or hallucinate one from the other.
6. For duplicate analysis: list each duplicate item with its exact count.
7. NEVER invent company names, vendor names, or external brand names unless they explicitly exist in the raw JSON data.
8. The authenticated user is the CUSTOMER. NEVER refer to the user as a salesperson or employee unless the query result explicitly maps them as such.
9. Be concise — 1-3 sentences for simple answers, short paragraphs for complex ones."""


async def _run_text_to_sql(question: str, user_id: int, history: list) -> tuple[str, bool]:
    """Run the TEXT_TO_SQL pipeline asynchronously. Returns (answer, success)."""
    error_feedback = None
    max_retries = 2

    for attempt in range(max_retries):
        try:
            sql = await generate_sql_async(question, user_id, history, error_feedback)
            if sql.strip() == "CANNOT_ANSWER":
                return ("I don't have enough data to answer that question. The available data doesn't include the information needed.", True)
            elif sql.strip() == "ACCESS_DENIED":
                return ("I'm sorry, but I can only show you your own data. I can't access information belonging to other customers.", True)
            else:
                # Split the generated SQL by semicolons to handle multi-part jagged requests
                sql_statements = [s.strip() for s in sql.split(";") if s.strip()]
                all_raw_results = []
                
                # Execute each statement
                for stmt in sql_statements:
                    try:
                        raw_result = await asyncio.to_thread(execute_sql, stmt)
                        all_raw_results.append(raw_result)
                    except Exception as parse_e:
                        print(f"Sub-statement failed: {parse_e} for SQL {stmt}")
                
                prompt = f"""User Question: {question}
Raw Database Results (from multiple queries): {all_raw_results}
Answer:"""
                answer = await call_llm_async(prompt=prompt, system_prompt=ANSWER_FORMAT_SYSTEM, history=history, max_tokens=512)
                return (answer, True)
        except Exception as e:
            print(f"TEXT_TO_SQL error on attempt {attempt+1}: {e}")
            error_feedback = str(e)

    return ("I couldn't process that query after multiple attempts. Try asking something more specific like 'How many orders do I have?' or 'What products have I purchased?'", False)


async def _run_rag(question: str, user_id: int, history: list) -> str:
    """Run the RAG pipeline asynchronously."""
    return await generate_rag_answer_async(question, user_id, history)


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
async def chat(request: ChatRequest):
    question = request.question
    user_id = request.user_id
    history = request.history

    # Step 1: Route the query (async)
    route = await route_query_async(question, history)

    if route == "TEXT_TO_SQL":
        answer, _ = await _run_text_to_sql(question, user_id, history)

    elif route == "RAG":
        answer = await _run_rag(question, user_id, history)

    elif route == "HYBRID":
        # Run BOTH pipelines in PARALLEL for speed
        sql_task = _run_text_to_sql(question, user_id, history)
        rag_task = _run_rag(question, user_id, history)

        (sql_result, rag_answer) = await asyncio.gather(sql_task, rag_task)
        sql_answer, sql_ok = sql_result

        # Combine both answers
        combine_system = """You are a helpful business assistant.
Combine these two partial answers into ONE coherent response.
Lead with concrete data, then add insights. Be concise and professional.
Do not mention combining sources."""

        combine_prompt = f"""User Question: {question}

Data Answer: {sql_answer}

Insight Answer: {rag_answer}

Combined Response:"""

        answer = await call_llm_async(prompt=combine_prompt, system_prompt=combine_system, max_tokens=512)

    elif route == "BLOCKED":
        system_prompt = """You are BizBot, a friendly AI assistant for a business data platform.
The user sent a conversational or off-topic message.
Respond politely and briefly (1-2 sentences).
If greeting: greet them back. If asking what you do: explain you analyze their sales data and documents.
If off-topic: say you're built for business analytics and guide them back."""

        prompt = f"User: {question}\nResponse:"
        answer = await call_llm_async(prompt=prompt, system_prompt=system_prompt, history=history, max_tokens=150, model=MODEL_FAST)

    else:
        answer = "I was unable to understand your question. Please try again."

    return {"question": question, "route": route, "answer": answer}

@app.get("/data-sources")
def get_data_sources(user_id: int):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            tables_res = conn.execute(text(
                "SELECT original_filename, table_name, created_at FROM uploaded_tables WHERE customer_id = :user_id ORDER BY created_at DESC"
            ), {"user_id": user_id}).fetchall()

            csv_list = [{"filename": r[0], "table_name": r[1], "type": "csv", "created_at": r[2].isoformat() if r[2] else None} for r in tables_res]

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