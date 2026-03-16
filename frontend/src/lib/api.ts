const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export interface ChatMessage {
  role: "user" | "ai";
  content: string;
}

export interface ChatResponse {
  question: string;
  route: "TEXT_TO_SQL" | "RAG";
  answer: string;
}

export async function sendChatMessage(
  question: string,
  userId: number,
  history: ChatMessage[],
): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      user_id: userId,
      history: history.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      })),
    }),
  });
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  return res.json();
}

export async function uploadFile(
  file: File,
  userId: number,
): Promise<{ status: string; message: string; type?: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("user_id", userId.toString());

  const res = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload error: ${res.status}`);
  return res.json();
}
