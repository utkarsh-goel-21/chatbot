import os
import asyncio
from groq import Groq, AsyncGroq
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
_API_KEYS = [k for k in _API_KEYS if k]

# ── Pre-build cached client objects (one per key) ──
_sync_clients = [Groq(api_key=k, max_retries=0) for k in _API_KEYS]
_async_clients = [AsyncGroq(api_key=k, max_retries=0) for k in _API_KEYS]

# Round-robin starting point
_current_key_index = 0

# ── Model constants ──
MODEL_FAST = "llama-3.1-8b-instant"           # For simple tasks: routing, classification
MODEL_SMART = "llama-3.3-70b-versatile"       # For complex tasks: SQL gen, answer formatting


def call_llm(
    prompt: str,
    system_prompt: str = "You are a helpful business assistant.",
    history: list = None,
    max_tokens: int = 1024,
    model: str = None,
) -> str:
    """Synchronous LLM call with key rotation. Uses cached clients."""
    global _current_key_index

    if model is None:
        model = MODEL_SMART

    if history is None:
        history = []

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({
            "role": "user" if msg["role"] == "user" else "assistant",
            "content": msg["content"],
        })
    messages.append({"role": "user", "content": prompt})

    last_error = None
    start_index = _current_key_index

    for i in range(len(_sync_clients)):
        key_index = (start_index + i) % len(_sync_clients)
        client = _sync_clients[key_index]

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
                max_tokens=max_tokens,
            )
            _current_key_index = (key_index + 1) % len(_sync_clients)
            return response.choices[0].message.content

        except Exception as e:
            is_rate_limit = "429" in str(e) or "RateLimit" in str(type(e).__name__)
            if is_rate_limit:
                print(f"⚠️  Rate limit on key #{key_index + 1}. Rotating...")
                last_error = e
                continue
            else:
                raise e

    print("🚨 All Groq API keys hit rate limits!")
    if model != MODEL_FAST:
        print(f"🔄 Falling back to {MODEL_FAST} to prevent crash...")
        return call_llm(prompt, system_prompt, history, max_tokens, model=MODEL_FAST)
        
    raise last_error


async def call_llm_async(
    prompt: str,
    system_prompt: str = "You are a helpful business assistant.",
    history: list = None,
    max_tokens: int = 1024,
    model: str = None,
) -> str:
    """Async LLM call with key rotation. Uses cached async clients."""
    global _current_key_index

    if model is None:
        model = MODEL_SMART

    if history is None:
        history = []

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({
            "role": "user" if msg["role"] == "user" else "assistant",
            "content": msg["content"],
        })
    messages.append({"role": "user", "content": prompt})

    last_error = None
    start_index = _current_key_index

    for i in range(len(_async_clients)):
        key_index = (start_index + i) % len(_async_clients)
        client = _async_clients[key_index]

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
                max_tokens=max_tokens,
            )
            _current_key_index = (key_index + 1) % len(_async_clients)
            return response.choices[0].message.content

        except Exception as e:
            is_rate_limit = "429" in str(e) or "RateLimit" in str(type(e).__name__)
            if is_rate_limit:
                print(f"⚠️  Rate limit on key #{key_index + 1} (async). Rotating...")
                last_error = e
                continue
            else:
                raise e

    print("🚨 All Groq API keys hit rate limits (async)!")
    if model != MODEL_FAST:
        print(f"🔄 Falling back to {MODEL_FAST} (async) to prevent crash...")
        return await call_llm_async(prompt, system_prompt, history, max_tokens, model=MODEL_FAST)
        
    raise last_error


def warm_up_llm():
    """Send a tiny throwaway request to warm up the Groq connection pool."""
    try:
        call_llm(
            prompt="Hi",
            system_prompt="Reply with just 'ok'.",
            max_tokens=2,
            model=MODEL_FAST,
        )
        print("✅ Groq LLM connection warmed up.")
    except Exception as e:
        print(f"⚠️  LLM warm-up failed (non-critical): {e}")