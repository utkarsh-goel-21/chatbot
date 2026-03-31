import requests
import time

BASE_URL = "http://127.0.0.1:8000"
USER_ID = 11091

print("Testing massive complex user query dynamically against new logic...")
start = time.time()

q = "what is this how many total products did we buy?how many of them are duplicate?how much we paid for each of them?and how much is the indicvidual cost"

try:
    resp = requests.post(f"{BASE_URL}/chat", json={
        "question": q,
        "user_id": USER_ID,
        "history": []
    }, timeout=30)
    
    elapsed = time.time() - start
    data = resp.json()
    
    print(f"\nRoute: {data.get('route')}")
    print(f"Elapsed: {elapsed:.2f}s")
    print(f"\nAnswer:\n{data.get('answer')}")
    
except Exception as e:
    print(f"FAILED: {e}")
