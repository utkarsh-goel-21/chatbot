from utils.groq_client import call_llm, call_llm_async
from rag.retriever import retrieve_relevant_docs

_RAG_SYSTEM_PROMPT = """You are a business analyst assistant.
You will be given business context documents about a specific customer and a user question.
Answer based on the documents provided.

RULES:
1. Be concise and professional. Use the actual numbers and facts from the documents.
2. If the documents contain information relevant to the question, use it — even if it doesn't match the exact wording of the question.
3. If the documents are truly about a completely different topic and contain NO relevant information, say: "I don't have enough detail on that in your current business documents. Try asking a data question like 'How many orders do I have?'"
4. NEVER invent names, numbers, IDs, customers, or external data. If the prompt asks about other people and they are not in the Business Context doc, explicitly say: "I only have access to your personal data."
5. If the documents mention the customer's name, use it naturally.
6. **STRICT TENANT ISOLATION**: Do not guess or fabricate information about other customers."""


def generate_rag_answer(user_question: str, user_id: int = 1, history: list = None) -> str:
    if history is None:
        history = []

    relevant_docs = retrieve_relevant_docs(user_question, user_id)

    prompt = f"""Business Context:
{relevant_docs}

User Question: {user_question}

Answer:"""

    return call_llm(prompt=prompt, system_prompt=_RAG_SYSTEM_PROMPT, history=history, max_tokens=512)


async def generate_rag_answer_async(user_question: str, user_id: int = 1, history: list = None) -> str:
    if history is None:
        history = []

    relevant_docs = retrieve_relevant_docs(user_question, user_id)

    prompt = f"""Business Context:
{relevant_docs}

User Question: {user_question}

Answer:"""

    return await call_llm_async(prompt=prompt, system_prompt=_RAG_SYSTEM_PROMPT, history=history, max_tokens=512)