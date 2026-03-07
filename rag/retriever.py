from rag.embedder import model, collection

def retrieve_relevant_docs(user_question: str, n_results: int = 2) -> str:
    question_embedding = model.encode(user_question).tolist()

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=n_results
    )

    docs = results["documents"][0]
    return "\n\n".join(docs)