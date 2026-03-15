from utils.groq_client import call_llm
from rag.retriever import retrieve_relevant_docs

def generate_rag_answer(user_question: str, user_id: int = 1, history: list = None) -> str:
    if history is None:
        history = []

    relevant_docs = retrieve_relevant_docs(user_question, user_id)

    system_prompt = """You are a helpful business analyst assistant.
You will be given some business context documents and a user question.
Answer the question using ONLY the information provided in the documents.
Be concise and professional. If the answer is not in the documents, say so clearly."""

    prompt = f"""Business Context:
{relevant_docs}

User Question: {user_question}

Answer:"""

    return call_llm(prompt=prompt, system_prompt=system_prompt, history=history)