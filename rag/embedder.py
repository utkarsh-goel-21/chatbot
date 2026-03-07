import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="business_docs")

def embed_documents(documents: list[dict]):
    for doc in documents:
        embedding = model.encode(doc["text"]).tolist()
        collection.add(
            documents=[doc["text"]],
            embeddings=[embedding],
            ids=[doc["id"]]
        )
    print(f"Embedded {len(documents)} documents successfully.")