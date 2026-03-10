import chromadb
from chromadb.utils import embedding_functions

_chroma_client = None
_collection = None

def get_collection():
    global _chroma_client, _collection
    if _collection is None:
        ef = embedding_functions.DefaultEmbeddingFunction()
        _chroma_client = chromadb.PersistentClient(path="./chroma_db")
        _collection = _chroma_client.get_or_create_collection(
            name="business_docs",
            embedding_function=ef
        )
    return _collection

def embed_documents(documents: list[dict]):
    collection = get_collection()
    for doc in documents:
        collection.add(
            documents=[doc["text"]],
            ids=[doc["id"]]
        )
    print(f"Embedded {len(documents)} documents successfully.")