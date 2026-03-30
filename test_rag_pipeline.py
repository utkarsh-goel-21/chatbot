"""
Comprehensive RAG pipeline test — tests router → retrieval → answer generation.
Tests insight queries, identity blocks, and anti-hallucination.
"""

import time
import traceback
from router.query_router import route_query
from rag.retriever import retrieve_relevant_docs
from rag.answer_generator import generate_rag_answer

CUSTOMER_ID = 11091  # Dalton Perez

# ─── Test Categories ───

TESTS = {
    # ── Category 1: General Business Insights (RAG) ──
    "INSIGHTS": [
        "Can you give me an overview of my purchasing habits?",
        "What are my spending trends over the last few years?",
        "Do you see any patterns in the categories I buy from?",
        "Summarize my recent business activity.",
    ],

    # ── Category 2: Identity / External Info (Should Route to BLOCKED or TEXT_TO_SQL) ──
    "IDENTITY": [
        "What is my user ID?",
        "Who am I?",
        "What is my email address?",
    ],

    # ── Category 3: Hallucination Traps (Should Route to RAG but refuse to answer) ──
    "HALLUCINATION": [
        "Who is the CEO of AdventureWorks?",
        "What is the phone number for customer support?",
        "How many active users are on this platform?",
        "Give me a list of all products purchased by Mason.",
    ],

    # ── Category 4: Off-topic / Conversational (Should Route to BLOCKED) ──
    "CONVERSATIONAL": [
        "Hello there",
        "What can you do?",
        "Tell me a joke about bikes.",
    ],

    # ── Category 5: Follow-up Queries (RAG Context) ──
    "FOLLOWUP": [
        ("Why did it drop in 2014?", [
            {"role": "user", "content": "What are my spending trends?"},
            {"role": "assistant", "content": "You spent a lot in 2013, but spending dropped in 2014."},
        ]),
        ("What about accessories?", [
            {"role": "user", "content": "Summarize my product categories."},
            {"role": "assistant", "content": "You mostly buy bikes and clothing."},
        ]),
    ],
}


def run_single_test(question: str, customer_id: int, history: list = None, test_id: str = ""):
    """Run one full pipeline test: route → retrieve → answer."""
    if history is None:
        history = []

    result = {
        "test_id": test_id,
        "question": question,
        "route": None,
        "docs_retrieved": None,
        "answer": None,
        "status": "UNKNOWN",
        "error": None,
        "time_s": 0,
    }

    start = time.time()

    try:
        # Step 1: Route
        route = route_query(question, history)
        result["route"] = route

        if route == "BLOCKED":
            result["status"] = "ROUTED_BLOCKED"
            result["time_s"] = round(time.time() - start, 2)
            return result
            
        if route == "TEXT_TO_SQL":
            result["status"] = "ROUTED_SQL"
            result["time_s"] = round(time.time() - start, 2)
            return result

        # Step 2: Retrieve Docs
        docs = retrieve_relevant_docs(question, customer_id)
        result["docs_retrieved"] = len(docs) > 0

        # Step 3: Generate Answer
        answer = generate_rag_answer(question, customer_id, history)
        result["answer"] = answer
        
        # Check if it triggered the anti-hallucination safeguard
        if "I do not have access to that information" in answer or "I don't have enough data" in answer:
            result["status"] = "SAFEGUARD_TRIGGERED"
        else:
            result["status"] = "SUCCESS"

    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
        traceback.print_exc()

    result["time_s"] = round(time.time() - start, 2)
    return result


def print_result(r):
    status_icon = {
        "SUCCESS": "✅",
        "SAFEGUARD_TRIGGERED": "🛡️",
        "ROUTED_SQL": "🗄️",
        "ROUTED_BLOCKED": "🚫",
        "ERROR": "❌",
    }.get(r["status"], "❓")

    print(f"\n{'='*80}")
    print(f"{status_icon} [{r['test_id']}] {r['question'][:70]}")
    print(f"   Route: {r['route']} | Status: {r['status']} | Time: {r['time_s']}s")
    if r["answer"]:
        answer_display = r["answer"][:200]
        print(f"   Answer: {answer_display}")
    if r["error"]:
        print(f"   ❌ Error: {r['error'][:200]}")


def run_all_tests():
    results = []
    total_start = time.time()

    for category, tests in TESTS.items():
        print(f"\n\n{'#'*80}")
        print(f"##  CATEGORY: {category}")
        print(f"{'#'*80}")

        for i, test in enumerate(tests):
            test_id = f"{category}_{i+1}"

            # Handle follow-up tests (tuple with history)
            if isinstance(test, tuple):
                question, history = test
            else:
                question = test
                history = []

            r = run_single_test(question, CUSTOMER_ID, history, test_id)
            results.append(r)
            print_result(r)

    # ── Summary ──
    total_time = round(time.time() - total_start, 2)
    print(f"\n\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")

    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    for status, count in sorted(counts.items()):
        icon = {"SUCCESS": "✅", "SAFEGUARD_TRIGGERED": "🛡️", "ROUTED_SQL": "🗄️", "ROUTED_BLOCKED": "🚫", "ERROR": "❌"}.get(status, "❓")
        print(f"  {icon} {status}: {count}")

    print(f"\n  Total tests: {len(results)}")
    print(f"  Total time: {total_time}s")
    print(f"  Avg time per test: {round(total_time / max(len(results), 1), 2)}s")

    errors = [r for r in results if r["status"] == "ERROR"]
    if errors:
        print(f"\n  ❌ FAILED TESTS:")
        for r in errors:
            print(f"    - [{r['test_id']}] {r['question'][:60]} → {r['error'][:100]}")

    return results


if __name__ == "__main__":
    run_all_tests()
