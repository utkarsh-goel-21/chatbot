import { useRef, useEffect, useCallback } from "react";
import { Menu } from "lucide-react";
import { useChatStore } from "@/store/chatStore";
import { sendChatMessage } from "@/lib/api";
import MessageBubble from "./MessageBubble";
import ThinkingIndicator from "./ThinkingIndicator";
import WelcomeScreen from "./WelcomeScreen";
import ChatInput from "./ChatInput";

const ChatArea = () => {
  const {
    sessions,
    activeSessionId,
    isLoading,
    createSession,
    addMessage,
    setLoading,
    setSidebarOpen,\
    currentUser,
  } = useChatStore();

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const messages = activeSession?.messages || [];
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages.length, isLoading]);

  const handleSend = useCallback(
    async (text: string) => {
      let sessionId = activeSessionId;
      if (!sessionId) {
        sessionId = createSession();
      }

      const userMsg = {
        id: crypto.randomUUID(),
        role: "user" as const,
        content: text,
        timestamp: Date.now(),
      };
      addMessage(sessionId, userMsg);
      setLoading(true);

      try {
        const res = await sendChatMessage(
        text,
        currentUser.id,
        messages.map((m) => ({ role: m.role, content: m.content }))
);
        addMessage(sessionId, {
          id: crypto.randomUUID(),
          role: "ai",
          content: res.answer,
          route: res.route,
          timestamp: Date.now(),
        });
      } catch {
        addMessage(sessionId, {
          id: crypto.randomUUID(),
          role: "ai",
          content:
            "Sorry, I couldn't reach the server. Make sure the backend is running at http://127.0.0.1:8000 and try again.",
          timestamp: Date.now(),
          isError: true,
        });
      } finally {
        setLoading(false);
      }
    },
    [activeSessionId, addMessage, createSession, setLoading],
  );

  const handleSuggestion = (text: string) => {
    handleSend(text);
  };

  const title = activeSession?.title || "New Conversation";

  return (
    <div className="flex-1 flex flex-col h-screen bg-qm-base">
      {/* Header */}
      <div className="h-14 flex items-center justify-between px-6 max-sm:px-4 border-b border-border flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(true)}
            className="md:hidden text-qm-text-sec hover:text-qm-text transition-colors"
          >
            <Menu size={20} />
          </button>
          <h2 className="font-semibold text-qm-text text-sm truncate max-w-[300px]">
            {title}
          </h2>
        </div>
        <span className="text-qm-text-muted text-[13px]">
          {messages.length} messages
        </span>
      </div>

      {/* Messages */}
      {messages.length === 0 && !isLoading ? (
        <WelcomeScreen onSuggestionClick={handleSuggestion} />
      ) : (
        <div className="flex-1 overflow-y-auto scrollbar-thin px-6 max-sm:px-4 py-6">
          <div className="max-w-[760px] mx-auto space-y-6">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            {isLoading && <ThinkingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        isLoading={isLoading}
        inputRef={inputRef}
      />
    </div>
  );
};

export default ChatArea;
