import os
from sqlalchemy import text
from text_to_sql.db_setup import get_engine
from dotenv import load_dotenv
from fastembed import TextEmbedding

load_dotenv()

_embedding_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_embedding(text_input: str) -> list[float]:
    vecs = list(_embedding_model.embed([text_input]))
    return vecs[0].tolist()

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