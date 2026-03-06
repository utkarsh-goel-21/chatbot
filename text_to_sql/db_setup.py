from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

def setup_database():
    engine = create_engine(os.getenv("DATABASE_URL"))

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                category TEXT,
                price REAL
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                product_id INTEGER,
                quantity INTEGER,
                total_amount REAL,
                transaction_date TEXT,
                payment_type TEXT
            )
        """))

        conn.execute(text("""
            INSERT OR IGNORE INTO products VALUES
            (1, 'Laptop', 'Electronics', 999.99),
            (2, 'Headphones', 'Electronics', 199.99),
            (3, 'Desk Chair', 'Furniture', 299.99),
            (4, 'Notebook', 'Stationery', 4.99),
            (5, 'Coffee Mug', 'Kitchen', 12.99)
        """))

        conn.execute(text("""
            INSERT OR IGNORE INTO transactions VALUES
            (1, 1, 2, 1999.98, '2026-03-07', 'credit_card'),
            (2, 2, 5, 999.95, '2026-03-07', 'upi'),
            (3, 3, 1, 299.99, '2026-03-06', 'cash'),
            (4, 4, 10, 49.90, '2026-03-06', 'credit_card'),
            (5, 5, 3, 38.97, '2026-03-05', 'upi'),
            (6, 1, 1, 999.99, '2026-03-05', 'cash'),
            (7, 2, 2, 399.98, '2026-03-07', 'credit_card')
        """))

        conn.commit()

    print("Database setup complete.")

if __name__ == "__main__":
    setup_database()
