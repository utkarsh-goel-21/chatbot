import re
from utils.groq_client import call_llm
from text_to_sql.schema_loader import get_schema


def _validate_sql(sql: str, customer_id: int) -> str | None:
    """
    Validate generated SQL for tenant isolation.
    Returns None if valid, or an error string if invalid.
    """
    sql_upper = sql.upper()

    # Block destructive statements
    if any(kw in sql_upper for kw in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]):
        return "ACCESS_DENIED"

    # Check if query touches customer-scoped tables without filtering
    customer_tables = ["salesorderheader", "customer"]
    touches_customer_table = any(t in sql.lower() for t in customer_tables)

    if touches_customer_table:
        # Must contain customerid = <correct id>
        if str(customer_id) not in sql:
            return "ACCESS_DENIED"

        # Check for other customerid literals (cross-tenant attempt)
        # Find all integers after "customerid" patterns
        id_matches = re.findall(r"customerid\s*=\s*(\d+)", sql, re.IGNORECASE)
        for match in id_matches:
            if int(match) != customer_id:
                return "ACCESS_DENIED"

    return None


def generate_sql(user_question: str, user_id: int, history: list = None) -> str:
    schema = get_schema(user_id)

    system_prompt = f"""You are an expert SQL generator for a PostgreSQL database (AdventureWorks).
You will be given a database schema, a user question, and a customer ID.
You may also receive conversation history to understand context for follow-up questions (e.g., "what about last year?", "also tell the quantity").
Your job is to return ONLY a valid SQL query that answers the question.

CRITICAL RULES:
1. Always filter by customerid = {user_id} when querying sales.salesorderheader or sales.customer. This ensures data privacy — never return data for other customers.
2. Never use SELECT *. Always select only the specific columns needed. For counting use SELECT COUNT(*).
3. Use fully qualified table names with schema prefix (e.g. sales.salesorderheader, person.person, production.product).
4. When joining customer info, use: sales.customer.personid = person.person.businessentityid
5. When joining order details, use: sales.salesorderheader.salesorderid = sales.salesorderdetail.salesorderid
6. When joining products, use: sales.salesorderdetail.productid = production.product.productid
7. If the question asks for something that cannot be determined from the available columns, return exactly: CANNOT_ANSWER

Do not explain anything. Do not add markdown. Just return the raw SQL query."""

    history_text = ""
    if history:
        history_text = "Recent Conversation Context:\n"
        for msg in history[-6:]:
            role_prefix = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role_prefix}: {msg['content']}\n"
        history_text += "\n"

    prompt = f"""Database Schema:
{schema}

Customer ID: {user_id}
{history_text}User Question: {user_question}

SQL Query:"""

    sql = call_llm(prompt=prompt, system_prompt=system_prompt)
    sql = sql.strip()

    # Strip markdown fences if LLM wraps the SQL
    if sql.startswith("```"):
        sql = re.sub(r"^```(?:sql)?\s*", "", sql)
        sql = re.sub(r"\s*```$", "", sql)

    if sql == "CANNOT_ANSWER":
        return sql

    # Validate tenant isolation
    violation = _validate_sql(sql, user_id)
    if violation:
        return "ACCESS_DENIED"

    return sql