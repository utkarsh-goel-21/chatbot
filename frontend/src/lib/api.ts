const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export interface ChatResponse {
  question: string;
  route: "TEXT_TO_SQL" | "RAG";
  answer: string;
}

export async function sendChatMessage(question: string): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  return res.json();
}
