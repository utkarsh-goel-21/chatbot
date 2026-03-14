from utils.groq_client import call_llm
from text_to_sql.schema_loader import get_schema

def generate_sql(user_question: str, user_id: int) -> str:
    schema = get_schema()

    system_prompt = """You are an expert SQL generator.
You will be given a database schema, a user question, and a user_id.
Your job is to return ONLY a valid SQL query that answers the question.
IMPORTANT: Always filter queries using WHERE user_id = {user_id} to ensure
data privacy. Never return data for other users.
Do not explain anything. Do not add markdown. Just return the raw SQL query."""

    prompt = f"""Database Schema:
{schema}

User ID: {user_id}
User Question: {user_question}

SQL Query:"""

    sql = call_llm(prompt=prompt, system_prompt=system_prompt)
    return sql.strip()