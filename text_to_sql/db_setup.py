import csv
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    return create_engine(os.getenv("DATABASE_URL"))

def setup_database():
    engine = get_engine()

    with engine.connect() as conn:
        # Create users table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            )
        """))

        # Create upi_transactions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS upi_transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                transaction_id TEXT,
                timestamp TEXT,
                transaction_type TEXT,
                merchant_category TEXT,
                amount_inr REAL,
                transaction_status TEXT,
                sender_age_group TEXT,
                receiver_age_group TEXT,
                sender_state TEXT,
                sender_bank TEXT,
                receiver_bank TEXT,
                device_type TEXT,
                network_type TEXT,
                fraud_flag INTEGER,
                hour_of_day INTEGER,
                day_of_week TEXT,
                is_weekend INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))

        conn.commit()

        # Check if users already exist — if yes, skip seeding
        result = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        if result > 0:
            print("Database already seeded. Skipping.")
            return

        # Insert 2 hardcoded users
        conn.execute(text("""
            INSERT INTO users (id, name, email) VALUES
            (1, 'Alice', 'alice@bizbot.com'),
            (2, 'Bob', 'bob@bizbot.com')
        """))
        conn.commit()

    # Load CSV data in batches
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "upi_transactions_2024.csv")

    if not os.path.exists(csv_path):
        print(f"CSV not found at {csv_path}. Skipping data load.")
        return

    print("Loading CSV data into Supabase. This will take a few minutes...")

    batch = []
    batch_size = 1000
    total = 0

    with engine.connect() as conn:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                user_id = 1 if i < 125000 else 2
                batch.append({
                    "user_id": user_id,
                    "transaction_id": row["transaction id"],
                    "timestamp": row["timestamp"],
                    "transaction_type": row["transaction type"],
                    "merchant_category": row["merchant_category"],
                    "amount_inr": float(row["amount (INR)"]),
                    "transaction_status": row["transaction_status"],
                    "sender_age_group": row["sender_age_group"],
                    "receiver_age_group": row["receiver_age_group"],
                    "sender_state": row["sender_state"],
                    "sender_bank": row["sender_bank"],
                    "receiver_bank": row["receiver_bank"],
                    "device_type": row["device_type"],
                    "network_type": row["network_type"],
                    "fraud_flag": int(row["fraud_flag"]),
                    "hour_of_day": int(row["hour_of_day"]),
                    "day_of_week": row["day_of_week"],
                    "is_weekend": int(row["is_weekend"]),
                })

                if len(batch) == batch_size:
                    conn.execute(text("""
                        INSERT INTO upi_transactions (
                            user_id, transaction_id, timestamp, transaction_type,
                            merchant_category, amount_inr, transaction_status,
                            sender_age_group, receiver_age_group, sender_state,
                            sender_bank, receiver_bank, device_type, network_type,
                            fraud_flag, hour_of_day, day_of_week, is_weekend
                        ) VALUES (
                            :user_id, :transaction_id, :timestamp, :transaction_type,
                            :merchant_category, :amount_inr, :transaction_status,
                            :sender_age_group, :receiver_age_group, :sender_state,
                            :sender_bank, :receiver_bank, :device_type, :network_type,
                            :fraud_flag, :hour_of_day, :day_of_week, :is_weekend
                        )
                    """), batch)
                    conn.commit()
                    total += len(batch)
                    print(f"Inserted {total} rows...")
                    batch = []

        # Insert remaining rows
        if batch:
            conn.execute(text("""
                INSERT INTO upi_transactions (
                    user_id, transaction_id, timestamp, transaction_type,
                    merchant_category, amount_inr, transaction_status,
                    sender_age_group, receiver_age_group, sender_state,
                    sender_bank, receiver_bank, device_type, network_type,
                    fraud_flag, hour_of_day, day_of_week, is_weekend
                ) VALUES (
                    :user_id, :transaction_id, :timestamp, :transaction_type,
                    :merchant_category, :amount_inr, :transaction_status,
                    :sender_age_group, :receiver_age_group, :sender_state,
                    :sender_bank, :receiver_bank, :device_type, :network_type,
                    :fraud_flag, :hour_of_day, :day_of_week, :is_weekend
                )
            """), batch)
            conn.commit()
            total += len(batch)

    print(f"Done! Total {total} rows loaded into Supabase.")

if __name__ == "__main__":
    setup_database()