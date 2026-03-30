from sqlalchemy import text
from text_to_sql.db_setup import get_engine
from utils.groq_client import call_llm


def fetch_customer_stats(customer_id: int) -> dict:
    """Pull key business stats for a specific customer from AdventureWorks."""
    engine = get_engine()
    stats = {}

    with engine.connect() as conn:
        # Customer name
        try:
            row = conn.execute(text("""
                SELECT p.firstname, p.lastname
                FROM sales.customer c
                JOIN person.person p ON c.personid = p.businessentityid
                WHERE c.customerid = :cid
            """), {"cid": customer_id}).fetchone()
            stats["name"] = f"{row[0]} {row[1]}" if row else "Unknown"
        except Exception:
            stats["name"] = "Unknown"

        # Order summary
        try:
            row = conn.execute(text("""
                SELECT COUNT(*) AS order_count,
                       ROUND(SUM(totaldue)::numeric, 2) AS total_spent,
                       ROUND(AVG(totaldue)::numeric, 2) AS avg_order_value,
                       MIN(orderdate)::date AS first_order,
                       MAX(orderdate)::date AS last_order
                FROM sales.salesorderheader
                WHERE customerid = :cid
            """), {"cid": customer_id}).fetchone()
            stats["order_count"] = row[0]
            stats["total_spent"] = row[1]
            stats["avg_order_value"] = row[2]
            stats["first_order"] = str(row[3])
            stats["last_order"] = str(row[4])
        except Exception:
            stats["order_count"] = 0
            stats["total_spent"] = 0
            stats["avg_order_value"] = 0
            stats["first_order"] = "N/A"
            stats["last_order"] = "N/A"

        # Top 5 products
        try:
            rows = conn.execute(text("""
                SELECT p.name, COUNT(*) AS times_ordered, SUM(d.orderqty) AS total_qty
                FROM sales.salesorderdetail d
                JOIN sales.salesorderheader h ON d.salesorderid = h.salesorderid
                JOIN production.product p ON d.productid = p.productid
                WHERE h.customerid = :cid
                GROUP BY p.name
                ORDER BY times_ordered DESC
                LIMIT 5
            """), {"cid": customer_id}).fetchall()
            stats["top_products"] = [(r[0], r[1], r[2]) for r in rows]
        except Exception:
            stats["top_products"] = []

        # Product categories
        try:
            rows = conn.execute(text("""
                SELECT pc.name AS category, COUNT(*) AS item_count
                FROM sales.salesorderdetail d
                JOIN sales.salesorderheader h ON d.salesorderid = h.salesorderid
                JOIN production.product p ON d.productid = p.productid
                JOIN production.productsubcategory ps ON p.productsubcategoryid = ps.productsubcategoryid
                JOIN production.productcategory pc ON ps.productcategoryid = pc.productcategoryid
                WHERE h.customerid = :cid
                GROUP BY pc.name
                ORDER BY item_count DESC
            """), {"cid": customer_id}).fetchall()
            stats["categories"] = [(r[0], r[1]) for r in rows]
        except Exception:
            stats["categories"] = []

        # Order size stats
        try:
            row = conn.execute(text("""
                SELECT ROUND(AVG(item_count)::numeric, 1) AS avg_items,
                       MAX(item_count) AS max_items,
                       MIN(item_count) AS min_items
                FROM (
                    SELECT h.salesorderid, COUNT(*) AS item_count
                    FROM sales.salesorderheader h
                    JOIN sales.salesorderdetail d ON h.salesorderid = d.salesorderid
                    WHERE h.customerid = :cid
                    GROUP BY h.salesorderid
                ) sub
            """), {"cid": customer_id}).fetchone()
            stats["avg_items_per_order"] = row[0]
            stats["max_items_in_order"] = row[1]
            stats["min_items_in_order"] = row[2]
        except Exception:
            stats["avg_items_per_order"] = 0
            stats["max_items_in_order"] = 0
            stats["min_items_in_order"] = 0

        # Yearly spending breakdown
        try:
            rows = conn.execute(text("""
                SELECT EXTRACT(YEAR FROM orderdate)::int AS year,
                       COUNT(*) AS orders,
                       ROUND(SUM(totaldue)::numeric, 2) AS spent
                FROM sales.salesorderheader
                WHERE customerid = :cid
                GROUP BY year
                ORDER BY year
            """), {"cid": customer_id}).fetchall()
            stats["yearly_spending"] = [(r[0], r[1], r[2]) for r in rows]
        except Exception:
            stats["yearly_spending"] = []

    return stats


def generate_insight_documents(customer_id: int) -> list[dict]:
    """Generate RAG insight documents for a customer using LLM."""
    stats = fetch_customer_stats(customer_id)

    raw_summary = f"""
Customer: {stats['name']} (ID: {customer_id})
Total Orders: {stats['order_count']}
Total Spent: ${stats['total_spent']}
Average Order Value: ${stats['avg_order_value']}
First Order: {stats['first_order']}
Last Order: {stats['last_order']}
Average Items Per Order: {stats['avg_items_per_order']}
Largest Order: {stats['max_items_in_order']} items
Smallest Order: {stats['min_items_in_order']} items
Top Products: {', '.join([f"{p[0]} (ordered {p[1]}x, qty {p[2]})" for p in stats['top_products']])}
Product Categories: {', '.join([f"{c[0]} ({c[1]} items)" for c in stats['categories']])}
Yearly Spending: {', '.join([f"{y[0]}: {y[1]} orders, ${y[2]}" for y in stats['yearly_spending']])}
"""

    topics = [
        "overall order history and spending overview",
        "product preferences and most purchased items",
        "product category trends and diversity of purchases",
        "order frequency, timing patterns, and yearly trends",
        "order size analysis and spending behavior",
    ]

    documents = []
    for i, topic in enumerate(topics):
        system_prompt = """You are a business analyst writing customer insight reports.
You will be given raw order statistics for a customer and a topic.
Write a clear, concise 3-4 sentence business insight paragraph about that specific topic.
Use the actual numbers provided. Write in third person as if describing this customer's purchasing behavior.
Do not use bullet points. Just a clean paragraph."""

        prompt = f"""Raw Customer Data:
{raw_summary}

Write a business insight paragraph specifically about: {topic}

Insight:"""

        insight_text = call_llm(prompt=prompt, system_prompt=system_prompt)

        documents.append({
            "id": f"customer_{customer_id}_insight_{i+1}",
            "text": insight_text,
            "user_id": customer_id,  # stored in rag_documents.user_id column
        })

    print(f"Generated {len(documents)} insight documents for customer {customer_id}")
    return documents


if __name__ == "__main__":
    for cid in [11091, 11176]:
        docs = generate_insight_documents(cid)
        for d in docs:
            print(f"\n--- {d['id']} ---")
            print(d['text'])