import re
import os
from utils.groq_client import call_llm, call_llm_async
from text_to_sql.schema_loader import get_schema

_LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

# Extra hints ONLY for small local models (Ollama) to prevent common mistakes.
# These are NOT added when using Groq (production) — the 70B model doesn't need them.
_OLLAMA_EXTRA_HINTS = """

CRITICAL TABLE-COLUMN MAPPING (do NOT mix these up):
- orderdate, shipdate, duedate, subtotal, totaldue, taxamt, freight, customerid → sales.salesorderheader
- orderqty, unitprice, unitpricediscount, productid, carriertrackingnumber → sales.salesorderdetail  
- salesorderid exists on BOTH tables (use it for JOINs)
- firstname, lastname, persontype → person.person (NOT sales.customer)
- name (product name), listprice, standardcost, color → production.product

COMMON JOIN PATTERNS:
- Customer orders: sales.customer c JOIN sales.salesorderheader soh ON c.customerid = soh.customerid
- Order items: sales.salesorderheader soh JOIN sales.salesorderdetail sod ON soh.salesorderid = sod.salesorderid
- Product info: sales.salesorderdetail sod JOIN production.product p ON sod.productid = p.productid
- Customer name: sales.customer c JOIN person.person p ON c.personid = p.businessentityid
- Product category: production.product p JOIN production.productsubcategory ps ON p.productsubcategoryid = ps.productsubcategoryid JOIN production.productcategory pc ON ps.productcategoryid = pc.productcategoryid
"""


def _validate_sql(sql: str, customer_id: int) -> str | None:
    """
    Validate generated SQL for tenant isolation.
    Two-tier security:
      1. Base tables (sales.*, person.*, etc.) → must have WHERE customerid = {customer_id}
      2. Uploaded tables (customer_{id}_*) → table name must belong to this user (table-level)
    Returns None if valid, or "ACCESS_DENIED" if invalid.
    """
    sql_upper = sql.upper()
    sql_lower = sql.lower()

    # Block destructive statements
    destructive = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE"]
    if any(kw in sql_upper for kw in destructive):
        return "ACCESS_DENIED"

    # ── Check 1: Uploaded table isolation (table-level security) ──
    # Find all references to customer_XXXXX_ tables in the SQL
    uploaded_refs = re.findall(r'customer_(\d+)_\w+', sql_lower)
    for ref_id in uploaded_refs:
        if int(ref_id) != customer_id:
            return "ACCESS_DENIED"  # Trying to access another user's uploaded table

    # ── Check 2: Base table isolation (row-level security) ──
    # These shared tables MUST be strictly filtered by the explicit user ID
    base_tables = ["salesorderheader", "salesorderdetail", "customer", "person", "emailaddress", "businessentity"]
    touches_base = any(t in sql_lower for t in base_tables)

    if touches_base:
        # Strictly enforce that an equality filter for this exact user ID exists in the query
        isolation_pattern = rf'(?:customer_?id|user_?id|businessentityid|personid)\s*=\s*[\'"]?{customer_id}[\'"]?'
        if not re.search(isolation_pattern, sql, re.IGNORECASE):
            return "ACCESS_DENIED"
            
        # Block inequality bypasses (e.g. customerid != 11091)
        if re.search(rf'(?:!|<>|>|<)\s*=\s*[\'"]?{customer_id}[\'"]?', sql, re.IGNORECASE):
            return "ACCESS_DENIED"

        # Block cross-tenant ID injection for any other ID
        id_matches = re.findall(r'(?:customer_?id|user_?id|businessentityid|personid)\s*=\s*[\'"]?(\d+)[\'"]?', sql, re.IGNORECASE)
        for match_id in id_matches:
            if int(match_id) != customer_id:
                return "ACCESS_DENIED"

    return None


def _build_system_prompt(user_id: int) -> str:
    base_prompt = f"""You are an expert SQL generator for PostgreSQL. Return ONLY a valid SQL query.

CRITICAL RULES:
1. **TENANT ISOLATION**: 
   - For base tables (sales.*, person.*, production.*): ALWAYS add WHERE customerid = {user_id} when the table has a customerid column.
   - For uploaded tables (marked "(uploaded)" in the schema): These are physically private to this user. Do NOT add customerid or user_id filters on uploaded tables — query them directly.
2. Never use SELECT *. Select only specific columns needed. For counts use COUNT(*).
3. Use schema-qualified names for base tables (e.g. sales.salesorderheader). Use plain names for uploaded tables.
4. Use concise aliases (soh, sod, p, c).
5. JOIN tables intelligently based on foreign keys in the schema.
6. If the question CLEARLY cannot be answered from the schema (e.g., asking about the weather), return exactly: CANNOT_ANSWER. However, if the question asks about business metrics using vague synonyms ("items", "things", "sales", "doing", "buying", "selling", "records"), you MUST map these to the closest matching tables (e.g., products, orders) and return a valid SQL query. NEVER return CANNOT_ANSWER for business-related questions.
7. Use LIMIT N (PostgreSQL syntax, never TOP N). Add LIMIT 100 to row-returning queries (not COUNT/SUM/AVG).
8. Use EXTRACT(YEAR FROM col) for dates, ILIKE for text matching.
9. Keep queries simple. Prefer JOINs over subqueries.
10. Max 5-8 columns when user asks for "everything".
11. Use name/title columns over raw IDs when available.
12. **GENERALIZED SEMANTICS (Apply to ANY schema):**
   - "Total products": SUM(quantity) if quantity exists, else COUNT(*).
   - "Unique products": COUNT(DISTINCT product_id) or COUNT(DISTINCT item_name).
   - "Duplicates": Group by item/product. Use HAVING SUM(quantity) > 1 if quantity exists, else HAVING COUNT(*) > 1.
   - "Total Cost / Spent": SUM(price * quantity) if quantity exists. If only price exists, use SUM(price).
   - "Cost for each/individual cost": Expose the base unit price column without multiplication.
   - "Most expensive overall including duplicates": Group by the item and ORDER BY SUM(price * quantity) DESC LIMIT 1.
   - **Pronouns & Ownership**: "I", "we", "my", "our", "us" ALL refer to the authenticated user. Always filter by customer_id/user_id = {user_id}.
   - **Vague Nouns/Verbs ("items", "things", "did", "made")**: Intelligently map conversational terms to the most relevant primary data table and action available in the schema (e.g., items = products/records, did = ordered/purchased). Do not fail just because specific schema terms aren't used.
13. For complex multi-part questions: if the question asks for mixed aggregations (e.g. scalar totals AND lists of items), output **MULTIPLE SEPARATE SELECT STATEMENTS** separated by a semicolon `;`. The system will execute all of them and combine the results. Do not force them into a single query with complex JOINs if they are logically different concepts.

IDENTITY QUERIES:
- "What is my name?" → SELECT firstname, lastname FROM sales.customer c JOIN person.person p ON c.personid = p.businessentityid WHERE c.customerid = {user_id}
- "What is my ID/customer ID?" → The user's ID is {user_id}. Return: SELECT {user_id} AS customer_id
- "What is my email?" → JOIN person.emailaddress ON businessentityid, filtered by customerid = {user_id}

Do not explain. No markdown. Just raw SQL."""

    # Add extra hints ONLY for small local models
    if _LLM_PROVIDER == "ollama":
        base_prompt += _OLLAMA_EXTRA_HINTS

    return base_prompt


def generate_sql(user_question: str, user_id: int, history: list = None, error_feedback: str = None) -> str:
    schema = get_schema(user_id)
    system_prompt = _build_system_prompt(user_id)

    history_text = ""
    if history:
        history_text = "Recent Conversation:\n"
        for msg in history[-6:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
        history_text += "\n"

    error_context = ""
    if error_feedback:
        error_context = f"\n[FIX REQUIRED]: Previous SQL failed with: {error_feedback}\nCorrect the syntax.\n"

    prompt = f"""Schema:
{schema}

Customer ID: {user_id}
{history_text}Question: {user_question}
{error_context}
SQL:"""

    sql = call_llm(prompt=prompt, system_prompt=system_prompt, max_tokens=512)
    sql = _clean_sql(sql)

    if sql == "CANNOT_ANSWER":
        return sql

    violation = _validate_sql(sql, user_id)
    if violation:
        return "ACCESS_DENIED"

    return sql


async def generate_sql_async(user_question: str, user_id: int, history: list = None, error_feedback: str = None) -> str:
    schema = get_schema(user_id)
    system_prompt = _build_system_prompt(user_id)

    history_text = ""
    if history:
        history_text = "Recent Conversation:\n"
        for msg in history[-6:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
        history_text += "\n"

    error_context = ""
    if error_feedback:
        error_context = f"\n[FIX REQUIRED]: Previous SQL failed with: {error_feedback}\nCorrect the syntax.\n"

    prompt = f"""Schema:
{schema}

Customer ID: {user_id}
{history_text}Question: {user_question}
{error_context}
SQL:"""

    sql = await call_llm_async(prompt=prompt, system_prompt=system_prompt, max_tokens=512)
    sql = _clean_sql(sql)

    if sql == "CANNOT_ANSWER":
        return sql

    violation = _validate_sql(sql, user_id)
    if violation:
        return "ACCESS_DENIED"

    return sql


def _clean_sql(sql: str) -> str:
    """Strip markdown fences, whitespace, and preserve multiple statements."""
    sql = sql.strip()
    if sql.startswith("```"):
        sql = re.sub(r"^```(?:sql)?\s*", "", sql)
        sql = re.sub(r"\s*```$", "", sql)
    
    # Strip any trailing semicolons to prevent empty final statements
    sql = sql.strip().rstrip(";")
    return sql