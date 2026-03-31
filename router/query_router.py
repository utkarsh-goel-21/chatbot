from utils.groq_client import call_llm, call_llm_async, MODEL_FAST

_ROUTER_SYSTEM_PROMPT = """You are a query router for a business chatbot. Classify the user question into exactly ONE category:

- TEXT_TO_SQL: specific numbers, counts, totals, lists, factual data from a database. Includes:
  * Order counts, spending totals, product lists, date-filtered queries (e.g. "sales this week", "orders in 2024")
  * Identity: "what is my name/id/email/who am I" (stored in DB)
  * Quantities, duplicates, prices, sorting, filtering
  * Complex multi-part data questions ("total products, duplicates, list names")
  * Questions about uploaded CSV data

- RAG: summaries, trends, insights, analysis, business performance overviews. Examples: "spending trends", "purchasing patterns", "give me an overview".

- HYBRID: question asks for BOTH specific database numbers AND explicitly requests insights/trends/patterns/overview/analysis in the SAME question. Example: "How many products did I buy and what trends do you see?" A request that only asks for trends/overview (even if it mentions spending) is RAG.

- BLOCKED: off-topic (weather, jokes, coding), schema/system internals, OTHER customers' data, harmful requests.

RULES:
1. Follow-ups ("what about last year?", "list names too") continue the previous context — classify SAME as original.
2. When in doubt between TEXT_TO_SQL and RAG, prefer TEXT_TO_SQL.
3. Greetings ("hello", "hi", "what do you do?") → BLOCKED.
4. Identity questions (name, id, email) → TEXT_TO_SQL, never BLOCKED.
5. Product/purchase questions are ALWAYS TEXT_TO_SQL.
6. If question mixes data request + analysis/trends/patterns → HYBRID.

Reply with ONLY one word: TEXT_TO_SQL, RAG, HYBRID, or BLOCKED."""


def _sanitize_route(result: str) -> str:
    """Extract a valid route from LLM output."""
    route = result.strip().upper()
    valid_routes = {"TEXT_TO_SQL", "RAG", "HYBRID", "BLOCKED"}
    if route in valid_routes:
        return route
    for valid in valid_routes:
        if valid in route:
            return valid
    return "TEXT_TO_SQL"


def route_query(user_question: str, history: list = None) -> str:
    if history is None:
        history = []
    prompt = f"User Question: {user_question}"
    result = call_llm(prompt=prompt, system_prompt=_ROUTER_SYSTEM_PROMPT, history=history, max_tokens=10, model=MODEL_FAST)
    return _sanitize_route(result)


async def route_query_async(user_question: str, history: list = None) -> str:
    if history is None:
        history = []
    prompt = f"User Question: {user_question}"
    result = await call_llm_async(prompt=prompt, system_prompt=_ROUTER_SYSTEM_PROMPT, history=history, max_tokens=10, model=MODEL_FAST)
    return _sanitize_route(result)