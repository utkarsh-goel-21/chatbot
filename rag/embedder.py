import requests
import os
from dotenv import load_dotenv

load_dotenv()

HF_API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"

def get_embedding(text: str) -> list[float]:
    headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
    response = requests.post(HF_API_URL, headers=headers, json={"inputs": text})
    response.raise_for_status()
    return response.json()

def embed_documents(documents: list[dict]):
    from text_to_sql.db_setup import get_engine
    from sqlalchemy import text

    engine = get_engine()

    with engine.connect() as conn:
        for doc in documents:
            embedding = get_embedding(doc["text"])
            conn.execute(text("""
                INSERT INTO rag_documents (id, user_id, content, embedding)
                VALUES (:id, :user_id, :content, :embedding)
                ON CONFLICT (id) DO UPDATE
                SET content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding
            """), {
                "id": doc["id"],
                "user_id": doc["user_id"],
                "content": doc["text"],
                "embedding": str(embedding)
            })
        conn.commit()

    print(f"Embedded {len(documents)} documents into Supabase pgvector.")