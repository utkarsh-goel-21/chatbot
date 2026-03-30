import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_llm(prompt: str, system_prompt: str = "You are a helpful business assistant.", history: list = None) -> str:
    if history is None:
        history = []
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history
    for msg in history:
        messages.append({
            "role": "user" if msg["role"] == "user" else "assistant",
            "content": msg["content"]
        })
    
    # Add current message
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0
        )
        return response.choices[0].message.content
    except Exception as e:
        if "429" in str(e) or "RateLimit" in str(type(e)):
            print("⚠️ Rate limit hit on 70b model. Falling back to llama-3.1-8b-instant...")
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0
            )
            return response.choices[0].message.content
        raise e