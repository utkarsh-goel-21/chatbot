import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# ── Provider detection ──
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()  # "groq" or "ollama"

# ── Model constants ──
MODEL_FAST = "llama-3.1-8b-instant"           # For simple tasks: routing, classification
MODEL_SMART = "llama-3.3-70b-versatile"       # For complex tasks: SQL gen, answer formatting


# ═══════════════════════════════════════════════════════════
#  OLLAMA PROVIDER  (OpenAI-compatible API, no API key needed)
# ═══════════════════════════════════════════════════════════

if LLM_PROVIDER == "ollama":
    from openai import OpenAI, AsyncOpenAI

    _OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    _OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    _ollama_sync = OpenAI(base_url=_OLLAMA_BASE, api_key="ollama")
    _ollama_async = AsyncOpenAI(base_url=_OLLAMA_BASE, api_key="ollama")

    print(f"🦙 LLM Provider: Ollama ({_OLLAMA_MODEL}) @ {_OLLAMA_BASE}")

    def call_llm(
        prompt: str,
        system_prompt: str = "You are a helpful business assistant.",
        history: list = None,
        max_tokens: int = 1024,
        model: str = None,
    ) -> str:
        """Synchronous LLM call via Ollama (OpenAI-compatible)."""
        if history is None:
            history = []

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({
                "role": "user" if msg["role"] == "user" else "assistant",
                "content": msg["content"],
            })
        messages.append({"role": "user", "content": prompt})

        response = _ollama_sync.chat.completions.create(
            model=_OLLAMA_MODEL,   # Always use the single configured model
            messages=messages,
            temperature=0,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def call_llm_async(
        prompt: str,
        system_prompt: str = "You are a helpful business assistant.",
        history: list = None,
        max_tokens: int = 1024,
        model: str = None,
    ) -> str:
        """Async LLM call via Ollama (OpenAI-compatible)."""
        if history is None:
            history = []

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({
                "role": "user" if msg["role"] == "user" else "assistant",
                "content": msg["content"],
            })
        messages.append({"role": "user", "content": prompt})

        response = await _ollama_async.chat.completions.create(
            model=_OLLAMA_MODEL,
            messages=messages,
            temperature=0,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def warm_up_llm():
        """Warm up the Ollama connection."""
        try:
            call_llm(prompt="Hi", system_prompt="Reply with just 'ok'.", max_tokens=2)
            print("✅ Ollama LLM connection warmed up.")
        except Exception as e:
            print(f"⚠️  Ollama warm-up failed: {e}")
            print("   Make sure Ollama is running: ollama serve")


# ═══════════════════════════════════════════════════════════
#  GROQ PROVIDER  (Cloud API with multi-key rotation)
# ═══════════════════════════════════════════════════════════

else:
    from groq import Groq, AsyncGroq

    # All 5 Groq API keys (each from a different account)
    _API_KEYS = [
        os.getenv("GROQ_API_KEY"),
        os.getenv("GROQ_API_KEY_ONE"),
        os.getenv("GROQ_API_KEY_TWO"),
        os.getenv("GROQ_API_KEY_THREE"),
        os.getenv("GROQ_API_KEY_FOUR"),
    ]
    _API_KEYS = [k for k in _API_KEYS if k]

    # Pre-build cached client objects (one per key)
    _sync_clients = [Groq(api_key=k, max_retries=0) for k in _API_KEYS]
    _async_clients = [AsyncGroq(api_key=k, max_retries=0) for k in _API_KEYS]

    # Round-robin starting point
    _current_key_index = 0

    print(f"☁️  LLM Provider: Groq ({len(_API_KEYS)} keys loaded)")

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