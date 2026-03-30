import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── All 5 Groq API keys (each from a different account) ──
_API_KEYS = [
    os.getenv("GROQ_API_KEY"),
    os.getenv("GROQ_API_KEY_ONE"),
    os.getenv("GROQ_API_KEY_TWO"),
    os.getenv("GROQ_API_KEY_THREE"),
    os.getenv("GROQ_API_KEY_FOUR"),
]
# Filter out any None values (missing env vars)
_API_KEYS = [k for k in _API_KEYS if k]

# Track which key to try next (round-robin starting point)
_current_key_index = 0

MODEL = "llama-3.3-70b-versatile"


def call_llm(
    prompt: str,
    system_prompt: str = "You are a helpful business assistant.",
    history: list = None,
    max_tokens: int = 1024,
) -> str:
    global _current_key_index

    if history is None:
        history = []

    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history
    for msg in history:
        messages.append({
            "role": "user" if msg["role"] == "user" else "assistant",
            "content": msg["content"],
        })

    # Add current message
    messages.append({"role": "user", "content": prompt})

    # ── Try each key in rotation ──
    last_error = None
    start_index = _current_key_index

    for i in range(len(_API_KEYS)):
        key_index = (start_index + i) % len(_API_KEYS)
        api_key = _API_KEYS[key_index]

        try:
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0,
                max_tokens=max_tokens,
            )
            # Success — advance the starting key so next call starts fresh
            _current_key_index = (key_index + 1) % len(_API_KEYS)
            return response.choices[0].message.content

        except Exception as e:
            is_rate_limit = "429" in str(e) or "RateLimit" in str(type(e).__name__)
            if is_rate_limit:
                print(f"⚠️  Rate limit on key #{key_index + 1}. Rotating to next key...")
                last_error = e
                continue
            else:
                # Non-rate-limit error — raise immediately
                raise e

    # All keys exhausted — raise the last rate limit error
    print("🚨 All 5 Groq API keys hit rate limits!")
    raise last_error