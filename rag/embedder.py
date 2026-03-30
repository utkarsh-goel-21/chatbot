import os
from dotenv import load_dotenv
from fastembed import TextEmbedding

load_dotenv()

# Load the local model into memory exactly once per process
_embedding_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_embedding(text: str) -> list[float]:
    # fastembed returns an iterator of numpy arrays
    vecs = list(_embedding_model.embed([text]))
    return vecs[0].tolist()

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