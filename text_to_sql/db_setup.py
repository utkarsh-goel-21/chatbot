import os
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    return create_engine(os.getenv("DATABASE_URL"), poolclass=NullPool)

def setup_database():
    """Verify AdventureWorks is reachable and ensure supporting tables exist."""
    engine = get_engine()

    with engine.connect() as conn:
        # 1. Verify AdventureWorks data is present
        count = conn.execute(text("SELECT COUNT(*) FROM sales.customer")).scalar()
        print(f"AdventureWorks verified — sales.customer has {count} rows.")

        # 2. Recreate uploaded_tables tracker (dropped with old UPI cleanup)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS uploaded_tables (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                table_name TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(customer_id, table_name)
            )
        """))
        conn.commit()
        print("uploaded_tables tracker ready.")

if __name__ == "__main__":
    setup_database()