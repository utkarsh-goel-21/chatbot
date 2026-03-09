import { useState, useRef, useEffect } from "react";
import { Menu, Send, Bot, User } from "lucide-react";

function ChatWindow({ session, onUpdateSession, onOpenSidebar }) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages]);

  const sendMessage = async () => {
    if (!input.trim() || !session || loading) return;

    const userMessage = { role: "user", content: input };
    const updatedMessages = [...(session.messages || []), userMessage];
    onUpdateSession(session.id, updatedMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: input }),
      });
      const data = await response.json();
      const botMessage = {
        role: "bot",
        content: data.answer,
        route: data.route,
      };
      onUpdateSession(session.id, [...updatedMessages, botMessage]);
    } catch (error) {
      const errorMessage = {
        role: "bot",
        content:
          "Something went wrong. Please make sure the backend is running.",
        route: null,
      };
      onUpdateSession(session.id, [...updatedMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col flex-1 h-full overflow-hidden bg-[#0a0a0a]">
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 py-4 border-b border-white/5">
        <button
          onClick={onOpenSidebar}
          className="md:hidden text-white/40 hover:text-white transition-colors"
        >
          <Menu size={20} />
        </button>
        <span className="text-white/50 text-sm">
          {session ? session.title : "Select or start a new chat"}
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {!session && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-3">
            <Bot size={40} className="text-white/10" />
            <p className="text-white/20 text-sm">
              Ask anything about your business.
              <br />
              Sales, revenue, trends and more.
            </p>
          </div>
        )}

        {session?.messages?.map((msg, idx) => (
          <div
            key={idx}
            className={`flex items-start gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
          >
            {/* Avatar */}
            <div
              className={`
              shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs
              ${msg.role === "user" ? "bg-white/10 text-white" : "bg-white/5 text-white/60"}
            `}
            >
              {msg.role === "user" ? <User size={14} /> : <Bot size={14} />}
            </div>

            {/* Bubble */}
            <div
              className={`
              max-w-[75%] md:max-w-[60%] px-4 py-3 rounded-2xl text-sm leading-relaxed
              ${
                msg.role === "user"
                  ? "bg-white/10 text-white rounded-tr-sm"
                  : "bg-[#1a1a1a] text-white/80 rounded-tl-sm"
              }
            `}
            >
              {msg.content}

              {/* Route tag */}
              {msg.route && (
                <span
                  className={`
                  block mt-2 text-[10px] font-medium tracking-wider uppercase
                  ${msg.route === "TEXT_TO_SQL" ? "text-blue-400/50" : "text-emerald-400/50"}
                `}
                >
                  {msg.route === "TEXT_TO_SQL" ? "⚡ Database" : "📄 Documents"}
                </span>
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex items-start gap-3">
            <div className="shrink-0 w-7 h-7 rounded-full bg-white/5 flex items-center justify-center">
              <Bot size={14} className="text-white/60" />
            </div>
            <div className="bg-[#1a1a1a] px-4 py-3 rounded-2xl rounded-tl-sm">
              <div className="flex gap-1 items-center h-4">
                <span className="w-1.5 h-1.5 bg-white/30 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 bg-white/30 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 bg-white/30 rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="px-4 py-4 border-t border-white/5">
        <div
          className={`
          flex items-end gap-3 px-4 py-3 rounded-2xl
          bg-[#111111] border border-white/10
          focus-within:border-white/20 transition-colors
          ${!session ? "opacity-40 pointer-events-none" : ""}
        `}
        >
          <textarea
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your business..."
            className="flex-1 bg-transparent text-white text-sm placeholder-white/20
              resize-none outline-none leading-relaxed max-h-32 overflow-y-auto"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="shrink-0 w-8 h-8 rounded-xl bg-white/10 hover:bg-white/20
              disabled:opacity-20 disabled:cursor-not-allowed
              flex items-center justify-center transition-all duration-200"
          >
            <Send size={14} className="text-white" />
          </button>
        </div>
        <p className="text-white/10 text-xs text-center mt-2">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}

export default ChatWindow;
