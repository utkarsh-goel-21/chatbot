from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()

_schema_cache = None

def reset_schema_cache():
    global _schema_cache
    _schema_cache = None

def get_engine():
    return create_engine(os.getenv("DATABASE_URL"))

def get_schema(user_id: int = None) -> str:
    global _schema_cache
    if _schema_cache is not None:
        return _schema_cache
    if user_id:
        with engine.connect() as conn:
            uploaded = conn.execute(text(
                "SELECT table_name FROM uploaded_tables WHERE user_id = :uid"
            ), {"uid": user_id}).fetchall()

            for row in uploaded:
                tname = row[0]
                try:
                    ucols = inspector.get_columns(tname)
                    col_defs = []
                    for col in ucols:
                        col_defs.append(f"{col['name']} ({str(col['type'])})")
                    schema_parts.append(f"Table: {tname} | Columns: {', '.join(col_defs)}")
                except:
                    pass


    engine = get_engine()
    inspector = inspect(engine)
    schema_parts = []

    excluded_tables = {"rag_documents"}
    skip_distinct = {"id", "amount_inr", "timestamp", "transaction_id", "hour_of_day"}

    with engine.connect() as conn:
        for table_name in inspector.get_table_names():
            if table_name in excluded_tables:
                continue
            columns = inspector.get_columns(table_name)
            col_definitions = []
            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                if col_name in skip_distinct:
                    col_definitions.append(f"{col_name} ({col_type})")
                else:
                    try:
                        rows = conn.execute(text(
                            f"SELECT DISTINCT {col_name} FROM {table_name} LIMIT 20"
                        )).fetchall()
                        values = [str(r[0]) for r in rows]
                        col_definitions.append(
                            f"{col_name} ({col_type}, possible values: {', '.join(values)})"
                        )
                    except:
                        col_definitions.append(f"{col_name} ({col_type})")
            schema_parts.append(
                f"Table: {table_name} | Columns: {', '.join(col_definitions)}"
            )

    _schema_cache = "\n".join(schema_parts)
    return _schema_cache