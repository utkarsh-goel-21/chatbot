import { useState, useRef, useEffect } from "react";
import { Menu, Send, Bot, User, Zap, FileText } from "lucide-react";

// ── Detect if a bot message contains tabular data ──
function tryRenderTable(content) {
  try {
    const parsed = JSON.parse(content);
    if (
      Array.isArray(parsed) &&
      parsed.length > 0 &&
      typeof parsed[0] === "object"
    ) {
      const headers = Object.keys(parsed[0]);
      return (
        <div
          className="overflow-x-auto mt-2 rounded-xl"
          style={{ border: "1px solid var(--border)" }}
        >
          <table className="result-table">
            <thead>
              <tr>
                {headers.map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {parsed.map((row, i) => (
                <tr key={i}>
                  {headers.map((h) => (
                    <td key={h}>{String(row[h])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }
  } catch {
    return null;
  }
  return null;
}

// ── Single message bubble ──
function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  const tableView = !isUser ? tryRenderTable(msg.content) : null;

  return (
    <div
      className={`flex items-end gap-2.5 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      {/* Avatar */}
      <div
        className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs mb-1"
        style={{
          background: isUser ? "var(--accent)" : "var(--bg-card)",
          border: "1px solid var(--border)",
          boxShadow: isUser ? "var(--shadow-accent)" : "none",
        }}
      >
        {isUser ? (
          <User size={13} className="text-white" />
        ) : (
          <Bot size={13} style={{ color: "var(--accent)" }} />
        )}
      </div>

      {/* Bubble */}
      <div
        className="max-w-[75%] md:max-w-[62%] px-4 py-3 rounded-2xl text-sm leading-relaxed"
        style={{
          background: isUser ? "var(--bubble-user-bg)" : "var(--bubble-bot-bg)",
          color: isUser ? "var(--bubble-user-text)" : "var(--bubble-bot-text)",
          borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
          border: isUser ? "none" : "1px solid var(--border)",
          boxShadow: "var(--shadow)",
          fontFamily: "'Nunito Sans', sans-serif",
          fontWeight: 500,
        }}
      >
        {tableView || (
          <p style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
            {msg.content}
          </p>
        )}

        {/* Route tag */}
        {msg.route && (
          <div className="flex items-center gap-1.5 mt-2.5">
            <span
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold"
              style={{
                fontFamily: "'Nunito', sans-serif",
                background:
                  msg.route === "TEXT_TO_SQL"
                    ? "var(--tag-sql)"
                    : "var(--tag-rag)",
                color:
                  msg.route === "TEXT_TO_SQL"
                    ? "var(--tag-sql-text)"
                    : "var(--tag-rag-text)",
              }}
            >
              {msg.route === "TEXT_TO_SQL" ? (
                <>
                  <Zap size={9} /> Database
                </>
              ) : (
                <>
                  <FileText size={9} /> Documents
                </>
              )}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Typing indicator ──
function TypingIndicator() {
  return (
    <div className="flex items-end gap-2.5">
      <div
        className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
        }}
      >
        <Bot size={13} style={{ color: "var(--accent)" }} />
      </div>
      <div
        className="px-4 py-3.5 rounded-2xl"
        style={{
          background: "var(--bubble-bot-bg)",
          border: "1px solid var(--border)",
          borderRadius: "18px 18px 18px 4px",
          boxShadow: "var(--shadow)",
        }}
      >
        <div className="flex gap-1.5 items-center">
          <span
            className="dot-bounce w-1.5 h-1.5 rounded-full inline-block"
            style={{ background: "var(--accent)", animationDelay: "0ms" }}
          />
          <span
            className="dot-bounce w-1.5 h-1.5 rounded-full inline-block"
            style={{ background: "var(--accent)", animationDelay: "150ms" }}
          />
          <span
            className="dot-bounce w-1.5 h-1.5 rounded-full inline-block"
            style={{ background: "var(--accent)", animationDelay: "300ms" }}
          />
        </div>
      </div>
    </div>
  );
}

// ── Main ChatWindow ──
function ChatWindow({ session, onUpdateSession, onOpenSidebar }) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages, loading]);

  // ── Auto expand textarea ──
  const handleInput = (e) => {
    const val = e.target.value;
    if (val.length > 1000) return;
    setInput(val);
    e.target.style.height = "auto";
    e.target.style.height = e.target.scrollHeight + "px";
  };

  const resetTextarea = () => {
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !session || loading) return;

    const userMessage = { role: "user", content: input };
    const updatedMessages = [...(session.messages || []), userMessage];
    onUpdateSession(session.id, updatedMessages);
    resetTextarea();
    setLoading(true);

    // ── Timeout fallback ──
    timeoutRef.current = setTimeout(() => {
      setLoading(false);
      onUpdateSession(session.id, [
        ...updatedMessages,
        {
          role: "bot",
          content:
            "The request timed out. Please check the backend and try again.",
          route: null,
        },
      ]);
    }, 15000);

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: input }),
      });
      clearTimeout(timeoutRef.current);
      const data = await response.json();
      onUpdateSession(session.id, [
        ...updatedMessages,
        { role: "bot", content: data.answer, route: data.route },
      ]);
    } catch {
      clearTimeout(timeoutRef.current);
      onUpdateSession(session.id, [
        ...updatedMessages,
        {
          role: "bot",
          content:
            "Something went wrong. Please make sure the backend is running.",
          route: null,
        },
      ]);
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

  const charCount = input.length;
  const charLimit = 1000;

  return (
    <div
      className="flex flex-col flex-1 h-full overflow-hidden"
      style={{ background: "var(--bg-primary)" }}
    >
      {/* ── Top Bar ── */}
      <div
        className="flex items-center gap-3 px-5 py-3.5"
        style={{
          borderBottom: "1px solid var(--border)",
          background: "var(--bg-secondary)",
        }}
      >
        <button
          onClick={onOpenSidebar}
          className="md:hidden w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ color: "var(--text-muted)" }}
        >
          <Menu size={18} />
        </button>

        <div className="flex-1 min-w-0">
          <p
            className="text-sm font-bold truncate"
            style={{
              fontFamily: "'Nunito', sans-serif",
              color: "var(--text-primary)",
            }}
          >
            {session ? session.title : "BizBot"}
          </p>
          {session && (
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              {session.messages.filter((m) => m.role === "user").length}{" "}
              messages
            </p>
          )}
        </div>
      </div>

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-4">
        {!session && (
          <div className="flex flex-col items-center justify-center h-full text-center gap-4">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center"
              style={{
                background: "var(--accent-soft)",
                border: "1px solid var(--accent-border)",
              }}
            >
              <BarChart2 size={28} style={{ color: "var(--accent)" }} />
            </div>
            <div>
              <h2
                className="text-xl font-extrabold mb-1"
                style={{
                  fontFamily: "'Nunito', sans-serif",
                  color: "var(--text-primary)",
                }}
              >
                Welcome to BizBot
              </h2>
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                Start a new chat to ask about your business.
              </p>
            </div>
          </div>
        )}

        {session?.messages?.map((msg, idx) => (
          <MessageBubble key={idx} msg={msg} />
        ))}

        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* ── Input Bar ── */}
      <div
        className="px-4 md:px-8 py-4"
        style={{
          borderTop: "1px solid var(--border)",
          background: "var(--bg-secondary)",
        }}
      >
        <div
          className="flex items-end gap-3 px-4 py-3 rounded-2xl"
          style={{
            background: "var(--bg-input)",
            border: "1px solid var(--border)",
          }}
          onFocus={() => {}}
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            disabled={!session || loading}
            placeholder={
              session
                ? "Ask about your business..."
                : "Start a new chat first..."
            }
            className="flex-1 bg-transparent text-sm resize-none outline-none leading-relaxed"
            style={{
              color: "var(--text-primary)",
              fontFamily: "'Nunito Sans', sans-serif",
              fontWeight: 500,
              maxHeight: "140px",
              overflowY: "auto",
              caretColor: "var(--accent)",
            }}
          />

          <div className="flex flex-col items-end gap-1.5 shrink-0">
            {/* Char counter */}
            {charCount > 800 && (
              <span
                className="text-[10px] font-bold"
                style={{
                  color: charCount > 950 ? "#f87171" : "var(--text-muted)",
                  fontFamily: "'Nunito', sans-serif",
                }}
              >
                {charLimit - charCount}
              </span>
            )}

            {/* Send button */}
            <button
              onClick={sendMessage}
              disabled={!input.trim() || loading || !session}
              className="w-8 h-8 rounded-xl flex items-center justify-center transition-all"
              style={{
                background:
                  input.trim() && session ? "var(--accent)" : "var(--bg-hover)",
                boxShadow:
                  input.trim() && session ? "var(--shadow-accent)" : "none",
              }}
            >
              <Send size={13} className="text-white" />
            </button>
          </div>
        </div>

        <p
          className="text-center text-[10px] mt-2 font-semibold"
          style={{
            color: "var(--text-muted)",
            fontFamily: "'Nunito', sans-serif",
          }}
        >
          Enter to send · Shift+Enter for new line · {charLimit} char limit
        </p>
      </div>
    </div>
  );
}

// Fix missing import
import { BarChart2 } from "lucide-react";

export default ChatWindow;
