from utils.groq_client import call_llm
from text_to_sql.schema_loader import get_schema

def generate_sql(user_question: str) -> str:
    schema = get_schema()

    system_prompt = """You are an expert SQL generator.
You will be given a database schema and a user question.
Your job is to return ONLY a valid SQL query that answers the question.
Do not explain anything. Do not add markdown. Just return the raw SQL query."""

    prompt = f"""Database Schema:
{schema}

User Question: {user_question}

SQL Query:"""

    sql = call_llm(prompt=prompt, system_prompt=system_prompt)
    return sql.strip()
