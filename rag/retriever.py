from rag.embedder import get_collection

def retrieve_relevant_docs(user_question: str, n_results: int = 2) -> str:
    collection = get_collection()
    results = collection.query(
        query_texts=[user_question],
        n_results=n_results
    )
    docs = results["documents"][0]
    return "\n\n".join(docs)
