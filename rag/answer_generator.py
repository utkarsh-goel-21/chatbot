from utils.groq_client import call_llm, call_llm_async
from rag.retriever import retrieve_relevant_docs

_RAG_SYSTEM_PROMPT = """You are a business analyst assistant.
You will be given business context documents about a specific customer and a user question.
Answer based on the documents provided.

RULES:
1. You may ONLY use facts, names, or numbers that appear explicitly within the <CONTEXT> tags. Do not pull on general knowledge.
2. If the user asks about other people, customers, or overall platform statistics not explicitly listed in <CONTEXT>, you MUST reply exactly: "I only have access to your personal data."
3. Do not invent filler names (e.g., Emily, Michael, Sarah) or placeholder data.
4. If the <CONTEXT> has no relevant information for a valid business query, say: "I don't have enough detail on that in your current business documents."
5. **STRICT ISOLATION**: Do not attempt to guess or fabricate generalized lists. Only report what is literally in the <CONTEXT>."""


def generate_rag_answer(user_question: str, user_id: int = 1, history: list = None) -> str:
    if history is None:
        history = []

    relevant_docs = retrieve_relevant_docs(user_question, user_id)

    prompt = f"""<CONTEXT>
{relevant_docs}
</CONTEXT>

User Question: {user_question}

Answer:"""

    return call_llm(prompt=prompt, system_prompt=_RAG_SYSTEM_PROMPT, history=history, max_tokens=512)


async def generate_rag_answer_async(user_question: str, user_id: int = 1, history: list = None) -> str:
    if history is None:
        history = []

    relevant_docs = retrieve_relevant_docs(user_question, user_id)

    prompt = f"""<CONTEXT>
{relevant_docs}
</CONTEXT>

User Question: {user_question}

Answer:"""

    return await call_llm_async(prompt=prompt, system_prompt=_RAG_SYSTEM_PROMPT, history=history, max_tokens=512)