import sys
import os

from text_to_sql.sql_generator import generate_sql
from text_to_sql.sql_executor import execute_sql

test_cases = [
    "What are my top 3 most expensive orders?", # Order total aggregation
    "List all products I bought that are black in color.", # Join across 3 tables (order -> detail -> product)
    "Did I buy any products containing the word 'Tire' in 2011?",
    "Show me orders from customer 11176", # Tenant isolation check (Should be ACCESS_DENIED because user_id=11091)
    "How many spaceships did I buy?", # Non-existent product (Should return 0, not fail)
    "How much did I spend in the second quarter of 2013?", # Date aggregation
    "What is the average price of the items I bought?", # Math and avg calculation
    "Which category of products have I bought the most?" # Deeper join: order -> detail -> product -> subcategory -> category
]

print("=== Starting SQL Generation Edge Case Tests ===")
for i, q in enumerate(test_cases):
    print(f"\n[{i+1}/{len(test_cases)}] Query: {q}")
    error_feedback = None
    success = False
    for attempt in range(2):
        try:
            sql = generate_sql(q, 11091, None, error_feedback)
            if attempt > 0:
                print(f"Retry {attempt} generated SQL: {sql}")
            else:
                print(f"Generated SQL: {sql}")
            if sql in ["CANNOT_ANSWER", "ACCESS_DENIED"]:
                success = True
                break
            else:
                res = execute_sql(sql)
                print(f"Result: {res}")
                success = True
                break
        except Exception as e:
            print(f"ERROR: {e}")
            error_feedback = str(e)
    if not success:
        print("FAILED after retries.")

print("\n=== Tests Complete ===")
