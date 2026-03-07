from utils.groq_client import call_llm

def route_query(user_question: str) -> str:
    system_prompt = """You are a query router for a business chatbot.
Your only job is to classify a user question into one of two categories:

- TEXT_TO_SQL: if the question asks for specific numbers, counts, totals, lists or any live data from the database. Examples: how many sales, total revenue, number of transactions, what products were sold.
- RAG: if the question asks for summaries, trends, insights, reports or general business performance. Examples: how is the business doing, what are payment trends, give me an overview.

Reply with ONLY one word: either TEXT_TO_SQL or RAG. Nothing else."""

    prompt = f"User Question: {user_question}"

    result = call_llm(prompt=prompt, system_prompt=system_prompt)
    return result.strip()