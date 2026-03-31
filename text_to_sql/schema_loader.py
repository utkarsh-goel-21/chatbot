import os
from sqlalchemy import inspect, text
from text_to_sql.db_setup import get_engine
from dotenv import load_dotenv

load_dotenv()

_schema_cache = None

def reset_schema_cache():
    global _schema_cache
    _schema_cache = None


def _build_base_schema() -> str:
    """Build schema string for core AdventureWorks tables (cached globally)."""
    engine = get_engine()
    inspector = inspect(engine)
    schema_parts = []

    aw_schemas = ["sales", "person", "production"]

    # Core tables we actually want the LLM to know about (saves tokens)
    core_tables = {
        "customer", "salesorderheader", "salesorderdetail",
        "person", "businessentity", "emailaddress",
        "product", "productcategory", "productsubcategory", "productmodel"
    }

    try:
        for schema_name in aw_schemas:
            try:
                tables = inspector.get_table_names(schema=schema_name)
            except Exception:
                continue

            for table_name in tables:
                if table_name not in core_tables:
                    continue

                full_table = f"{schema_name}.{table_name}"

                try:
                    columns = inspector.get_columns(table_name, schema=schema_name)
                except Exception:
                    continue

                col_definitions = []
                for col in columns:
                    col_name = col["name"]
                    col_type = str(col["type"])
                    col_definitions.append(f"{col_name} ({col_type})")

                schema_parts.append(
                    f"Table: {full_table} | Columns: {', '.join(col_definitions)}"
                )
    except Exception as e:
        print(f"Error building schema: {e}")

    return "\n".join(schema_parts)


def _get_uploaded_tables_schema(customer_id: int) -> str:
    """Get schema for tables uploaded by a specific customer (never cached)."""
    engine = get_engine()
    inspector = inspect(engine)
    parts = []

    try:
        with engine.connect() as conn:
            uploaded = conn.execute(text(
                "SELECT table_name FROM uploaded_tables WHERE customer_id = :cid"
            ), {"cid": customer_id}).fetchall()

            for row in uploaded:
                tname = row[0]
                try:
                    ucols = inspector.get_columns(tname)
                    col_defs = [f"{col['name']} ({str(col['type'])})" for col in ucols]
                    parts.append(f"Table: {tname} (uploaded) | Columns: {', '.join(col_defs)}")
                except Exception:
                    pass
    except Exception:
        pass

    return "\n".join(parts)


def get_schema(user_id: int = None) -> str:
    """
    Return full schema string for the LLM.
    Base AdventureWorks schema is cached globally.
    Uploaded tables are appended per-customer (not cached).
    """
    global _schema_cache

    if _schema_cache is None:
        _schema_cache = _build_base_schema()

    if user_id:
        uploaded = _get_uploaded_tables_schema(user_id)
        if uploaded:
            return _schema_cache + "\n" + uploaded

    return _schema_cache