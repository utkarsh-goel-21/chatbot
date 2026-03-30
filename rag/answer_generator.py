from utils.groq_client import call_llm
from rag.retriever import retrieve_relevant_docs

def generate_rag_answer(user_question: str, user_id: int = 1, history: list = None) -> str:
    if history is None:
        history = []

    relevant_docs = retrieve_relevant_docs(user_question, user_id)

    system_prompt = """You are a helpful business analyst assistant.
You will be given some true business context documents and a user question.
Your ONLY job is to extract the answer directly from these documents.
Be concise and professional. 
CRITICAL RULE: If the exact answer is NOT explicitly stated in the provided documents, you MUST reply with nothing else but: "I do not have access to that information based on your currently available documents." NEVER invent names, IDs, user lists, metrics, or external data."""

    prompt = f"""Business Context:
{relevant_docs}

User Question: {user_question}

Answer:"""

    return call_llm(prompt=prompt, system_prompt=system_prompt, history=history, max_tokens=512)