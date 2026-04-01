import os
from dotenv import load_dotenv
from fastembed import TextEmbedding

load_dotenv()

# ── Vector store detection ──
VECTOR_STORE = os.getenv("VECTOR_STORE", "pgvector").lower()  # "pgvector" or "chromadb"

# Load the local embedding model lazily to save memory on Render startup
_embedding_model = None

def get_embedding(text: str) -> list[float]:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # fastembed returns an iterator of numpy arrays
    vecs = list(_embedding_model.embed([text]))
    return vecs[0].tolist()


# ═══════════════════════════════════════════════════════════
#  ChromaDB helpers (lazy-loaded)
# ═══════════════════════════════════════════════════════════

_chroma_client = None
_chroma_collection = None

def _get_chroma_collection():
    """Lazy-load ChromaDB client and collection."""
    global _chroma_client, _chroma_collection
    if _chroma_collection is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path="./chroma_db")
        _chroma_collection = _chroma_client.get_or_create_collection(
            name="rag_documents",
            metadata={"hnsw:space": "cosine"}
        )
    return _chroma_collection


# ═══════════════════════════════════════════════════════════
#  Embed documents (auto-routes by VECTOR_STORE)
# ═══════════════════════════════════════════════════════════

def embed_documents(documents: list[dict]):
    if VECTOR_STORE == "chromadb":
        _embed_chromadb(documents)
    else:
        _embed_pgvector(documents)


def _embed_pgvector(documents: list[dict]):
    """Store embeddings in Supabase pgvector."""
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

    print(f"Embedded {len(documents)} documents into pgvector.")


def _embed_chromadb(documents: list[dict]):
    """Store embeddings in local ChromaDB."""
    collection = _get_chroma_collection()

    ids = []
    embeddings = []
    docs_text = []
    metadatas = []

    for doc in documents:
        embedding = get_embedding(doc["text"])
        ids.append(doc["id"])
        embeddings.append(embedding)
        docs_text.append(doc["text"])
        metadatas.append({"user_id": doc["user_id"]})

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=docs_text,
        metadatas=metadatas,
    )

    print(f"Embedded {len(documents)} documents into ChromaDB.")