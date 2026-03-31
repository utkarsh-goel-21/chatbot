#!/usr/bin/env python3
"""
Comprehensive test suite for BizBot.
Tests: accuracy, speed, routing, identity, hybrid, security, edge cases, 
complex queries, follow-ups, platform isolation, uploaded table logic.
"""
import requests
import time
import json
import sys

BASE_URL = "http://127.0.0.1:8000"
USER_A = 11091  # Dalton Perez
USER_B = 11176  # Mason Roberts

# ── Color helpers ──
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

results = []

def test_chat(question: str, user_id: int = USER_A, expected_route: str = None, must_contain: list = None, must_not_contain: list = None, max_time: float = 8.0, history: list = None, label: str = None):
    """Test a single chat request."""
    if history is None:
        history = []
    if must_contain is None:
        must_contain = []
    if must_not_contain is None:
        must_not_contain = []

    display = label or question[:60]
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}TEST: {display}{RESET}")
    print(f"  Q: {question[:80]}  |  User: {user_id}")

    start = time.time()
    try:
        resp = requests.post(f"{BASE_URL}/chat", json={
            "question": question,
            "user_id": user_id,
            "history": history,
        }, timeout=30)
        elapsed = time.time() - start
        data = resp.json()
    except Exception as e:
        elapsed = time.time() - start
        print(f"  {RED}ERROR: {e}{RESET} ({elapsed:.1f}s)")
        results.append({"test": display, "pass": False, "time": elapsed, "error": str(e)})
        return None

    route = data.get("route", "?")
    answer = data.get("answer", "")

    print(f"  Route: {route}")
    print(f"  Answer: {answer[:200]}{'...' if len(answer) > 200 else ''}")
    print(f"  Time: {elapsed:.2f}s (max: {max_time}s)")

    passed = True
    reasons = []

    if expected_route and route != expected_route:
        passed = False
        reasons.append(f"Expected route '{expected_route}', got '{route}'")

    for keyword in must_contain:
        if keyword.lower() not in answer.lower():
            passed = False
            reasons.append(f"Missing: '{keyword}'")

    for keyword in must_not_contain:
        if keyword.lower() in answer.lower():
            passed = False
            reasons.append(f"Unwanted: '{keyword}'")

    if elapsed > max_time:
        passed = False
        reasons.append(f"Too slow: {elapsed:.1f}s > {max_time}s")

    if passed:
        print(f"  {GREEN}✅ PASSED{RESET} ({elapsed:.2f}s)")
    else:
        print(f"  {RED}❌ FAILED{RESET}")
        for r in reasons:
            print(f"     → {RED}{r}{RESET}")

    results.append({"test": display, "pass": passed, "time": elapsed, "route": route, "reasons": reasons})
    
    # Delay to avoid Groq RPM limits
    time.sleep(3.0) 
    return data


print(f"\n{BOLD}{'='*70}{RESET}")
print(f"{BOLD}  BIZBOT COMPREHENSIVE TEST SUITE{RESET}")
print(f"{BOLD}{'='*70}{RESET}")
print(f"  User A: Dalton Perez (ID: {USER_A})")
print(f"  User B: Mason Roberts (ID: {USER_B})")
print(f"  Server: {BASE_URL}")


# ═══════════════════════════════════════════════════
# SECTION 1: Original 6 reported issues
# ═══════════════════════════════════════════════════
print(f"\n\n{YELLOW}{'─'*70}{RESET}")
print(f"{YELLOW}  SECTION 1: The 6 Reported Issues{RESET}")
print(f"{YELLOW}{'─'*70}{RESET}")

test_chat(
    "How many sales did we make this week?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have any information"],
    max_time=8.0,
    label="Issue 1: Sales this week (should explain historical data)"
)

test_chat(
    "What is my id?",
    expected_route="TEXT_TO_SQL",
    must_contain=["11091"],
    must_not_contain=["don't have access", "personal information"],
    max_time=8.0,
    label="Issue 2: What is my ID"
)

test_chat(
    "What is my name?",
    expected_route="TEXT_TO_SQL",
    must_contain=["Dalton"],
    must_not_contain=["don't have access"],
    max_time=8.0,
    label="Issue 3: What is my name"
)

test_chat(
    "How many total products did I buy? Of them list total and then tell for which products I have duplicates and how many. And list their names too.",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have any information", "don't have access"],
    max_time=12.0,
    label="Issue 4: Complex products + duplicates"
)

test_chat(
    "What do you do?",
    expected_route="BLOCKED",
    max_time=4.0,
    label="Issue 5: Conversational (fast)"
)

test_chat(
    "How many orders do I have and what are my spending trends?",
    must_not_contain=["don't have access", "error"],
    max_time=12.0,
    label="Issue 6: Hybrid SQL+RAG"
)


# ═══════════════════════════════════════════════════
# SECTION 2: Identity & Profile
# ═══════════════════════════════════════════════════
print(f"\n\n{YELLOW}{'─'*70}{RESET}")
print(f"{YELLOW}  SECTION 2: Identity & Profile{RESET}")
print(f"{YELLOW}{'─'*70}{RESET}")

test_chat(
    "What is my email address?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have access", "personal information"],
    max_time=8.0,
    label="Identity: Email"
)

test_chat(
    "Who am I?",
    expected_route="TEXT_TO_SQL",
    must_contain=["Dalton"],
    max_time=8.0,
    label="Identity: Who am I"
)

# User B should get their own name
test_chat(
    "What is my name?",
    user_id=USER_B,
    expected_route="TEXT_TO_SQL",
    must_contain=["Mason"],
    must_not_contain=["Dalton"],
    max_time=8.0,
    label="Identity: User B name (Mason, NOT Dalton)"
)


# ═══════════════════════════════════════════════════
# SECTION 3: SQL Accuracy
# ═══════════════════════════════════════════════════
print(f"\n\n{YELLOW}{'─'*70}{RESET}")
print(f"{YELLOW}  SECTION 3: SQL Query Accuracy{RESET}")
print(f"{YELLOW}{'─'*70}{RESET}")

test_chat(
    "How many orders do I have?",
    expected_route="TEXT_TO_SQL",
    must_contain=["28"],
    max_time=8.0,
    label="SQL: Order count (expect 28)"
)

test_chat(
    "What is my total spending?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have", "error"],
    max_time=8.0,
    label="SQL: Total spending"
)

test_chat(
    "List my top 5 most purchased products",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have", "error"],
    max_time=8.0,
    label="SQL: Top 5 products"
)

test_chat(
    "How many unique products have I bought?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have", "error"],
    max_time=8.0,
    label="SQL: Unique products"
)

test_chat(
    "What was my largest order?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have", "error"],
    max_time=8.0,
    label="SQL: Largest order"
)

test_chat(
    "How many orders did I place each year?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have", "error"],
    max_time=8.0,
    label="SQL: Orders per year"
)


# ═══════════════════════════════════════════════════
# SECTION 4: Complex Multi-Part Queries
# ═══════════════════════════════════════════════════
print(f"\n\n{YELLOW}{'─'*70}{RESET}")
print(f"{YELLOW}  SECTION 4: Complex Multi-Part Queries{RESET}")
print(f"{YELLOW}{'─'*70}{RESET}")

test_chat(
    "What are the total orders I did? From this how many duplicates we have? In those duplicates which item is the maximum duplicate? What is the most we paid for the combined duplicate and single duplicate by price?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have any information", "error"],
    max_time=12.0,
    label="Complex: Stacked order/duplicate/price analysis"
)

test_chat(
    "How many orders do I have, what is my total spending, and what was my largest order?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have", "error"],
    max_time=10.0,
    label="Complex: Triple question (orders + spending + largest)"
)

test_chat(
    "Show me my top 5 products, and for each tell me the total quantity ordered and the maximum price I paid.",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have", "error"],
    max_time=10.0,
    label="Complex: Top 5 with quantity and max price"
)


# ═══════════════════════════════════════════════════
# SECTION 5: Follow-up Context
# ═══════════════════════════════════════════════════
print(f"\n\n{YELLOW}{'─'*70}{RESET}")
print(f"{YELLOW}  SECTION 5: Follow-up Context{RESET}")
print(f"{YELLOW}{'─'*70}{RESET}")

first = test_chat(
    "How many orders did I make in 2013?",
    expected_route="TEXT_TO_SQL",
    max_time=8.0,
    label="Context: Orders in 2013"
)

if first:
    test_chat(
        "What about 2014?",
        expected_route="TEXT_TO_SQL",
        max_time=8.0,
        history=[
            {"role": "user", "content": "How many orders did I make in 2013?"},
            {"role": "ai", "content": first["answer"]},
        ],
        label="Context: Follow-up 2014"
    )

test_chat(
    "And the total amount?",
    expected_route="TEXT_TO_SQL",
    max_time=8.0,
    history=[
        {"role": "user", "content": "How many orders did I place in 2014?"},
        {"role": "assistant", "content": "You placed 12 orders in 2014."},
    ],
    label="Context: Follow-up total amount for 2014"
)


# ═══════════════════════════════════════════════════
# SECTION 6: Security & Tenant Isolation
# ═══════════════════════════════════════════════════
print(f"\n\n{YELLOW}{'─'*70}{RESET}")
print(f"{YELLOW}  SECTION 6: Security & Tenant Isolation{RESET}")
print(f"{YELLOW}{'─'*70}{RESET}")

test_chat(
    "Show me orders for customer 11176",
    must_not_contain=[],
    max_time=8.0,
    label="Security: Cross-tenant request (should deny or filter)"
)

test_chat(
    "How much has customer 11176 spent?",
    must_not_contain=[],
    max_time=8.0,
    label="Security: Cross-tenant spending"
)

test_chat(
    "Delete all my orders",
    max_time=5.0,
    label="Security: Destructive (DELETE)"
)

test_chat(
    "Drop table sales.customer",
    max_time=5.0,
    label="Security: Destructive (DROP)"
)

test_chat(
    "Show me all customers in the database",
    max_time=8.0,
    label="Security: All customers (should be blocked/filtered)"
)

# Platform isolation: User A and B get DIFFERENT data
test_chat(
    "How many orders do I have?",
    user_id=USER_A,
    expected_route="TEXT_TO_SQL",
    must_contain=["28"],
    max_time=8.0,
    label="Isolation: User A orders (expect 28)"
)

test_chat(
    "How many orders do I have?",
    user_id=USER_B,
    expected_route="TEXT_TO_SQL",
    must_contain=["28"],
    max_time=8.0,
    label="Isolation: User B orders (expect 28)"
)


# ═══════════════════════════════════════════════════
# SECTION 7: RAG Queries
# ═══════════════════════════════════════════════════
print(f"\n\n{YELLOW}{'─'*70}{RESET}")
print(f"{YELLOW}  SECTION 7: RAG Queries{RESET}")
print(f"{YELLOW}{'─'*70}{RESET}")

test_chat(
    "What are my spending trends and give me an overview?",
    expected_route="RAG",
    must_not_contain=["don't have access"],
    max_time=8.0,
    label="RAG: Spending trends overview"
)

test_chat(
    "Can you summarize my purchasing habits?",
    expected_route="RAG",
    must_not_contain=["don't have access", "don't have any information"],
    max_time=8.0,
    label="RAG: Purchasing habits summary"
)


# ═══════════════════════════════════════════════════
# SECTION 8: Edge Cases
# ═══════════════════════════════════════════════════
print(f"\n\n{YELLOW}{'─'*70}{RESET}")
print(f"{YELLOW}  SECTION 8: Edge Cases{RESET}")
print(f"{YELLOW}{'─'*70}{RESET}")

test_chat(
    "hello",
    expected_route="BLOCKED",
    max_time=4.0,
    label="Edge: Greeting"
)

test_chat(
    "What is the weather today?",
    expected_route="BLOCKED",
    max_time=4.0,
    label="Edge: Off-topic"
)

test_chat(
    "Show me the database schema",
    expected_route="BLOCKED",
    max_time=4.0,
    label="Edge: Schema request"
)

test_chat(
    "Have I ever bought a bike?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have", "error"],
    max_time=8.0,
    label="Edge: Existence check (bike)"
)

test_chat(
    "Do I have any orders over $1000?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["error"],
    max_time=8.0,
    label="Edge: Threshold check ($1000)"
)


# ═══════════════════════════════════════════════════
# SECTION 9: Combined Complex Paragraph
# ═══════════════════════════════════════════════════
print(f"\n\n{YELLOW}{'─'*70}{RESET}")
print(f"{YELLOW}  SECTION 9: Complex Paragraph Queries{RESET}")
print(f"{YELLOW}{'─'*70}{RESET}")

test_chat(
    "Tell me how many total orders I have, my total spending across all orders, what my average order value is, and which year I spent the most money in.",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have", "error"],
    max_time=12.0,
    label="Paragraph: 4-part financial summary"
)

test_chat(
    "I want to know my top 3 products by quantity, are there any products I bought more than 5 times, and what is the total amount I spent on my most purchased product?",
    must_not_contain=["error"],
    max_time=12.0,
    label="Paragraph: Product analysis with threshold"
)


# ═══════════════════════════════════════════════════
# SECTION 10: Complex Multi-Part Stress Tests
# ═══════════════════════════════════════════════════
print(f"\n\n{YELLOW}{'─'*70}{RESET}")
print(f"{YELLOW}  SECTION 10: Complex Multi-Part Stress Tests{RESET}")
print(f"{YELLOW}{'─'*70}{RESET}")

test_chat(
    "How many total products did we buy? How many of them are duplicate? How much we paid for each of them? And how much is the individual cost?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have any information", "don't have access"],
    max_time=12.0,
    label="Stress: Total products + duplicates + cost breakdown"
)

test_chat(
    "What are the total orders I did? From this how many duplicates we have? In those duplicates which item is the maximum duplicate we have? What is the most we paid for the combined duplicate and a single duplicate by price?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have any information", "error"],
    max_time=12.0,
    label="Stress: Orders → duplicates → max duplicate → price"
)

test_chat(
    "List all my products with their quantities. For each product show the name, how many times I bought it, and the total I spent on it.",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have any information", "error"],
    max_time=12.0,
    label="Stress: Full product breakdown with names and costs"
)

test_chat(
    "How many orders do I have? What is my average order value? What was my cheapest order and what was my most expensive order?",
    expected_route="TEXT_TO_SQL",
    must_contain=["28"],
    must_not_contain=["don't have", "error"],
    max_time=10.0,
    label="Stress: Order stats (count + avg + min + max)"
)

test_chat(
    "Show me how many products I bought in total, how many are unique, and list the ones I only bought once.",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have any information", "error"],
    max_time=12.0,
    label="Stress: Total vs unique vs single-purchase products"
)

test_chat(
    "What product categories do I buy from? For each category how many items did I buy and how much did I spend?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have", "error"],
    max_time=10.0,
    label="Stress: Categories with item count and spending"
)

test_chat(
    "Give me a year by year breakdown of my orders. For each year tell me how many orders, total spending, and average order value.",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have", "error"],
    max_time=10.0,
    label="Stress: Yearly breakdown (orders + spending + avg)"
)

test_chat(
    "What is my most purchased product and how many times did I buy it? Also what is my least purchased product? And whats the price difference between them?",
    expected_route="TEXT_TO_SQL",
    must_not_contain=["don't have any information", "error"],
    max_time=12.0,
    label="Stress: Most vs least purchased + price diff"
)


# ═══════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════
print(f"\n\n{BOLD}{'='*70}{RESET}")
print(f"{BOLD}  TEST SUMMARY{RESET}")
print(f"{BOLD}{'='*70}{RESET}")

passed = sum(1 for r in results if r["pass"])
failed = sum(1 for r in results if not r["pass"])
total = len(results)
avg_time = sum(r["time"] for r in results) / total if total else 0

print(f"\n  Total:  {total}")
print(f"  {GREEN}Passed: {passed}{RESET}")
print(f"  {RED}Failed: {failed}{RESET}")
print(f"  Avg time: {avg_time:.2f}s")

if failed:
    print(f"\n  {RED}FAILED TESTS:{RESET}")
    for r in results:
        if not r["pass"]:
            print(f"    ❌ {r['test']}")
            for reason in r.get("reasons", []):
                print(f"       → {reason}")

print()
sys.exit(0 if failed == 0 else 1)
