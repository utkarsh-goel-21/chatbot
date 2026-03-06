from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    return create_engine(os.getenv("DATABASE_URL"))

def get_schema() -> str:
    engine = get_engine()
    inspector = inspect(engine)
    schema_parts = []

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        col_definitions = ", ".join(
            f"{col['name']} ({str(col['type'])})" for col in columns
        )
        schema_parts.append(f"Table: {table_name} | Columns: {col_definitions}")

    return "\n".join(schema_parts)