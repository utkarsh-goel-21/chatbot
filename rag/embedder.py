import chromadb

_model = None
_chroma_client = None
_collection = None

def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def get_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path="./chroma_db")
        _collection = _chroma_client.get_or_create_collection(name="business_docs")
    return _collection

def embed_documents(documents: list[dict]):
    model = get_model()
    collection = get_collection()
    for doc in documents:
        embedding = model.encode(doc["text"]).tolist()
        collection.add(
            documents=[doc["text"]],
            embeddings=[embedding],
            ids=[doc["id"]]
        )
    print(f"Embedded {len(documents)} documents successfully.")