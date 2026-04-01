import os
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            os.getenv("DATABASE_URL"),
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,       # auto-reconnect stale connections
            pool_recycle=300,          # recycle connections every 5 min
        )
    return _engine

def setup_database():
    """Verify AdventureWorks is reachable and ensure supporting tables exist."""
    engine = get_engine()

    with engine.connect() as conn:
        # 1. Verify AdventureWorks data is present
        try:
            count = conn.execute(text("SELECT COUNT(*) FROM sales.customer")).scalar()
            print(f"AdventureWorks verified — sales.customer has {count} rows.")
        except Exception as e:
            print(f"⚠️  AdventureWorks verification skipped: {e}")
            print("   If running locally, make sure you've loaded the AdventureWorks data.")

        # 2. Recreate uploaded_tables tracker
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

        # 3. Ensure rag_documents table exists (needed for local PG without pgvector pre-setup)
        vector_store = os.getenv("VECTOR_STORE", "pgvector").lower()
        if vector_store == "pgvector":
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS rag_documents (
                        id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        embedding vector(384)
                    )
                """))
                print("rag_documents table ready (pgvector).")
            except Exception as e:
                print(f"⚠️  Could not create rag_documents with pgvector: {e}")
                print("   If using local mode, set VECTOR_STORE=chromadb in .env")

        conn.commit()
        print("uploaded_tables tracker ready.")

if __name__ == "__main__":
    setup_database()