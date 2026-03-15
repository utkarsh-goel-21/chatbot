from sqlalchemy import text
from text_to_sql.db_setup import get_engine
from utils.groq_client import call_llm

def fetch_user_stats(user_id: int) -> dict:
    engine = get_engine()
    stats = {}

    with engine.connect() as conn:
        # Total transactions
        stats["total_transactions"] = conn.execute(text(
            "SELECT COUNT(*) FROM upi_transactions WHERE user_id = :uid"
        ), {"uid": user_id}).scalar()

        # Total amount
        stats["total_amount"] = conn.execute(text(
            "SELECT ROUND(SUM(amount_inr)::numeric, 2) FROM upi_transactions WHERE user_id = :uid"
        ), {"uid": user_id}).scalar()

        # Success rate
        stats["success_rate"] = conn.execute(text(
            """SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE transaction_status = 'SUCCESS') / COUNT(*)::numeric, 2)
               FROM upi_transactions WHERE user_id = :uid"""
        ), {"uid": user_id}).scalar()

        # Top 3 merchant categories
        rows = conn.execute(text(
            """SELECT merchant_category, COUNT(*) as cnt
               FROM upi_transactions WHERE user_id = :uid
               GROUP BY merchant_category ORDER BY cnt DESC LIMIT 3"""
        ), {"uid": user_id}).fetchall()
        stats["top_categories"] = [(r[0], r[1]) for r in rows]

        # Fraud rate
        stats["fraud_rate"] = conn.execute(text(
            """SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE fraud_flag = 1) / COUNT(*)::numeric, 2)
               FROM upi_transactions WHERE user_id = :uid"""
        ), {"uid": user_id}).scalar()

        # Top 3 banks
        rows = conn.execute(text(
            """SELECT sender_bank, COUNT(*) as cnt
               FROM upi_transactions WHERE user_id = :uid
               GROUP BY sender_bank ORDER BY cnt DESC LIMIT 3"""
        ), {"uid": user_id}).fetchall()
        stats["top_banks"] = [(r[0], r[1]) for r in rows]

        # Weekend vs weekday
        stats["weekend_count"] = conn.execute(text(
            "SELECT COUNT(*) FROM upi_transactions WHERE user_id = :uid AND is_weekend = 1"
        ), {"uid": user_id}).scalar()
        stats["weekday_count"] = conn.execute(text(
            "SELECT COUNT(*) FROM upi_transactions WHERE user_id = :uid AND is_weekend = 0"
        ), {"uid": user_id}).scalar()

        # Top transaction types
        rows = conn.execute(text(
            """SELECT transaction_type, COUNT(*) as cnt
               FROM upi_transactions WHERE user_id = :uid
               GROUP BY transaction_type ORDER BY cnt DESC"""
        ), {"uid": user_id}).fetchall()
        stats["transaction_types"] = [(r[0], r[1]) for r in rows]

        # Top states
        rows = conn.execute(text(
            """SELECT sender_state, COUNT(*) as cnt
               FROM upi_transactions WHERE user_id = :uid
               GROUP BY sender_state ORDER BY cnt DESC LIMIT 3"""
        ), {"uid": user_id}).fetchall()
        stats["top_states"] = [(r[0], r[1]) for r in rows]

        # Average transaction amount
        stats["avg_amount"] = conn.execute(text(
            "SELECT ROUND(AVG(amount_inr)::numeric, 2) FROM upi_transactions WHERE user_id = :uid"
        ), {"uid": user_id}).scalar()

        # Network type breakdown
        rows = conn.execute(text(
            """SELECT network_type, COUNT(*) as cnt
               FROM upi_transactions WHERE user_id = :uid
               GROUP BY network_type ORDER BY cnt DESC"""
        ), {"uid": user_id}).fetchall()
        stats["network_types"] = [(r[0], r[1]) for r in rows]

    return stats


def generate_insight_documents(user_id: int) -> list[dict]:
    stats = fetch_user_stats(user_id)

    # Build a raw data summary to feed to LLM
    raw_summary = f"""
User ID: {user_id}
Total Transactions: {stats['total_transactions']}
Total Amount (INR): {stats['total_amount']}
Average Transaction Amount (INR): {stats['avg_amount']}
Transaction Success Rate: {stats['success_rate']}%
Fraud Rate: {stats['fraud_rate']}%
Top Merchant Categories: {', '.join([f"{c[0]} ({c[1]} txns)" for c in stats['top_categories']])}
Top Sender Banks: {', '.join([f"{b[0]} ({b[1]} txns)" for b in stats['top_banks']])}
Weekend Transactions: {stats['weekend_count']}
Weekday Transactions: {stats['weekday_count']}
Transaction Types: {', '.join([f"{t[0]} ({t[1]} txns)" for t in stats['transaction_types']])}
Top States: {', '.join([f"{s[0]} ({s[1]} txns)" for s in stats['top_states']])}
Network Types: {', '.join([f"{n[0]} ({n[1]} txns)" for n in stats['network_types']])}
"""

    # Use Groq to generate 5 different insight documents from this data
    topics = [
        "overall business performance and transaction volumes",
        "merchant category trends and spending patterns",
        "fraud analysis and transaction success rates",
        "banking and payment method preferences",
        "geographic and network usage patterns",
    ]

    documents = []
    for i, topic in enumerate(topics):
        system_prompt = """You are a business analyst writing insight reports.
You will be given raw transaction statistics and a topic.
Write a clear, concise 3-4 sentence business insight paragraph about that specific topic.
Use the actual numbers provided. Write in third person as if describing this business's performance.
Do not use bullet points. Just a clean paragraph."""

        prompt = f"""Raw Transaction Data:
{raw_summary}

Write a business insight paragraph specifically about: {topic}

Insight:"""

        insight_text = call_llm(prompt=prompt, system_prompt=system_prompt)

        documents.append({
            "id": f"user_{user_id}_insight_{i+1}",
            "text": insight_text,
            "user_id": user_id
        })

    print(f"Generated {len(documents)} insight documents for user {user_id}")
    return documents


if __name__ == "__main__":
    for uid in [1, 2]:
        docs = generate_insight_documents(uid)
        for d in docs:
            print(f"\n--- {d['id']} ---")
            print(d['text'])