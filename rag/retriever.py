import os
from dotenv import load_dotenv
from sqlalchemy import text
from text_to_sql.db_setup import get_engine
from rag.embedder import get_embedding, _get_chroma_collection

load_dotenv()

VECTOR_STORE = os.getenv("VECTOR_STORE", "pgvector").lower()


def retrieve_relevant_docs(user_question: str, user_id: int, n_results: int = 2) -> str:
    if VECTOR_STORE == "chromadb":
        return _retrieve_chromadb(user_question, user_id, n_results)
    else:
        return _retrieve_pgvector(user_question, user_id, n_results)


def _retrieve_pgvector(user_question: str, user_id: int, n_results: int) -> str:
    """Retrieve docs from Supabase pgvector using cosine similarity."""

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


def _retrieve_chromadb(user_question: str, user_id: int, n_results: int) -> str:
    """Retrieve docs from local ChromaDB using cosine similarity."""

    collection = _get_chroma_collection()
    question_embedding = get_embedding(user_question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=n_results,
        where={"user_id": user_id},
    )

    docs = results.get("documents", [[]])[0]
    return "\n\n".join(docs)