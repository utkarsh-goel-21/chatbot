import os
import requests
from sqlalchemy import text
from text_to_sql.db_setup import get_engine
from dotenv import load_dotenv

load_dotenv()

HF_API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"

def get_embedding(text_input: str) -> list[float]:
    headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
    response = requests.post(HF_API_URL, headers=headers, json={"inputs": text_input})
    response.raise_for_status()
    return response.json()

def retrieve_relevant_docs(user_question: str, user_id: int, n_results: int = 2) -> str:
    engine = get_engine()
    question_embedding = get_embedding(user_question)
    embedding_str = str(question_embedding)

    with engine.connect() as conn:
        results = conn.execute(text("""
            SELECT content
            FROM rag_documents
            WHERE user_id = :user_id
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :n
        """), {
            "user_id": user_id,
            "embedding": embedding_str,
            "n": n_results
        }).fetchall()

    docs = [r[0] for r in results]
    return "\n\n".join(docs)