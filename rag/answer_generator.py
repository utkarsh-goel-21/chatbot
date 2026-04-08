from utils.groq_client import call_llm, call_llm_async, MODEL_FAST
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

_CONDENSE_SYSTEM_PROMPT = """Given a conversation history and a follow-up question, rephrase the follow-up question into a standalone search query.
Focus on extracting the CORE SUBJECT and USER INTENT. 
Use concise keywords. Do NOT output full sentences. Do NOT answer the question. 
ONLY output the refined search terms."""


def generate_rag_answer(user_question: str, user_id: int = 1, history: list = None) -> str:
    if history is None:
        history = []

    # 1. Condense query if history exists
    search_query = user_question
    if history:
        condense_prompt = f"Follow-up Question: {user_question}\nStandalone Search Query:"
        search_query = call_llm(
            prompt=condense_prompt,
            system_prompt=_CONDENSE_SYSTEM_PROMPT,
            history=history,
            max_tokens=64,
            model=MODEL_FAST
        ).strip().replace('"', '').replace("'", "")
        # print(f"🔍 RAG History Fix: '{user_question}' -> '{search_query}'")

    # 2. Retrieve using the condensed query
    relevant_docs = retrieve_relevant_docs(search_query, user_id, n_results=3)

    # 3. Generate final answer using original question + retrieved context
    prompt = f"""<CONTEXT>
{relevant_docs}
</CONTEXT>

User Question: {user_question}

Answer:"""

    return call_llm(prompt=prompt, system_prompt=_RAG_SYSTEM_PROMPT, history=history, max_tokens=512)


async def generate_rag_answer_async(user_question: str, user_id: int = 1, history: list = None) -> str:
    if history is None:
        history = []

    # 1. Condense query if history exists
    search_query = user_question
    if history:
        condense_prompt = f"Follow-up Question: {user_question}\nStandalone Search Query:"
        condensed = await call_llm_async(
            prompt=condense_prompt,
            system_prompt=_CONDENSE_SYSTEM_PROMPT,
            history=history,
            max_tokens=64,
            model=MODEL_FAST
        )
        search_query = condensed.strip().replace('"', '').replace("'", "")
        # print(f"🔍 RAG History Fix (Async): '{user_question}' -> '{search_query}'")

    # 2. Retrieve using the condensed query
    relevant_docs = retrieve_relevant_docs(search_query, user_id, n_results=3)

    # 3. Generate final answer using original question + retrieved context
    prompt = f"""<CONTEXT>
{relevant_docs}
</CONTEXT>

User Question: {user_question}

Answer:"""

    return await call_llm_async(prompt=prompt, system_prompt=_RAG_SYSTEM_PROMPT, history=history, max_tokens=512)