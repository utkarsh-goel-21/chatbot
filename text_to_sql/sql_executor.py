from sqlalchemy import text
from text_to_sql.schema_loader import get_engine

def execute_sql(sql_query: str) -> list[dict]:
    engine = get_engine()

    with engine.connect() as conn:
        result = conn.execute(text(sql_query))
        columns = result.keys()
        rows = result.fetchall()

    return [dict(zip(columns, row)) for row in rows]